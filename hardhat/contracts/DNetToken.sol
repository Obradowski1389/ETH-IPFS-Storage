// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract DNetToken is ERC20, Ownable {
    // Event to emit when metadata is stored
    event MetadataStored(address indexed user, bytes32 indexed hash, uint256 timestamp);
    
    // Event to emit when fee is updated
    event FeeUpdated(uint256 oldFee, uint256 newFee);
    
    // Mapping to store metadata hashes
    mapping(bytes32 => bool) public storedHashes;
    
    // Fee for storing metadata (in tokens)
    uint256 public metadataStorageFee;
    
    constructor() ERC20("DNet Token", "DNET") {
        // Mint 1,000,000 tokens to the contract creator
        // Using 18 decimals (standard for ERC20)
        _mint(msg.sender, 1000000 * 10 ** decimals());
        
        // Set initial fee to 1 token
        metadataStorageFee = 1 * 10 ** decimals();
    }

    // No mint function: supply is fixed

    // Function to burn tokens
    function burn(uint256 amount) public {
        _burn(msg.sender, amount);
    }
    
    // Function to update the metadata storage fee
    function updateMetadataStorageFee(uint256 newFee) public {
        uint256 oldFee = metadataStorageFee;
        metadataStorageFee = newFee;
        emit FeeUpdated(oldFee, newFee);
    }
    
    // Function to store metadata hash (requires fee payment)
    function storeMetadataHash(bytes32 hash) public {
        // Check if hash is already stored
        require(!storedHashes[hash], "Hash already stored");
        
        // Transfer fee from user to contract
        _transfer(msg.sender, address(this), metadataStorageFee);
        
        // Store the hash
        storedHashes[hash] = true;
        
        // Emit event
        emit MetadataStored(msg.sender, hash, block.timestamp);
    }
    
    // Function to validate if a hash exists (free)
    function validateHash(bytes32 hash) public view returns (bool) {
        return storedHashes[hash];
    }
    
    // Function to withdraw collected fees
    function withdrawFees() public {
        uint256 balance = balanceOf(address(this));
        require(balance > 0, "No fees to withdraw");
        _transfer(address(this), msg.sender, balance);
    }
} 
