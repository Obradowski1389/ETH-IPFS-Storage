from web3 import Web3
from eth_account import Account
import os
from dotenv import load_dotenv
import json

# Enable new account creation
Account.enable_unaudited_hdwallet_features()

def generate_account():
    # Load environment variables
    load_dotenv()
    
    # Connect to Ganache
    w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
    if not w3.is_connected():
        raise Exception("Failed to connect to Ganache")

    # Generate new account
    account = Account.create()
    private_key = account.key.hex()
    address = account.address

    print("\nGenerated Ethereum Account:")
    print(f"Private Key: {private_key}")
    print(f"Address: {address}")

    # Get Ganache account from environment
    ganache_account = os.getenv('GANACHE_ACCOUNT_0_ADDRESS')
    ganache_private_key = os.getenv('GANACHE_ACCOUNT_0_PRIVATE_KEY')
    
    if not ganache_account or not ganache_private_key:
        print("\nWarning: Ganache account information not found in environment.")
        print("Please run get_ganache_account.py first to set up the environment.")
        return
    
    # Send 10 ETH to the new account
    amount = w3.to_wei(10, 'ether')
    nonce = w3.eth.get_transaction_count(ganache_account)
    
    transaction = {
        'nonce': nonce,
        'to': address,
        'value': amount,
        'gas': 21000,
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id
    }
    
    # Sign and send transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, ganache_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    
    # Wait for transaction to be mined
    print("\nFunding new account with 10 ETH...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Check new balance
    balance = w3.eth.get_balance(address)
    balance_eth = w3.from_wei(balance, 'ether')
    print(f"\nNew account funded successfully!")
    print(f"Current balance: {balance_eth} ETH")

    # Save private key to .env file
    env_content = f"PRIVATE_KEY={private_key}\n"
    with open('.env', 'a') as f:
        f.write(env_content)
    print("\nPrivate key has been saved to .env file")

if __name__ == "__main__":
    generate_account()
