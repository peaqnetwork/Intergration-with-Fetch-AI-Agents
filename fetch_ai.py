import os
import sys
import ssl

from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model, Bureau
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException
import substrateinterface.utils.ss58 as ss58
import substrateinterface.utils.hasher as hasher
import substrateinterface.storage as encrypted_json
import hashlib
import base64
# encrypted_json
# example blake2_256 from substrate interface
ssl._create_default_https_context = ssl._create_unverified_context

# Read the seed phrase from a file
seed_file = "seed.txt"
if not os.path.isfile(seed_file):
    print(f"Error: {seed_file} not found")
    sys.exit(1)
with open(seed_file, "r") as f:
    seed = f.read().strip()

# Create a key pair from the seed phrase
keypair = Keypair.create_from_mnemonic(seed)

# Connect to a Substrate-based blockchain
substrate = SubstrateInterface(
    url="wss://wsspc1-qa.agung.peaq.network",
    # ss58_format=42,  # Replace with the SS58 format of your chain
    # type_registry_preset="substrate-node-template",
)

minimum_balance = 5 * 10 ** substrate.token_decimals

def create_storage_keys(args):
    print(f"args: {args}")
    keys_byte_array = []
    for arg in args:
        if arg['type'] == 'ADDRESS':
            decoded_address = ss58.ss58_decode(arg['value'], 42)
            decoded_address_byte_array = decoded_address.encode('utf-8')
            print(f"decoded_address: {decoded_address_byte_array}")
            keys_byte_array.append(decoded_address_byte_array)
        elif arg['type'] == 'STANDARD':
            hash_name = arg['value'].encode('utf-8')
            # hash_name = bytearray(hash_name)
            print(f"hash_name: {hash_name}")
            keys_byte_array.append(hash_name)
    print(f"keys_byte_array: {keys_byte_array}")
    key = b''.join(keys_byte_array)
    hashed_key = hasher.blake2_256(key)
    return '0x' + hashed_key.hex()

def get_hashed_key_for_attr(did_account:str, name:str):  
    bytes_in_name = bytearray(name, 'utf-8')
    bytes_to_hash = ('0x{}'.format(ss58.ss58_decode(did_account, 42))).encode('utf-8')
    print(f"bytes_to_hash before: {bytes_to_hash}")
    bytes_to_hash = bytes_to_hash + bytes_in_name
    print(f"bytes_to_hash: {bytes_to_hash}")
    print(f"bytes_to_name: {bytes_in_name}")
    # h = hashlib.blake2b(digest_size=32)
    # h.update(bytes_to_hash)
    # print(f"hashed_key: {h.hexdigest()}")
    hash = hasher.blake2_256(bytes_to_hash)
    print(f"hashed_key: {hash.hex()}")
    return '0x' + hash.hex()

# get_hashed_key_for_attr('5GZ7f6de6HdPGrFpzAac3HDSB6bJHBvwUDqUPjBiG7dq2bTm', 'fetchAgentAddress')
# 0xb595844fa883ea5327353c800fc78ea01453ab82f6fb9df1a0f9ab4674c11d8a
# 0xc69becbda076ed9e2e5dc434a9b58deae8a9f574842ffc1f78a4af4d1a693141fetchAgentAddress

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
    # Check if the address is already stored
    # hashKey = create_storage_keys([{'type': 'ADDRESS', 'value': keypair.ss58_address}, {'type': 'STANDARD', 'value': 'fetchAgentAddress'}])
    # testHashKey = get_hashed_key_for_attr(keypair.ss58_address, 'fetchAgentAddress')
    # print(f"testHashKey: {testHashKey}")
    # 0x90e519cb98c6b1f04b6bf6ce62d36b7cd092aa34e55e88f7d50691242267e14b -> right
    # 7c258cf38e595fbbc0c346f4656a3729a9b7053f023cc5e706d5d5fb0d47600b -> wrong
    # print(f"hashKey: {hashKey}")
    # result = substrate.query('PeaqStorage', 'ItemStore', [hashKey])
    # print(f"result: {result}")
    data = substrate.rpc_request('peaqstorage_readAttribute', [keypair.ss58_address, type.encode().hex()])
    print(f"data: {data}")
    itemHex = None
    if data and 'result' in data and data['result'] and 'item' in data['result']:
        itemHex = data['result']['item']
    item = bytes.fromhex(itemHex[2:]).decode('utf-8') if itemHex else None
    print(f"item: {item}")
    if item:
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
        keypair=keypair,
    )
    # Submit the transaction
    try:
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        print("Extrinsic '{}' sent and included in block '{}'".format(receipt.extrinsic_hash, receipt.block_hash))
    except SubstrateRequestException as e:
        print("Failed to send: {}".format(e))


