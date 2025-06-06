import json, os, hashlib, mysql.connector
from flask import Flask, request, jsonify
from eth_account import Account
from dotenv import load_dotenv
import base64, time, logging
from web3 import Web3
import ipfshttpclient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)

# Setup web3
ETHEREUM_NODE_URL = os.getenv("ETHEREUM_NODE_URL", "http://localhost:8545")
logger.info(f"Connecting to Ethereum node at {ETHEREUM_NODE_URL}")

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(ETHEREUM_NODE_URL))
logger.info(f"Connecting to Ethereum node at {ETHEREUM_NODE_URL}")

# Check connection
try:
    w3.eth.get_block_number()
    logger.info("Successfully connected to Ethereum node")
except Exception as e:
    logger.error(f"Failed to connect to Ethereum node: {str(e)}")
    raise

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    logger.error("PRIVATE_KEY environment variable is not set")
    raise ValueError("PRIVATE_KEY environment variable is required")

try:
    ACCOUNT = Account.from_key(PRIVATE_KEY)
    SENDER_ADDRESS = ACCOUNT.address
    logger.info(f"Loaded account: {SENDER_ADDRESS}")
except Exception as e:
    logger.error(f"Failed to load account: {str(e)}")
    raise

# Load DNetToken ABI
try:
    with open('DNetToken.json', 'r') as f:
        dnet_data = json.load(f)
        DNET_ABI = dnet_data.get('abi', [])
        if not DNET_ABI:
            raise ValueError("No ABI found in DNetToken.json")
except FileNotFoundError:
    logger.error("DNetToken.json file not found")
    raise
except json.JSONDecodeError as e:
    logger.error(f"Error parsing DNetToken.json: {str(e)}")
    raise
except Exception as e:
    logger.error(f"Error loading DNetToken ABI: {str(e)}")
    raise

# Load contract address
try:
    with open('data/contract-address.json', 'r') as f:
        contract_info = json.load(f)
        DNET_ADDRESS = contract_info.get('address')
        if not DNET_ADDRESS:
            raise ValueError("No contract address found in contract-address.json")
        logger.info(f"Loaded DNetToken contract address: {DNET_ADDRESS}")
except FileNotFoundError:
    logger.error("contract-address.json file not found")
    raise
except json.JSONDecodeError as e:
    logger.error(f"Error parsing contract-address.json: {str(e)}")
    raise
except Exception as e:
    logger.error(f"Error loading contract address: {str(e)}")
    raise

dnet_contract = w3.eth.contract(address=DNET_ADDRESS, abi=DNET_ABI)

# Setup IPFS client
IPFS_NODE_URL = os.getenv("IPFS_NODE_URL", "http://localhost:5001")
logger.info(f"Connecting to IPFS node at {IPFS_NODE_URL}")

# Setup reward amount
DEFAULT_REWARD_AMOUNT = os.getenv("DEFAULT_REWARD_AMOUNT", "1")
logger.info(f"Default reward amount: {DEFAULT_REWARD_AMOUNT} DNET")

INITIAL_DNET_AMOUNT = int(os.getenv("INITIAL_DNET_AMOUNT", "10"))
REWARD_DNET_AMOUNT = int(os.getenv("REWARD_DNET_AMOUNT", "1"))

