from flask import Flask, request, jsonify
from web3 import Web3
import json
import os
from eth_account import Account
from dotenv import load_dotenv
import hashlib
import ipfshttpclient
import base64
import time
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)

# Setup web3
ETHEREUM_NODE_URL = os.getenv("ETHEREUM_NODE_URL", "http://localhost:8545")
logger.info(f"Connecting to Ethereum node at {ETHEREUM_NODE_URL}")
w3 = Web3(Web3.HTTPProvider(ETHEREUM_NODE_URL))
if not w3.is_connected():
    logger.error("Failed to connect to Ethereum node")
    raise Exception("Failed to connect to Ethereum node")
logger.info("Connected to Ethereum node")

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

# Setup IPFS client
IPFS_NODE_URL = os.getenv("IPFS_NODE_URL", "/dns4/ipfs/tcp/5001/http")
logger.info(f"Connecting to IPFS node at {IPFS_NODE_URL}")

# Custom IPFS client class to handle newer IPFS versions
class CustomIPFSClient:
    def __init__(self, api_url):
        self.api_url = api_url.replace('/dns4/', 'http://').replace('/tcp/', ':').replace('/http', '')
        logger.info(f"Using IPFS API URL: {self.api_url}")

    def add(self, file):
        files = {'file': file}
        response = requests.post(f"{self.api_url}/api/v0/add", files=files)
        response.raise_for_status()
        return response.json()

    def add_json(self, json_str):
        files = {'file': ('data.json', json_str)}
        response = requests.post(f"{self.api_url}/api/v0/add", files=files)
        response.raise_for_status()
        return response.json()['Hash']

    def cat(self, ipfs_hash):
        response = requests.post(f"{self.api_url}/api/v0/cat", params={'arg': ipfs_hash})
        response.raise_for_status()
        return response.content

    def id(self):
        response = requests.post(f"{self.api_url}/api/v0/id")
        response.raise_for_status()
        return response.json()

try:
    ipfs_client = CustomIPFSClient(IPFS_NODE_URL)
    ipfs_id = ipfs_client.id()
    logger.info(f"Connected to IPFS node: {ipfs_id['ID']}")
except Exception as e:
    logger.error(f"Failed to connect to IPFS node: {str(e)}")
    raise

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
    """Retrieve metadata from blockchain by scanning recent blocks"""
    # Get the latest block number
    latest_block = w3.eth.block_number
    # Look back up to 1000 blocks
    start_block = max(0, latest_block - 1000)
    
    # Convert IPFS hash to hex format for comparison
    ipfs_hash_hex = '0x' + ipfs_hash.encode().hex()
    
    for block_number in range(latest_block, start_block - 1, -1):
        block = w3.eth.get_block(block_number, full_transactions=True)
        for tx in block.transactions:
            if tx['to'] == '0x0000000000000000000000000000000000000000':  # Zero address
                try:
                    # Compare the transaction input with our IPFS hash
                    if tx['input'] == ipfs_hash_hex:
                        # Found the transaction, now get the receipt
                        receipt = w3.eth.get_transaction_receipt(tx['hash'])
                        return {
                            'ethereum_tx_hash': tx['hash'].hex(),
                            'block_number': block_number,
                            'from': tx['from']
                        }
                except Exception as e:
                    logger.error(f"Error processing transaction: {str(e)}")
                    continue
    return None

@app.route('/submit', methods=['POST'])
def submit_data():
    try:
        # Get user_id from form data
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        # Get metadata from form data
        metadata = {}
        if 'metadata' in request.form:
            try:
                metadata = json.loads(request.form['metadata'])
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid JSON metadata"}), 400

        # Handle file upload if present
        file_hash = None
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                ipfs_result = ipfs_client.add(file)
                file_hash = ipfs_result['Hash']
                metadata['file_name'] = file.filename

                # Check if this file was already uploaded
                try:
                    existing_metadata = ipfs_client.cat(file_hash)
                    logger.info(f"File {file_hash} already exists in IPFS")
                except Exception:
                    logger.info(f"New file {file_hash} uploaded to IPFS")

        # Store metadata to IPFS
        metadata['timestamp'] = int(time.time())
        metadata['user_id'] = user_id
        if file_hash:
            metadata['file_hash'] = file_hash

        metadata_ipfs_result = store_json_to_ipfs(metadata)
        metadata_hash = metadata_ipfs_result

        # Store hash on Ethereum
        latest_block = w3.eth.get_block('latest')
        gas_price = w3.to_wei('20', 'gwei')  # Increased for faster mining
        nonce = w3.eth.get_transaction_count(SENDER_ADDRESS)

        # Create transaction with IPFS hash
        tx = {
            'to': '0x0000000000000000000000000000000000000000',
            'value': 0,
            'gas': 60000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'data': '0x' + metadata_hash.encode().hex(),
            'chainId': w3.eth.chain_id
        }

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for transaction to be mined
        receipt = wait_for_transaction(tx_hash)

        response = {
            "message": "Data stored successfully",
            "metadata_hash": metadata_hash,
            "ethereum_tx_hash": tx_hash.hex(),
            "block_number": receipt['blockNumber'],
            "metadata": metadata
        }

        if file_hash:
            response["file_hash"] = file_hash
            # Add information about whether this is a duplicate file
            try:
                ipfs_client.cat(file_hash)
                response["is_duplicate_file"] = True
            except Exception:
                response["is_duplicate_file"] = False

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in submit_data: {str(e)}")
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
            metadata_json = ipfs_client.cat(ipfs_hash)
            metadata = json.loads(metadata_json)
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
                file_data = ipfs_client.cat(metadata['file_hash'])
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
        # Find the transaction in the blockchain
        blockchain_data = get_metadata_from_blockchain(ipfs_hash)
        if not blockchain_data:
            return jsonify({"error": "Hash not found in blockchain"}), 404

        # Get metadata from IPFS
        try:
            metadata_json = ipfs_client.cat(ipfs_hash)
            metadata = json.loads(metadata_json)
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

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', debug=True)
