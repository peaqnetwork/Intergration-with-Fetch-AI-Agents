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

# Create a key pair from the seed phrase
peaqKeypair = Keypair.create_from_mnemonic(seed)

aliceSeed = "library weekend over soap laundry capable glory sun witness ivory sting coyote"

aliceKeyPair = Keypair.create_from_mnemonic(aliceSeed)

# Connect to a Substrate-based blockchain
substrate = SubstrateInterface(
    url="wss://wsspc1-qa.agung.peaq.network",
    # ss58_format=42,  # Replace with the SS58 format of your chain
    # type_registry_preset="substrate-node-template",
)

minimum_balance = 5 * 10 ** substrate.token_decimals

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
    print(f"getAddressMapping: {type} {key}")
    data = substrate.rpc_request('peaqstorage_readAttribute', [key, type.encode().hex()])
    itemHex = None
    if data and 'result' in data and data['result'] and 'item' in data['result']:
        itemHex = data['result']['item']
    item = bytes.fromhex(itemHex[2:]).decode('utf-8') if itemHex else None
    print(f"item: {item}")
    return item



class Transfer(Model):
    amount: int

bobAddress = "5FyGbQZS3wEbKbDeMxyKD6B3d6dPBuJiDb2CDTThZebtLCAK"
alice = Agent(name="alice", seed=aliceSeed, port=8000, endpoint=["http://127.0.0.1:8000/submit"])


fund_agent_if_low(alice.wallet.address())

@alice.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f'starting up {ctx.name}')
    await storeAddressMapping(f'{ctx.address}:{ctx.wallet.address()}', aliceKeyPair.ss58_address)
    await storeAddressMapping(f'{aliceKeyPair.ss58_address}', ctx.address.replace("agent", ""))
    ctx.logger.info(f'address mapping stored for {ctx.storage.get(f"pAM:{ctx.address}")}')





@alice.on_interval(period=2.0)
async def check_balance(ctx: Context):
    ctx.logger.info(f'hello, my name is {ctx.name}')
    ctx.logger.info(f'my address is {ctx.address}')
    balance = await getBalance(aliceKeyPair.ss58_address)
    ctx.logger.info(f"Address: {aliceKeyPair.ss58_address}")
    ctx.logger.info(
        f"Balance: {balance} {substrate.token_symbol}")
    if balance < minimum_balance:
        ctx.logger.info(f"Low balance, requesting {minimum_balance - balance} funds from {bobAddress}")
        mappedAddress = getAddressMapping(bobAddress, peaqKeypair.ss58_address)
        if not mappedAddress:
            ctx.logger.info(f"Address mapping not found for {bobAddress}")
            return
        agentAddress = mappedAddress.split(':')[0]
        fetchAgentBalance = ctx.ledger.query_bank_balance(agentAddress)
        ctx.logger.info(f"agent's balance: {fetchAgentBalance}")
        await ctx.send(agentAddress, Transfer(amount=(minimum_balance - balance)))
        
    

@alice.on_message(model=Transfer)
async def message_handler(ctx: Context, sender: str, msg: Transfer):
    aliceBalance = await getBalance(aliceKeyPair.ss58_address)
    senderSubstrateAddress = getAddressMapping(sender.replace("agent", ""), peaqKeypair.ss58_address)
    ctx.logger.info(f"Received Transfer request from {senderSubstrateAddress}: {msg.amount}")
    if aliceBalance < msg.amount:
        ctx.logger.info(f"Insufficient balance to transfer {msg.amount} {substrate.token_symbol} to {senderSubstrateAddress}")
        return
    ctx.logger.info(f"Transferring {msg.amount} {substrate.token_symbol} to {senderSubstrateAddress}")
    print("sender: ", sender)
    result = await transferBalance(senderSubstrateAddress, msg.amount, aliceKeyPair)
    ctx.logger.info(f"Transfer result: {result}")

if __name__ == "__main__":
    alice.run()
