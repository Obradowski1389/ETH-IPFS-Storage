# DNET Infrastructure

This project implements a decentralized network infrastructure with IPFS storage and blockchain integration, featuring DNET - a custom Ethereum-based cryptocurrency token.

## Key Features

- **DNET Token**: A custom ERC-20 token built on Ethereum blockchain
  - Initial supply of 10 DNET tokens for new users
  - Reward system for content submission
  - Token burning mechanism
  - Real-time balance tracking
  - Transaction history

- **Decentralized Storage**
  - IPFS integration for metadata and file storage
  - Content verification through blockchain
  - Immutable record of all submissions

- **Smart Contract Integration**
  - Automated token distribution
  - Secure transaction handling
  - Blockchain-based content validation

## Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Git

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd DNet-Infra
```

### 2. Create and Activate Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root with the following variables:

```env
# Required for test_operations.py and transfer_to_server.py
PRIVATE_KEY=your_private_key_here  # Private key for the server wallet
GANACHE_ACCOUNT_0_ADDRESS=0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
GANACHE_ACCOUNT_0_PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
INITIAL_DNET_AMOUNT=10
REWARD_DNET_AMOUNT=1
```

### 5. Start Infrastructure Services
```bash
# Start IPFS, MySQL, and other required services
docker-compose up -d
```

### 6. Initialize Server Wallet
Before running any tests, you need to transfer initial DNET tokens to the server wallet:

```bash
# Run the transfer script
python transfer_to_server.py
```

This script will:
- Create a server wallet if it doesn't exist
- Transfer initial DNET tokens to the server wallet
- Verify the transfer was successful

## DNET Token Features

### Token Distribution
- New users receive 10 DNET tokens upon registration
- Content submission rewards of 1 DNET per submission
- Token burning mechanism for supply control

### Smart Contract Integration
- Built on Ethereum's ERC-20 standard
- Secure token transfers with gas optimization
- Transaction history tracking
- Real-time balance monitoring

### Security Features
- Private key hashing for user authentication
- Blockchain-verified transactions
- Immutable transaction records
- Secure token burning mechanism

## Testing the Infrastructure

The project includes a comprehensive test script that demonstrates all major functionalities.

### Running Tests

```bash
python test_operations.py
```

The test script will execute the following operations in sequence:

1. **User Registration**
   - Register a new user
   - Receive initial DNET tokens

2. **Metadata Operations**
   - Submit metadata to IPFS
   - Check transaction status
   - Verify metadata validity
   - Retrieve metadata

3. **File Operations**
   - Submit a file to IPFS
   - Check transaction status
   - Verify file validity
   - Retrieve the file

4. **Balance and Supply Operations**
   - Check user balance
   - Get total DNET supply
   - Burn tokens
   - Check server transactions
   - Check server balance

## API Endpoints

The infrastructure provides the following main endpoints:

- `/register` - Register a new user
- `/submit` - Submit metadata and files
- `/balance/<wallet_address>` - Check wallet balance
- `/transactions/<wallet_address>` - View wallet transactions
- `/validity/<ipfs_hash>` - Verify IPFS content validity
- `/metadata/<ipfs_hash>` - Retrieve metadata
- `/file/<ipfs_hash>` - Retrieve file
- `/total_supply` - Get total DNET supply
- `/burn` - Burn DNET tokens

## Infrastructure Services

The project uses Docker Compose to manage the following services:

- **IPFS Node**: Handles decentralized file storage
- **MySQL**: Stores user
- **Hardhat Node**: Local Ethereum development network
- **DNET Token Contract**: Manages token operations

All services are configured through `docker-compose.yml` and don't require additional environment setup.

## Future Work

### Enhanced Security
- **End-to-End Encryption**
  - Implement asymmetric encryption for sensitive data
  - Replace private key hashing with encrypted storage
  - Add data encryption for IPFS content

- **Request Signing**
  - Implement EIP-712 typed data signing
  - Replace raw private key transmission with signed messages
  - Add request timestamp and nonce for replay protection

### Web3 Integration
- **MetaMask Integration**
  - Add MetaMask wallet connection
  - Implement wallet-based authentication
  - Support multiple wallet connections per user
  - Add wallet switching capabilities

- **Smart Contract Improvements**
  - Add role-based access control (RBAC)
  - Implement token vesting schedules
  - Add governance features for token management
  - Support token staking mechanisms

### User Experience
- **Web Interface**
  - Develop a React-based frontend
  - Add real-time transaction monitoring
  - Implement wallet management dashboard
  - Add token transfer history visualization

- **API Enhancements**
  - Add WebSocket support for real-time updates
  - Implement rate limiting and API key management
  - Add batch operations for multiple transactions
  - Support pagination for large data sets

### Infrastructure
- **Scalability Improvements**
  - Implement database sharding
  - Add caching layer for frequently accessed data
  - Support multiple IPFS nodes
  - Add load balancing for API endpoints

- **Monitoring and Analytics**
  - Add comprehensive logging system
  - Implement performance metrics collection
  - Add transaction analytics dashboard
  - Support custom alerting system

