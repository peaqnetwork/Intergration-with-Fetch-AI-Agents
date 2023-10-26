import os
import sys
import ssl

from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

ssl._create_default_https_context = ssl._create_unverified_context

# Read the seed phrase from a file
seed_file = "seed.txt"
if not os.path.isfile(seed_file):
    print(f"Error: {seed_file} not found")
    sys.exit(1)
with open(seed_file, "r") as f:
    seed = f.read().strip()

class AirSensorData(Model):
    temperature: float
    humidity: float
    lux: float
    pressure: float

# Create a key pair from the seed phrase
peaqKeypair = Keypair.create_from_mnemonic(seed)

bobSeed = "panic pretty surge torch reunion uncle execute snack silver praise math midnight"
# Create a key pair from the seed phrase
bobKeypair = Keypair.create_from_mnemonic(bobSeed)

# Connect to a Substrate-based blockchain
substrate = SubstrateInterface(
    url="wss://wsspc1-qa.agung.peaq.network",
    # ss58_format=42,  # Replace with the SS58 format of your chain
    # type_registry_preset="substrate-node-template",
)

minimum_balance = 5 * 10 ** substrate.token_decimals
DATA_PRICE = 0.001 * 10 ** substrate.token_decimals  # 0.001 tokens

async def transferBalance(address, amount, keypair):
    # Create a transfer extrinsic
    call = substrate.compose_call(
        call_module='Balances',
        call_function='transfer',
        call_params={
            'dest': address,
            'value': amount
        }
    )

    # Create a extrinsic
    extrinsic = substrate.create_signed_extrinsic(
        call=call,
        keypair=keypair,
    )
    # Submit the transaction
    try:
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print("Extrinsic '{}' sent and included in block '{}'".format(receipt.extrinsic_hash, receipt.block_hash))

    except SubstrateRequestException as e:
        print("Failed to send: {}".format(e))


async def formatBalance(balance):
    return balance / 10 ** substrate.token_decimals


async def getBalance(address):
    result = substrate.query('System', 'Account', [address])
    balance = result.value['data']['free']
    return balance

def item_exists(item_type: str):
    item = getAddressMapping(item_type, bobKeypair.ss58_address)
    return item is not None

async def store_sensor_data_on_chain(data: AirSensorData):
    # Convert the data into a string or JSON format to store as an item
    data_string = f"Temperature: {data.temperature}, Humidity: {data.humidity}, Lux: {data.lux}, Pressure: {data.pressure}"

    # Check if item of type 'AirSensorData' already exists
    existdata = item_exists('AirSensorData');
    print("test exist", existdata)
    if item_exists('AirSensorData'):
        call_function = 'update_item'
    else:
        call_function = 'add_item'

    print("test", call_function)

    # Create an extrinsic call to store or update the air sensor data
    call = substrate.compose_call(
        call_module='PeaqStorage',  
        call_function=call_function,   
        call_params={
            'item_type': 'AirSensorData',
            'item': data_string,
        }
    )

    # Create a signed extrinsic
    extrinsic = substrate.create_signed_extrinsic(
        call=call,
        keypair=bobKeypair,
    )

    # Submit the extrinsic to the blockchain
    try:
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print("Extrinsic '{}' sent and included in block '{}'".format(receipt.extrinsic_hash, receipt.block_hash))
    except SubstrateRequestException as e:
        print("Failed to send data to chain: {}".format(e))




async def storeAddressMapping(value: str, type: str):
    print(f"storeAddressMapping: {value}")
    item = getAddressMapping(type, peaqKeypair.ss58_address)
    if item:
        # if item == value:
        #     return
        
        # call = substrate.compose_call(
        #     call_module='PeaqStorage',
        #     call_function='update_item',
        #     call_params={
        #         'item_type': type,
        #         'item': value,
        #     }
        # )
        # extrinsic = substrate.create_signed_extrinsic(
        #     call=call,
        #     keypair=peaqKeypair,
        # )
        # # Submit the transaction
        # try:
        #     receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        #     print("Extrinsic '{}' sent and included in block '{}'".format(receipt.extrinsic_hash, receipt.block_hash))
        # except SubstrateRequestException as e:
        #     print("Failed to send: {}".format(e))
        return
    # Create a transfer extrinsic
    call = substrate.compose_call(
        call_module='PeaqStorage',
        call_function='add_item',
        call_params={
            'item_type': type,
            'item': value,
        }
    )
    extrinsic = substrate.create_signed_extrinsic(
        call=call,
        keypair=peaqKeypair,
    )
    # Submit the transaction
    try:
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print("Extrinsic '{}' sent and included in block '{}'".format(receipt.extrinsic_hash, receipt.block_hash))
    except SubstrateRequestException as e:
        print("Failed to send: {}".format(e))


def getAddressMapping(type: str, key: str):
    print(f"getAddressMapping: {type}, {key}")
    data = substrate.rpc_request('peaqstorage_readAttribute', [key, type.encode().hex()])
    itemHex = None
    if data and 'result' in data and data['result'] and 'item' in data['result']:
        itemHex = data['result']['item']
    item = bytes.fromhex(itemHex[2:]).decode('utf-8') if itemHex else None
    print(f"item: {item}")
    return item



