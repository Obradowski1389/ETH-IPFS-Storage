from web3 import Web3
import os
from dotenv import load_dotenv

def check_balance():
    # Load environment variables
    load_dotenv()
    
    # Get account information from environment
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        print("Error: PRIVATE_KEY not found in environment variables")
        return

    # Connect to Ganache
    w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
    if not w3.is_connected():
        print("Error: Failed to connect to Ganache")
        return

    # Get account from private key
    account = w3.eth.account.from_key(private_key)
    address = account.address

    # Get balance
    balance = w3.eth.get_balance(address)
    balance_eth = w3.from_wei(balance, 'ether')

    # Get current gas price
    gas_price = w3.eth.gas_price
    gas_price_gwei = w3.from_wei(gas_price, 'gwei')

    # Estimate transaction cost (using typical gas limit of 60000)
    estimated_cost = w3.from_wei(gas_price * 60000, 'ether')

    print(f"\nAccount Information:")
    print(f"Address: {address}")
    print(f"Balance: {balance_eth} ETH")
    print(f"Balance in Wei: {balance}")
    print(f"Current gas price: {gas_price_gwei} gwei")
    print(f"Estimated transaction cost: {estimated_cost} ETH")

if __name__ == "__main__":
    check_balance() 