# Custom IPFS client class to handle newer IPFS versions
class CustomIPFSClient:
    def __init__(self, ipfs_url):
        self.ipfs_url = ipfs_url
        try:
            # Suppress version check warning
            import warnings
            warnings.filterwarnings("ignore", category=ipfshttpclient.exceptions.VersionMismatch)
            
            self.client = ipfshttpclient.connect(ipfs_url)
            # Override version check to return a compatible version
            self.client.version = lambda: {"Version": "0.8.0"}
            logger.info(f"Connected to IPFS node at {ipfs_url}")
        except Exception as e:
            logger.error(f"Failed to connect to IPFS node: {str(e)}")
            raise

    def add(self, data):
        """Add data to IPFS and return the hash"""
        try:
            # Convert to bytes if it's a string
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Add to IPFS
            result = self.client.add_bytes(data)
            logger.info(f"Added data to IPFS: {result}")
            return {'Hash': result}
        except Exception as e:
            logger.error(f"Error adding data to IPFS: {str(e)}")
            raise

    def add_json(self, json_data):
        """Add JSON data to IPFS and return the hash"""
        try:
            # Convert to JSON string if it's a dict
            if isinstance(json_data, dict):
                json_data = json.dumps(json_data)
            
            # Convert to bytes if it's a string
            if isinstance(json_data, str):
                json_data = json_data.encode('utf-8')
            
            # Add to IPFS
            result = self.client.add_bytes(json_data)
            logger.info(f"Added JSON to IPFS: {result}")
            return result
        except Exception as e:
            logger.error(f"Error adding JSON to IPFS: {str(e)}")
            raise

    def get_json(self, ipfs_hash):
        """Retrieve and parse JSON data from IPFS"""
        try:
            # Get the data from IPFS
            data = self.client.get_json(ipfs_hash)
            logger.info(f"Retrieved JSON from IPFS: {data}")
            return data
        except Exception as e:
            logger.error(f"Error getting JSON from IPFS: {str(e)}")
            raise

# Initialize IPFS client
ipfs_client = CustomIPFSClient(IPFS_NODE_URL)

# MySQL connection setup
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
MYSQL_USER = os.getenv('MYSQL_USER', 'dnetuser')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'dnetpass')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'eth_storage')

def get_mysql_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )

def init_mysql():
    conn = get_mysql_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id VARCHAR(255) PRIMARY KEY,
        wallet_address VARCHAR(255),
        private_key VARCHAR(255)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS token_transfers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        from_address VARCHAR(255),
        to_address VARCHAR(255),
        amount VARCHAR(255),
        tx_hash VARCHAR(255),
        block_number INT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()
init_mysql()

def wait_for_transaction(tx_hash, max_attempts=30):
    """Wait for transaction to be mined"""
    for _ in range(max_attempts):
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                return receipt
        except Exception:
            pass
        time.sleep(1)
    raise Exception("Transaction not mined after maximum attempts")

def store_json_to_ipfs(json_data):
    """Store JSON data to IPFS"""
    json_str = json.dumps(json_data, sort_keys=True)
    result = ipfs_client.add_json(json_str)
    return result

def get_metadata_from_blockchain(ipfs_hash):
    logger.info("=== Starting get_metadata_from_blockchain ===")
    logger.info(f"Received IPFS hash: {ipfs_hash}")

    latest_block = w3.eth.block_number
    start_block = max(0, latest_block - 10000)
    logger.info(f"Scanning from block {latest_block} to {start_block}")

    try:
        # ABI-encode function call using web3 to match actual tx input
        keccak_hash = Web3.keccak(text=ipfs_hash)
        expected_input = dnet_contract.encodeABI(
            fn_name="storeMetadataHash",
            args=[keccak_hash]
        )
        logger.info(f"Expected transaction input: {expected_input}")

        for block_number in range(latest_block, start_block - 1, -1):
            logger.info(f"Processing block {block_number}")
            block = w3.eth.get_block(block_number, full_transactions=True)
            logger.info(f"Block {block_number} has {len(block.transactions)} transactions")

            for tx in block.transactions:
                try:
                    tx_input = tx['input'].lower()
                    if tx_input == expected_input.lower():
                        logger.info(f"Match found in tx {tx['hash'].hex()} at block {block_number}")
                        receipt = w3.eth.get_transaction_receipt(tx['hash'])
                        return {
                            'ethereum_tx_hash': tx['hash'].hex(),
                            'block_number': block_number,
                            'from': tx['from']
                        }
                except Exception as e:
                    logger.error(f"Error processing transaction: {str(e)}")
                    continue

    except Exception as e:
        logger.error(f"Error processing blocks: {str(e)}")
        raise

    logger.info("No matching transaction found")
    return None