class Transfer(Model):
    amount: int

class RequestAirSensorData(Model):
    pass

aliceAddress = "5ENVjhQV514okBJpYuwBQLjcTPMkzXBu18swygWpsyHzvw6W"
bob = Agent(name="bob", seed=bobSeed, port=8002, endpoint=["http://127.0.0.1:8002/submit"])


fund_agent_if_low(bob.wallet.address())

@bob.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f'starting up {ctx.name}')
    await storeAddressMapping(f'{ctx.address}:{ctx.wallet.address()}', bobKeypair.ss58_address)
    await storeAddressMapping(f'{bobKeypair.ss58_address}', ctx.address.replace("agent", ""))
    ctx.logger.info(f'address mapping stored for {ctx.storage.get(f"pAM:{ctx.address}")}')





@bob.on_interval(period=2.0)
async def check_balance(ctx: Context):
    ctx.logger.info(f'hello, my name is {ctx.name}')
    ctx.logger.info(f'my address is {ctx.address}')
    balance = await getBalance(bobKeypair.ss58_address)
    ctx.logger.info(f"Address: {bobKeypair.ss58_address}")
    ctx.logger.info(
        f"Balance: {balance} {substrate.token_symbol}")
    if balance < minimum_balance:
        ctx.logger.info(f"Low balance, requesting {minimum_balance - balance} funds from {aliceAddress}")
        mappedAddress = getAddressMapping(aliceAddress, peaqKeypair.ss58_address)
        if not mappedAddress:
            ctx.logger.info(f"Address mapping not found for {aliceAddress}")
            return
        agentAddress = mappedAddress.split(':')[0]
        walletAddress = mappedAddress.split(':')[1]
        fetchAgentBalance = ctx.ledger.query_bank_balance(walletAddress)
        ctx.logger.info(f"agent's balance: {fetchAgentBalance}")
        await ctx.send(agentAddress, Transfer(amount=(minimum_balance - balance)))

@bob.on_interval(period=30.0)
async def request_sensor_data(ctx: Context):
    ctx.logger.info(f"Checking balance before requesting air sensor data from Alice.")
    balance = await getBalance(bobKeypair.ss58_address)
    
    if balance < DATA_PRICE:
        ctx.logger.warning(f"Insufficient balance to pay for data. Not requesting data from Alice.")
        return
    ctx.logger.info(f"Requesting air sensor data from Alice.")
    # Get the mapped address for Alice
    mappedAddress = getAddressMapping(aliceAddress, peaqKeypair.ss58_address)
    if not mappedAddress:
        ctx.logger.info(f"Address mapping not found for {aliceAddress}")
        return
    agentAddress = mappedAddress.split(':')[0]
    print("agent address before sendng ", agentAddress)
    
    # Send the data request to Alice using the resolved address
    await ctx.send(agentAddress, RequestAirSensorData()) 

@bob.on_message(model=AirSensorData)
async def handle_sensor_data(ctx: Context, sender: str, msg: AirSensorData):
    print("testtestetsetsetsetsetsetsetsetsetset")
    if not msg or msg.temperature is None or msg.humidity is None or msg.lux is None or msg.pressure is None:
        ctx.logger.info(f"No valid air sensor data received from {sender}.")
        return
    
    ctx.logger.info(f"Received air sensor data from {sender}: Temperature: {msg.temperature}, Humidity: {msg.humidity}, Lux: {msg.lux}, Pressure: {msg.pressure}")
    
    # Store the received data on the blockchain
    await store_sensor_data_on_chain(msg)
    senderSubstrateAddress = getAddressMapping(sender.replace("agent", ""), peaqKeypair.ss58_address)
    
    ctx.logger.info(f"Sending {DATA_PRICE} tokens to substrate address {senderSubstrateAddress} as payment for the data.")
    await transferBalance(senderSubstrateAddress, DATA_PRICE, bobKeypair)
 

@bob.on_message(model=Transfer)
async def message_handler(ctx: Context, sender: str, msg: Transfer):
    bobBalance = await getBalance(bobKeypair.ss58_address)
    senderSubstrateAddress = getAddressMapping(sender.replace("agent", ""), peaqKeypair.ss58_address)
    ctx.logger.info(f"Received Transfer request from {senderSubstrateAddress}: {msg.amount}")
    if bobBalance < msg.amount:
        ctx.logger.info(f"Insufficient balance to transfer {msg.amount} {substrate.token_symbol} to {senderSubstrateAddress}")
        return
    ctx.logger.info(f"Transferring {msg.amount} {substrate.token_symbol} to {senderSubstrateAddress}")
    print("sender: ", sender)
    result = await transferBalance(senderSubstrateAddress, msg.amount, bobKeypair)
    ctx.logger.info(f"Transfer result: {result}")

if __name__ == "__main__":
    bob.run()
