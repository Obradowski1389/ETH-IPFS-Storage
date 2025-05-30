from web3 import Web3
import json
import os
import time
from eth_account import Account

def get_ganache_account():
    # For Ganache with --wallet.deterministic flag, we know the first account's details
    address = "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"  # First deterministic account
    private_key = "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"
    
    # Create .env file if it doesn't exist
    env_path = '.env'
    if not os.path.exists(env_path):
        print(f"Creating new .env file at {env_path}")
    
    # Save to .env file
    env_content = f"""GANACHE_ACCOUNT_0_ADDRESS={address}
GANACHE_ACCOUNT_0_PRIVATE_KEY={private_key}
PRIVATE_KEY={private_key}
"""
    with open(env_path, 'w') as f:  # Use 'w' to overwrite any existing content
        f.write(env_content)
    
    print(f"\nGanache Account Information:")
    print(f"Address: {address}")
    print(f"Private Key: {private_key}")
    print(f"\nAccount information has been saved to {env_path}")

if __name__ == "__main__":
    get_ganache_account() 