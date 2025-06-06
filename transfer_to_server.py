from web3 import Web3
import json
import os
from eth_account import Account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to Ethereum node
w3 = Web3(Web3.HTTPProvider("http://localhost:8545"))
if not w3.is_connected():
    raise Exception("Failed to connect to Ethereum node")

# Load contract details
with open('hardhat/artifacts/contracts/DNetToken.sol/DNetToken.json', 'r') as f:
    dnet_data = json.load(f)
    DNET_ABI = dnet_data.get('abi', [])

with open('data/contract-address.json', 'r') as f:
    contract_info = json.load(f)
    DNET_ADDRESS = contract_info.get('address')

# Initialize contract
dnet_contract = w3.eth.contract(address=DNET_ADDRESS, abi=DNET_ABI)

# Get server wallet details
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    raise ValueError("PRIVATE_KEY environment variable is required")

ACCOUNT = Account.from_key(PRIVATE_KEY)
SERVER_ADDRESS = ACCOUNT.address

# Get Ganache account 0 details
GANACHE_ADDRESS = os.getenv("GANACHE_ACCOUNT_0_ADDRESS")
GANACHE_PRIVATE_KEY = os.getenv("GANACHE_ACCOUNT_0_PRIVATE_KEY")

if not GANACHE_ADDRESS or not GANACHE_PRIVATE_KEY:
    raise ValueError("GANACHE_ACCOUNT_0_ADDRESS and GANACHE_ACCOUNT_0_PRIVATE_KEY must be set in .env file")

def check_balances(address, is_server=True):
    """Check ETH and DNET balances for an address"""
    # Check ETH balance
    eth_balance = w3.eth.get_balance(address)
    eth_balance_in_eth = w3.from_wei(eth_balance, 'ether')
    print(f"{'Server' if is_server else 'Ganache'} ETH balance: {eth_balance_in_eth} ETH")

    # Check DNetToken balance
    token_balance = dnet_contract.functions.balanceOf(address).call()
    token_balance_in_tokens = token_balance / 10**18  # Convert from wei to tokens
    print(f"{'Server' if is_server else 'Ganache'} DNetToken balance: {token_balance_in_tokens} DNET")

def transfer_eth_to_server(amount_eth):
    """Transfer ETH from Ganache to server"""
    amount_wei = w3.to_wei(amount_eth, 'ether')
    
    # Build transaction
    nonce = w3.eth.get_transaction_count(GANACHE_ADDRESS)
    tx = {
        'from': GANACHE_ADDRESS,
        'to': SERVER_ADDRESS,
        'value': amount_wei,
        'nonce': nonce,
        'gas': 21000,  # Standard gas for ETH transfer
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id
    }

    # Sign and send transaction
    signed_tx = w3.eth.account.sign_transaction(tx, GANACHE_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    # Wait for transaction receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"ETH transfer successful! Hash: {receipt['transactionHash'].hex()}")

def transfer_dnet_to_server(amount_dnet):
    """Transfer DNET tokens from Ganache to server"""
    amount_wei = w3.to_wei(amount_dnet, 'ether')
    
    # Build transaction
    nonce = w3.eth.get_transaction_count(GANACHE_ADDRESS)
    tx = dnet_contract.functions.transfer(
        SERVER_ADDRESS,
        amount_wei
    ).build_transaction({
        'from': GANACHE_ADDRESS,
        'nonce': nonce,
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id
    })

    # Sign and send transaction
    signed_tx = w3.eth.account.sign_transaction(tx, GANACHE_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    # Wait for transaction receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"DNET transfer successful! Hash: {receipt['transactionHash'].hex()}")

def main():
    print("Current balances:")
    print("--------------------------------------------------")
    print(f"Server address: {SERVER_ADDRESS}")
    check_balances(SERVER_ADDRESS, True)
    print("\n--------------------------------------------------")
    print(f"Ganache address: {GANACHE_ADDRESS}")
    check_balances(GANACHE_ADDRESS, False)
    print("\n--------------------------------------------------")

    # Ask user for transfer amounts
    try:
        eth_amount = float(input("Enter amount of ETH to transfer to server: "))
        dnet_amount = float(input("Enter amount of DNET to transfer to server: "))
        
        if eth_amount > 0:
            print(f"\nTransferring {eth_amount} ETH to server...")
            transfer_eth_to_server(eth_amount)
        
        if dnet_amount > 0:
            print(f"\nTransferring {dnet_amount} DNET to server...")
            transfer_dnet_to_server(dnet_amount)
        
        # Show updated balances
        print("\nUpdated balances:")
        print("--------------------------------------------------")
        print(f"Server address: {SERVER_ADDRESS}")
        check_balances(SERVER_ADDRESS, True)
        print("\n--------------------------------------------------")
        print(f"Ganache address: {GANACHE_ADDRESS}")
        check_balances(GANACHE_ADDRESS, False)
        print("\n--------------------------------------------------")
        
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 