# Ethereum and IPFS File Storage Demo

This project demonstrates a decentralized file storage system using Ethereum blockchain and IPFS. It provides a Flask-based API for storing, retrieving, and verifying files with their metadata.

## Features

- Store files and metadata on IPFS
- Record file hashes on Ethereum blockchain
- Verify file integrity and existence
- Health check endpoint for system status
- Immutable data storage (blockchain-based)

## Setup

1. **Local Development**
   ```bash
   # Start services
   docker-compose up -d

   # View logs
   docker-compose logs -f

   # Stop services (not now...)
   docker-compose down
   ```

2. **Set up the environment**
   ```bash
   # Generate .env file with Ganache account information
   python3 get_ganache_account.py
   ```
3. **Start the services**
   ```bash
   docker-compose up -d
   ```
4. **Verify the setup**
   ```bash
   # Check account balance
   python3 check_balance.py
   ```

## Account Management

The system uses a deterministic Ganache account for initial setup. The account information is automatically configured in the `.env` file when you run `get_ganache_account.py`.

### Checking Account Balance
```bash
python3 check_balance.py
```
This script will show:
- Account address
- Balance in ETH and Wei
- Current gas price
- Estimated transaction cost

## API Endpoints

### Submit Data
```bash
curl -X POST http://localhost:5000/submit \
  -F "file=@your_file.txt" \
  -F "user_id=test123" \
  -F "metadata={\"description\":\"Test file\"}"
```

### Retrieve Data
```bash
curl http://localhost:5000/retrieve/QmYourHash
```

### Verify Data
```bash
curl http://localhost:5000/verify/QmYourHash
```

### Health Check
```bash
curl http://localhost:5000/health
```

## System Components

1. **Flask Application**
   - REST API for file operations
   - Handles file uploads and metadata
   - Manages blockchain interactions

2. **Ethereum Node (Ganache)**
   - Local blockchain for testing
   - Stores file hashes
   - Provides transaction history
   - Uses deterministic account generation

3. **IPFS Node**
   - Decentralized file storage
   - Content-addressed storage
   - Metadata storage
   - File deduplication

## Data Storage Architecture

### File Storage
- Files are stored on IPFS
- Each file gets a unique content hash
- Duplicate files are automatically deduplicated
- Original files are preserved

### Metadata Storage
- Metadata is stored on IPFS
- Includes file information and user data
- Each submission creates new metadata
- No modifications to existing data

### Blockchain Storage
- IPFS hashes are recorded on Ethereum
- Each submission creates a new transaction
- Complete audit trail is maintained
- Data is immutable once recorded

## Recent Improvements

1. **Blockchain-based Metadata Storage**
   - Metadata now stored on blockchain
   - Improved verification system
   - Better data persistence
   - Enhanced security

2. **IPFS Integration**
   - Improved IPFS client
   - Better error handling
   - File deduplication
   - Efficient storage

3. **Security Enhancements**
   - Deterministic Ganache configuration
   - Secure private key handling
   - Improved error handling
   - Better logging



## Production Deployment

For production deployment:
1. Use a production Ethereum node
2. Configure proper IPFS node
3. Set up proper security measures
4. Use environment variables for configuration
5. Implement proper error handling
6. Set up monitoring and logging

## Environment Variables

- `ETHEREUM_NODE_URL`: Ethereum node URL (default: http://localhost:8545)
- `IPFS_NODE_URL`: IPFS node URL (default: /dns4/ipfs/tcp/5001/http)
- `PRIVATE_KEY`: Ethereum account private key (set by get_ganache_account.py)

## Error Handling

The system includes comprehensive error handling:
- Invalid file uploads
- Network connectivity issues
- Blockchain transaction failures
- IPFS storage errors
- Insufficient funds
- Invalid account credentials

## Logging

- Application logs available via Docker
- Transaction logging
- Error tracking
- System health monitoring 