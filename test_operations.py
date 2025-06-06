import requests, json, os, time
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base URL for the API
BASE_URL = "http://localhost:5000"

# Get user input for testing
USER_ID = input("Enter user ID for testing (e.g., test_user1): ").strip()
if not USER_ID:
    USER_ID = "test_user1"  # Default value if empty
    print(f"Using default user ID: {USER_ID}")

# Get server wallet details
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    raise ValueError("PRIVATE_KEY environment variable is required")

ACCOUNT = Account.from_key(PRIVATE_KEY)
SERVER_ADDRESS = ACCOUNT.address

def print_section(title, desc):
    """Print a formatted section title with description"""
    print(f"\n================= {title} : {desc} =================")

def test_register_user():
    """Register a new user and receive initial DNET tokens.
    
    This function:
    1. Sends a registration request with the user ID
    2. Creates a new Ethereum wallet for the user
    3. Receives 10 DNET tokens as initial balance
    4. Returns wallet details including address and private key
    """
    global USER_ID
    response = requests.post(f"{BASE_URL}/register", data={'user_id': USER_ID})
    if response.status_code == 200:
        data = response.json()
        print("Registration successful!")
        print(f"User ID: {data['user_id']}")
        print(f"Wallet address: {data['wallet_address']}")
        print(f"Private key: {data['private_key']}")
        print(f"Initial DNET: {data['initial_dnet']}")
        return data
    else:
        print(f"Registration failed: {response.text}")
        return None

def test_submit_metadata(user_data):
    """Submit metadata to IPFS and receive DNET tokens as reward.
    
    This function:
    1. Creates a sample metadata object with description and timestamp
    2. Submits the metadata to IPFS
    3. Stores the IPFS hash in the blockchain
    4. Receives DNET tokens as reward for submission
    5. Returns transaction details including IPFS hash and block number
    """
    
    metadata = {
        "description": "Test metadata submission",
        "timestamp": int(time.time()),
        "user_id": user_data['user_id']
    }
    
    data = {
        'user_id': user_data['user_id'],
        'user_wallet': user_data['wallet_address'],
        'metadata': json.dumps(metadata)
    }
    
    response = requests.post(f"{BASE_URL}/submit", data=data)
    if response.status_code == 200:
        data = response.json()
        print("Metadata submission successful!")
        print(f"IPFS hash: {data['ipfs_hash']}")
        print(f"Block number: {data['block_number']}")
        print(f"Reward: {data['reward']['amount']}")
        return data
    else:
        print(f"Metadata submission failed: {response.text}")
        return None

def test_check_transaction(wallet_address):
    """Check all transactions for a wallet address.
    
    This function:
    1. Retrieves all transactions (sent and received) for the wallet
    2. Displays transaction details including type, amount, and block number
    3. Returns the list of transactions
    """
    response = requests.get(f"{BASE_URL}/transactions/{wallet_address}")
    if response.status_code == 200:
        data = response.json()
        print("Transactions retrieved successfully!")
        print(f"Wallet address: {data['wallet_address']}")
        print("\nTransactions:")
        for tx in data['transactions']:
            if tx['type'] == 'received':
                print(f"Received {tx['amount']} from {tx['from']} (Block: {tx['block_number']})")
            else:  # sent
                print(f"Sent {tx['amount']} to {tx['to']} (Block: {tx['block_number']})")
        return data
    else:
        print(f"Failed to get transactions: {response.text}")
        return None

def test_check_validity(ipfs_hash):
    """Verify that metadata exists in both IPFS and blockchain.
    
    This function:
    1. Checks if the IPFS hash is stored in the blockchain
    2. Verifies the metadata can be retrieved from IPFS
    3. Returns verification status and blockchain details
    """
    
    response = requests.get(f"{BASE_URL}/verify/{ipfs_hash}")
    if response.status_code == 200:
        data = response.json()
        print("Verification successful!")
        print(f"Block number: {data['block_number']}")
        print(f"Transaction hash: {data['ethereum_tx_hash']}")
        return data
    else:
        print(f"Verification failed: {response.text}")
        return None

def test_get_balance(wallet_address):
    """Retrieve the current balance of a wallet.
    
    This function:
    1. Gets the current ETH balance of the wallet
    2. Gets the current DNET token balance
    3. Returns both balances in their respective units
    """
    
    response = requests.get(f"{BASE_URL}/balance/{wallet_address}")
    if response.status_code == 200:
        data = response.json()
        print("Balance retrieved successfully!")
        print(f"Wallet address: {data['wallet_address']}")
        print(f"ETH balance: {data['eth_balance']}")
        print(f"DNET balance: {data['dnet_balance']}")
        return data
    else:
        print(f"Balance check failed: {response.text}")
        return None

def test_burn_tokens(user_data, amount):
    """Burn a specified amount of DNET tokens.
    
    This function:
    1. Sends a burn request with the specified amount
    2. Verifies the burn transaction
    3. Returns transaction details including block number
    """
    
    data = {
        'from_wallet': user_data['wallet_address'],
        'private_key': user_data['private_key'],
        'amount': amount
    }
    
    response = requests.post(f"{BASE_URL}/burn", json=data)
    if response.status_code == 200:
        data = response.json()
        print("Tokens burned successfully!")
        print(f"Transaction hash: {data['burn_tx_hash']}")
        print(f"Block number: {data['block_number']}")
        return data
    else:
        print(f"Burn failed: {response.text}")
        return None