def log_token_transfer(from_address, to_address, amount, tx_hash, block_number):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO token_transfers (from_address, to_address, amount, tx_hash, block_number)
            VALUES (%s, %s, %s, %s, %s)
        ''', (from_address, to_address, str(amount), tx_hash, block_number))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log token transfer: {str(e)}")

def hash_private_key(private_key):
    return hashlib.sha256(private_key.encode()).hexdigest()

def validate_user(user_id, user_wallet):
    """Check if user exists in database"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # Log the query parameters
        logger.info(f"Validating user - ID: {user_id}, Wallet: {user_wallet}")
        
        # Check if user exists with matching wallet
        cursor.execute(
            "SELECT * FROM users WHERE user_id = %s AND wallet_address = %s",
            (user_id, user_wallet)
        )
        result = cursor.fetchone()
        
        # Log the query result
        logger.info(f"User validation result: {result}")
        
        cursor.close()
        conn.close()
        
        return result is not None
    except Exception as e:
        logger.error(f"Error validating user: {str(e)}")
        return False

@app.route('/submit', methods=['POST'])
def submit():
    """Submit metadata and optionally a file to IPFS and blockchain"""
    try:
        user_id = request.form.get('user_id')
        user_wallet = request.form.get('user_wallet')
        metadata = request.form.get('metadata')
        file = request.files.get('file')
        
        logger.info(f"Received submission request for user: {user_id}")
        logger.info(f"User wallet: {user_wallet}")
        logger.info(f"Metadata: {metadata}")
        logger.info(f"File provided: {file is not None}")
        logger.info(f"Reward amount: {REWARD_DNET_AMOUNT} DNET")
        
        if not all([user_id, user_wallet, metadata]):
            return jsonify({"error": "Missing required parameters"}), 400
            
        # Validate user
        if not validate_user(user_id, user_wallet):
            return jsonify({"error": "Invalid user"}), 401
            
        # Store metadata and file in IPFS
        ipfs_hash = None
        file_hash = None
        try:
            # Convert metadata to JSON string
            metadata_json = json.dumps(json.loads(metadata))
            
            # Add to IPFS
            if file:
                # Store file first
                file_content = file.read()
                file_result = ipfs_client.add(file_content)
                file_hash = file_result['Hash']
                
                # Add file hash to metadata
                metadata_dict = json.loads(metadata_json)
                metadata_dict['file_hash'] = file_hash
                metadata_json = json.dumps(metadata_dict)
            
            # Store metadata
            ipfs_hash = ipfs_client.add_json(metadata_json)
            
            logger.info(f"Stored in IPFS with hash: {ipfs_hash}")
            
            # Verify IPFS storage
            try:
                retrieved_data = ipfs_client.get_json(ipfs_hash)
                if retrieved_data != json.loads(metadata_json):
                    logger.error("IPFS verification failed")
                    return jsonify({"error": "Failed to verify IPFS storage"}), 500
            except Exception as e:
                logger.error(f"IPFS verification error: {str(e)}")
                return jsonify({"error": "Failed to verify IPFS storage"}), 500
                
        except Exception as e:
            logger.error(f"Failed to store metadata to IPFS: {str(e)}")
            return jsonify({"error": "Failed to store metadata"}), 500
            
        # Only proceed with blockchain operations if IPFS storage was successful
        if not ipfs_hash:
            return jsonify({"error": "IPFS storage failed"}), 500
            
        # Store hash in blockchain and send reward
        try:
            # Get the contract instance
            contract = w3.eth.contract(address=DNET_ADDRESS, abi=DNET_ABI)
            
            # Use the account from the private key
            sender = SENDER_ADDRESS
            
            # Get current gas price
            gas_price = w3.eth.gas_price
            
            # Encode the IPFS hash
            logger.info(f"Original metadata hash: {ipfs_hash}")
            encoded_hash = ipfs_hash.encode('utf-8')
            logger.info(f"Encoded metadata hash: {encoded_hash}")
            hex_hash = encoded_hash.hex()
            logger.info(f"Hex encoded metadata hash: {hex_hash}")
            
            # Get current nonce
            nonce = w3.eth.get_transaction_count(sender)
            
            # Convert IPFS hash to bytes32
            hash_bytes32 = w3.keccak(text=ipfs_hash)
            logger.info(f"Bytes32 hash: {hash_bytes32.hex()}")

            # First, store the metadata hash in blockchain
            store_tx = contract.functions.storeMetadataHash(hash_bytes32).build_transaction({
                'from': sender,
                'nonce': nonce,
                'gasPrice': gas_price,
                'chainId': w3.eth.chain_id
            })
            
            # Sign and send the transaction
            signed_txn = w3.eth.account.sign_transaction(store_tx, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] != 1:
                return jsonify({"error": "Failed to store metadata hash"}), 500
                
            # Get the block number
            block_number = receipt['blockNumber']
            
            # Store the transaction in database
            conn = get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO token_transfers (from_address, to_address, amount, tx_hash, block_number) VALUES (%s, %s, %s, %s, %s)",
                (sender, DNET_ADDRESS, "0", tx_hash.hex(), block_number)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            # Now send reward tokens after successful hash storage
            nonce = w3.eth.get_transaction_count(sender)  # Get new nonce for reward transaction
            reward_amount_wei = w3.toWei(REWARD_DNET_AMOUNT, 'ether')
            
            # Build and send reward transaction
            reward_tx = contract.functions.transfer(user_wallet, reward_amount_wei).build_transaction({
                'from': sender,
                'nonce': nonce,
                'gasPrice': gas_price,
                'chainId': w3.eth.chain_id
            })
            
            # Sign and send reward transaction
            signed_reward_tx = w3.eth.account.sign_transaction(reward_tx, PRIVATE_KEY)
            reward_tx_hash = w3.eth.send_raw_transaction(signed_reward_tx.rawTransaction)
            reward_receipt = wait_for_transaction(reward_tx_hash)
            
            if reward_receipt['status'] != 1:
                return jsonify({"error": "Reward transfer failed"}), 500
                
            # Log the reward transfer
            log_token_transfer(sender, user_wallet, reward_amount_wei, reward_tx_hash.hex(), reward_receipt['blockNumber'])
                
            return jsonify({
                "message": "Data submitted successfully",
                "ipfs_hash": ipfs_hash,
                "transaction_hash": tx_hash.hex(),
                "block_number": block_number,
                "reward": {
                    "amount": f"{REWARD_DNET_AMOUNT} DNET",  # Convert to string with unit
                    "transaction_hash": reward_tx_hash.hex()
                }
            })
            
        except Exception as e:
            logger.error(f"Error storing metadata hash: {str(e)}")
            return jsonify({"error": str(e)}), 500
            
    except Exception as e:
        logger.error(f"Error in submit: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/retrieve/<ipfs_hash>', methods=['GET'])
def retrieve_file(ipfs_hash):
    try:
        # First, find the transaction in the blockchain
        blockchain_data = get_metadata_from_blockchain(ipfs_hash)
        if not blockchain_data:
            return jsonify({"error": "Hash not found in blockchain"}), 404

        # Get metadata from IPFS
        try:
            metadata = ipfs_client.get_json(ipfs_hash)
        except Exception as e:
            logger.error(f"Error retrieving metadata from IPFS: {str(e)}")
            return jsonify({"error": "Failed to retrieve metadata from IPFS"}), 500

        response = {
            "metadata": metadata,
            "blockchain_data": blockchain_data
        }

        # If there's a file hash, retrieve the file
        if metadata.get('file_hash'):
            try:
                file_data = ipfs_client.get_json(metadata['file_hash'])
                response["file_data"] = base64.b64encode(file_data).decode('utf-8')
            except Exception as e:
                response["file_error"] = str(e)

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in retrieve_file: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/verify/<ipfs_hash>', methods=['GET'])
def verify_file(ipfs_hash):
    try:
        # Determine if user passed a tx hash instead of IPFS hash
        is_tx_hash = ipfs_hash.startswith("0x") and len(ipfs_hash) == 66  # 32-byte hash + '0x'

        if is_tx_hash:
            logger.info("Assuming user passed a transaction hash directly")
            tx_hash = ipfs_hash
            try:
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                tx = w3.eth.get_transaction(tx_hash)
                tx_input = tx['input']
                logger.info(f"Extracted tx input: {tx_input}")
                ipfs_hash_bytes32 = tx_input[-64:]  # last 32 bytes = keccak(IPFS string)
            except Exception as e:
                logger.error(f"Transaction not found: {str(e)}")
                return jsonify({"error": "Transaction not found"}), 404

            # No way to reverse keccak to get original IPFS hash
            return jsonify({
                "verified": True,
                "block_number": receipt['blockNumber'],
                "ethereum_tx_hash": tx_hash,
                "note": "IPFS hash cannot be derived from keccak; only tx verified"
            })

        else:
            logger.info("Assuming user passed a raw IPFS hash")
            blockchain_data = get_metadata_from_blockchain(ipfs_hash)
            if not blockchain_data:
                return jsonify({"error": "Hash not found in blockchain"}), 404

            try:
                metadata = ipfs_client.get_json(ipfs_hash)
            except Exception as e:
                logger.error(f"Error retrieving metadata from IPFS: {str(e)}")
                return jsonify({"error": "Failed to retrieve metadata from IPFS"}), 500

            return jsonify({
                "verified": True,
                "block_number": blockchain_data['block_number'],
                "ethereum_tx_hash": blockchain_data['ethereum_tx_hash'],
                "metadata": metadata
            })

    except Exception as e:
        logger.error(f"Error in verify_file: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Check Ethereum connection
        eth_connected = w3.is_connected()
        
        # Check IPFS connection
        ipfs_connected = ipfs_client.id() is not None
        
        return jsonify({
            "status": "healthy" if eth_connected and ipfs_connected else "unhealthy",
            "ethereum_connected": eth_connected,
            "ipfs_connected": ipfs_connected
        })
    except Exception as e:
        logger.error(f"Error in health_check: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/register', methods=['POST'])
def register():
    """Register a new user and send initial DNET tokens"""
    try:
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
            
        # Check if user already exists
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "User already exists"}), 400
            
        # Create new account
        account = w3.eth.account.create()
        wallet_address = account.address
        private_key = account.key.hex()
        # Hashed key is saved in db
        hashed_key = hash_private_key(private_key)

        # Store user in database
        cursor.execute(
            "INSERT INTO users (user_id, wallet_address, private_key) VALUES (%s, %s, %s)",
            (user_id, wallet_address, hashed_key)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Send initial DNET tokens
        try:
            # Get the contract instance
            contract = w3.eth.contract(address=DNET_ADDRESS, abi=DNET_ABI)
            
            # Use the account from the private key
            sender = SENDER_ADDRESS
            
            # Build the transaction
            initial_amount = w3.toWei(INITIAL_DNET_AMOUNT, 'ether')

            nonce = w3.eth.get_transaction_count(sender)
            gas_price = w3.eth.gas_price
    
            # Build the transaction
            transaction = contract.functions.transfer(wallet_address, initial_amount).build_transaction({
                'from': sender,
                'nonce': nonce,
                'gasPrice': gas_price,
                'chainId': w3.eth.chain_id
            })
            
            # Sign and send the transaction
            signed_txn = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] != 1:
                return jsonify({"error": "Token transfer failed"}), 500
                
            # Get the block number
            block_number = receipt['blockNumber']
            
            # Store the transfer in database
            conn = get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO token_transfers (from_address, to_address, amount, tx_hash, block_number) VALUES (%s, %s, %s, %s, %s)",
                (sender, wallet_address, "10", tx_hash.hex(), block_number)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Initial DNET tokens sent to {wallet_address}")
            
            return jsonify({
                "user_id": user_id,
                "wallet_address": wallet_address,
                "private_key": private_key,
                "initial_dnet": "10 DNET",
                "transaction_hash": tx_hash.hex(),
                "block_number": block_number
            })
            
        except Exception as e:
            logger.error(f"Error sending initial tokens: {str(e)}")
            return jsonify({"error": str(e)}), 500
            
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/balance/<wallet_address>', methods=['GET'])
def get_balance(wallet_address):
    try:
        # Get DNET balance
        dnet_balance = dnet_contract.functions.balanceOf(wallet_address).call()
        # Convert from wei to DNET (assuming 18 decimals)
        dnet_balance_in_tokens = w3.fromWei(dnet_balance, 'ether')
        
        # Get ETH balance
        eth_balance = w3.eth.get_balance(wallet_address)
        eth_balance_in_eth = w3.fromWei(eth_balance, 'ether')
        
        return jsonify({
            "wallet_address": wallet_address,
            "eth_balance": str(eth_balance_in_eth) + " ETH",
            "dnet_balance": str(dnet_balance_in_tokens) + " DNET"
        })
    except Exception as e:
        logger.error(f"Error getting balance: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/total-supply', methods=['GET'])
def get_total_supply():
    try:
        total_supply = dnet_contract.functions.totalSupply().call()
        # Convert from wei to DNET (assuming 18 decimals)
        total_supply_in_dnet = w3.fromWei(total_supply, 'ether')
        return jsonify({
            "total_supply": str(total_supply_in_dnet) + " DNET"
        })
    except Exception as e:
        logger.error(f"Error getting total supply: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/transactions/<wallet_address>', methods=['GET'])
def get_transactions(wallet_address):
    try:
        # Get the latest block number
        latest_block = w3.eth.block_number
        start_block = max(0, latest_block - 10000)  # Look back 10000 blocks
        
        transactions = []
        
        # Get Transfer events for the wallet
        transfer_filter = {
            'fromBlock': start_block,
            'toBlock': latest_block,
            'address': DNET_ADDRESS,
            'topics': [
                w3.keccak(text='Transfer(address,address,uint256)').hex(),
                None,
                '0x' + wallet_address.lower()[2:].zfill(64)  # Remove 0x prefix before padding
            ]
        }
        
        # Get events where the wallet is the sender
        sent_filter = {
            'fromBlock': start_block,
            'toBlock': latest_block,
            'address': DNET_ADDRESS,
            'topics': [
                w3.keccak(text='Transfer(address,address,uint256)').hex(),
                '0x' + wallet_address.lower()[2:].zfill(64),  # Remove 0x prefix before padding
                None
            ]
        }
        
        # Get received transfers
        received_logs = w3.eth.get_logs(transfer_filter)
        for log in received_logs:
            event = dnet_contract.events.Transfer().processLog(log)
            transactions.append({
                'type': 'received',
                'from': event['args']['from'],
                'amount': str(w3.fromWei(event['args']['value'], 'ether')) + " DNET",
                'block_number': log['blockNumber'],
                'transaction_hash': log['transactionHash'].hex()
            })
            
        # Get sent transfers
        sent_logs = w3.eth.get_logs(sent_filter)
        for log in sent_logs:
            event = dnet_contract.events.Transfer().processLog(log)
            transactions.append({
                'type': 'sent',
                'to': event['args']['to'],
                'amount': str(w3.fromWei(event['args']['value'], 'ether')) + " DNET",
                'block_number': log['blockNumber'],
                'transaction_hash': log['transactionHash'].hex()
            })
            
        # Sort transactions by block number (newest first)
        transactions.sort(key=lambda x: x['block_number'], reverse=True)
        
        return jsonify({
            "wallet_address": wallet_address,
            "transactions": transactions
        })
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/burn', methods=['POST'])
def burn_tokens():
    try:
        data = request.get_json()
        from_wallet = data.get('from_wallet')
        private_key = data.get('private_key')
        amount = data.get('amount')

        if not from_wallet or not private_key or not amount:
            # Retrieve user by wallet address
            conn = get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, private_key FROM users WHERE wallet_address = %s", (from_wallet,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "Wallet not registered"}), 404

            # Validate private key by comparing hashes
            hashed_input = hash_private_key(private_key)
            if hashed_input != user['private_key']:
                return jsonify({"error": "Invalid private key"}), 403

        amount_wei = w3.toWei(amount, 'ether')

        # Build the burn transaction
        burn_tx = dnet_contract.functions.burn(amount_wei).build_transaction({
            'from': from_wallet,
            'nonce': w3.eth.get_transaction_count(from_wallet),
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id
        })

        # Sign and send burn transaction with user's key
        signed_burn = w3.eth.account.sign_transaction(burn_tx, private_key)
        burn_tx_hash = w3.eth.send_raw_transaction(signed_burn.rawTransaction)
        burn_receipt = wait_for_transaction(burn_tx_hash)

        if burn_receipt['status'] != 1:
            return jsonify({"error": "Burn failed"}), 500

        log_token_transfer(from_wallet, "0x0000000000000000000000000000000000000000", amount_wei, burn_tx_hash.hex(), burn_receipt['blockNumber'])

        return jsonify({
            "message": "Tokens burned successfully",
            "burn_tx_hash": burn_tx_hash.hex(),
            "block_number": burn_receipt['blockNumber']
        })

    except Exception as e:
        logger.error(f"Error burning tokens: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', debug=True)