def getAddressMapping(type: str):
    data = substrate.rpc_request('peaqstorage_readAttribute', [keypair.ss58_address, type.encode().hex()])
    print(f"data: {data}")
    itemHex = None
    if data and 'result' in data and data['result'] and 'item' in data['result']:
        itemHex = data['result']['item']
    item = bytes.fromhex(itemHex[2:]).decode('utf-8') if itemHex else None
    print(f"item: {item}")
    return item



# Query the balance of the corresponding address
# result = substrate.query('System', 'Account', [keypair.ss58_address])
# print(f"Address: {keypair.ss58_address}")
# print(f"Balance: {result.value['data']['free']} units")

class Transfer(Model):
    amount: int

bobSeed = "panic pretty surge torch reunion uncle execute snack silver praise math midnight"
bobAddress = "5FZpsT8LKCX7tMKNX7e24R1BgnMfzgSL1Y4V9enYFoYpSmft"
alice = Agent(name="alice", seed=seed, port=8000, endpoint=["http://127.0.0.1:8000/submit"])
bob = Agent(name="bob", seed="5FZpsT8LKCX7tMKNX7e24R1BgnMfzgSL1Y4V9enYFoYpSmft", port=8001, endpoint=["http://127.0.0.1:8001/submit"])


fund_agent_if_low(alice.wallet.address())
fund_agent_if_low(bob.wallet.address())

# storeAddressMapping(alice.address, keypair.ss58_address)

# @bob.on_event("startup")
@bob.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f'starting up {ctx.name}')
    await storeAddressMapping(f'{ctx.address}:{ctx.wallet.address()}', bobAddress)
    await storeAddressMapping(f'{bobAddress}', ctx.address.replace("agent", ""))
    ctx.logger.info(f'address mapping stored for {ctx.storage.get(f"pAM:{ctx.address}")}')





@bob.on_interval(period=2.0)
async def check_balance(ctx: Context):
    ctx.logger.info(f'hello, my name is {ctx.name}')
    # agent1q0zk0c8jm0qe46kyw9p6wkmz9y2fs7yf8t2k06ewt7m8mg08s8glkzde0yn -> 5FZpsT8LKCX7tMKNX7e24R1BgnMfzgSL1Y4V9enYFoYpSmft
    # agent1qwmwmsrcxpda0gnwrfvjhqgrjrad4uwdlw40y0kxlr6mmj7ynrxd28tdmrf -> 5FZpsT8LKCX7tMKNX7e24R1BgnMfzgSL1Y4V9enYFoYpSmftd
    ctx.logger.info(f'my address is {ctx.name}')
    balance = await getBalance(bobAddress)
    ctx.logger.info(f"Address: {bobAddress}")
    ctx.logger.info(
        f"Balance: {balance} {substrate.token_symbol}")
    if balance < minimum_balance:
        ctx.logger.info(f"Low balance, requesting {minimum_balance - balance} funds from {alice.name}")
        await ctx.send(alice.address, Transfer(amount=(minimum_balance - balance)))

@alice.on_interval(period=2.0)
async def get_balance(ctx: Context):
    ctx.logger.info(f'hello, my name is {ctx.name}')
    ctx.logger.info(f'my address is {ctx.address}')
    result = substrate.query('System', 'Account', [keypair.ss58_address])
    ctx.logger.info(f"Address: {keypair.ss58_address}")
    ctx.logger.info(
        f"Balance: {result.value['data']['free'] / 10 ** substrate.token_decimals} {substrate.token_symbol}")
    mappedAddress = getAddressMapping(bobAddress)
    agentWalletAddress = mappedAddress.split(':')[1]
    balance = ctx.ledger.query_bank_balance(agentWalletAddress)
    ctx.logger.info(f"bob's balance: {balance}")
        
    

# @alice.on_interval(period=2.0)
# async def send_message(ctx: Context):
#     msg = f'hello there {bob.name} my name is {alice.name}'
#     await ctx.send(bob.address, Transfer(address=bobAddress, amount=10 * 10 ** substrate.token_decimals))


@alice.on_message(model=Transfer)
async def message_handler(ctx: Context, sender: str, msg: Transfer):
    aliceBalance = await getBalance(keypair.ss58_address)
    senderAddress = getAddressMapping(sender.replace("agent", ""))
    ctx.logger.info(f"Received Transfer request from {senderAddress}: {msg.amount}")
    if aliceBalance < msg.amount:
        ctx.logger.info(f"Insufficient balance to transfer {msg.amount} {substrate.token_symbol} to {senderAddress}")
        return
    ctx.logger.info(f"Transferring {msg.amount} {substrate.token_symbol} to {senderAddress}")
    print("sender: ", sender)
    result = await transferBalance(senderAddress, msg.amount, keypair)
    ctx.logger.info(f"Transfer result: {result}")

# bureau = Bureau()
# bureau.add(alice)
# bureau.add(bob)
# transferBalance(bobAddress, 1 * 10**18, keypair)

if __name__ == "__main__":
    alice.run()
    bob.run()
    # bureau.run()