def test_submit_file(user_data):
    """Submit a file to IPFS and receive DNET tokens as reward.
    
    This function:
    1. Creates a test file with sample content
    2. Creates metadata with description and timestamp
    3. Submits both file and metadata to IPFS
    4. Stores the IPFS hash in the blockchain
    5. Receives DNET tokens as reward
    6. Returns transaction details including IPFS hash and block number
    """
    
    # Create a test file
    with open('test.txt', 'w') as f:
        f.write("This is a test file content.")
    
    # Create metadata
    metadata = {
        "description": "Test file submission",
        "timestamp": int(time.time()),
        "user_id": user_data['user_id']
    }
    
    with open('test.txt', 'rb') as f:
        files = {'file': f}
        data = {
            'user_id': user_data['user_id'],
            'user_wallet': user_data['wallet_address'],
            'metadata': json.dumps(metadata)
        }
        response = requests.post(f"{BASE_URL}/submit", files=files, data=data)
    
    if response.status_code == 200:
        data = response.json()
        print("File submission successful!")
        print(f"IPFS hash: {data['ipfs_hash']}")
        print(f"Block number: {data['block_number']}")
        print(f"Reward: {data['reward']['amount']}")
        return data
    else:
        print(f"File submission failed: {response.text}")
        return None

def test_retrieve_metadata(ipfs_hash):
    """Test metadata retrieval"""
    
    response = requests.get(f"{BASE_URL}/retrieve/{ipfs_hash}")
    
    if response.status_code == 200:
        data = response.json()
        print("Metadata retrieved successfully!")
        print(json.dumps(data, indent=2))
        return data
    else:
        print(f"Failed to retrieve metadata: {response.text}")
        return None

def test_get_total_supply():
    """Test total supply check"""
    
    response = requests.get(f"{BASE_URL}/total-supply")
    
    if response.status_code == 200:
        data = response.json()
        print("Total supply retrieved successfully!")
        print(f"Total supply: {data['total_supply']}")
        return data
    else:
        print(f"Failed to get total supply: {response.text}")
        return None

def test_retrieve_file(ipfs_hash):
    """Test file retrieval"""
    
    response = requests.get(f"{BASE_URL}/retrieve/{ipfs_hash}")
    
    if response.status_code == 200:
        print("File retrieved successfully!")
        return response
    else:
        print(f"Failed to retrieve file: {response}")
        return None

def main():
    """Main function to run all test operations in sequence.
    
    Test Flow:
    1. Register user
    2. Submit metadata
    3. Check transaction
    4. Check validity
    5. Get metadata
    6. Get balance
    7. Submit file
    8. Check transaction
    9. Check validity
    10. Get file
    11. Get balance
    12. Get total supply
    13. Burn coins
    14. Check server transactions
    15. Check server balance
    """    
    try:
        # 1. Register user
        print_section("1. User Registration", "Register a new user and get wallet address")
        user_data = test_register_user()
        if not user_data:
            return
            
        # 2. Submit metadata
        print_section("#2 Submit metadata", "Submit metadata to IPFS and get DNET reward")
        metadata_result = test_submit_metadata(user_data)
        if not metadata_result:
            return
            
        # 3. Check transactions
        print_section("#3 Check transactions", "Check all transactions for user wallet")
        tx_result = test_check_transaction(user_data['wallet_address'])
        if not tx_result:
            return
            
        # 4. Check validity
        print_section("#4 Check validity", "Verify metadata hash in blockchain")
        validity_result = test_check_validity(metadata_result['ipfs_hash'])
        if not validity_result:
            return
            
        # 5. Retrieve metadata
        print_section("#5 Retrieve metadata", "Get metadata from IPFS")
        retrieve_result = test_retrieve_metadata(metadata_result['ipfs_hash'])
        if not retrieve_result:
            return
            
        # 6. Get balance
        print_section("#6 Get balance", "Check user wallet balance")
        balance_result = test_get_balance(user_data['wallet_address'])
        if not balance_result:
            return
            
        # 7. Submit file
        print_section("#7 Submit file", "Submit test.txt to IPFS")
        file_result = test_submit_file(user_data)
        if not file_result:
            return
            
        # 8. Check transactions
        print_section("#8 Check transactions", "Check all transactions for user wallet")
        tx_result = test_check_transaction(user_data['wallet_address'])
        if not tx_result:
            return
            
        # 9. Check validity
        print_section("#9 Check validity", "Verify file hash in blockchain")
        validity_result = test_check_validity(file_result['ipfs_hash'])
        if not validity_result:
            return
            
        # 10. Retrieve file
        print_section("#10 Retrieve file", "Get file from IPFS")
        retrieve_result = test_retrieve_file(file_result['ipfs_hash'])
        if not retrieve_result:
            return
            
        # 11. Check balance
        print_section("#11 Check balance", "Check user wallet balance")
        balance_result = test_get_balance(user_data['wallet_address'])
        if not balance_result:
            return
            
        # 12. Get total supply
        print_section("#12 Total supply", "Get total DNET token supply")
        supply_result = test_get_total_supply()
        if not supply_result:
            return
            
        # 13. Burn tokens
        print_section("#13 Burn tokens", "Burn DNET tokens from server wallet")
        burn_result = test_burn_tokens({
            'wallet_address': SERVER_ADDRESS,
            'private_key': PRIVATE_KEY
        }, "1")
        if not burn_result:
            return
            
        # 14. Get server transactions
        print_section("#14 Server transactions", "Check all transactions for server wallet")
        tx_result = test_check_transaction(SERVER_ADDRESS)
        if not tx_result:
            return
            
        # 15. Get server balance
        print_section("#15 Server balance", "Check server wallet balance")
        balance_result = test_get_balance(SERVER_ADDRESS)
        if not balance_result:
            return
            
        print("\nAll operations completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        return

if __name__ == "__main__":
    main() 