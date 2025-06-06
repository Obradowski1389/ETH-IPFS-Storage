const hre = require("hardhat");
const ethers = hre.ethers;
const crypto = require("crypto");

// Helper: calculate SHA-256 hash of JSON metadata
function calculateMetadataHash(metadata) {
    const jsonString = JSON.stringify(metadata);
    return '0x' + crypto.createHash('sha256').update(jsonString).digest('hex');
}

async function main() {
    // Replace with your deployed contract address
    const contractAddress = "YOUR_CONTRACT_ADDRESS_HERE";

    // Example metadata
    const metadata = {
        title: "Example Document",
        description: "This is a test document",
        timestamp: Date.now(),
        author: "John Doe"
    };

    // Calculate hash
    const hash = calculateMetadataHash(metadata);
    console.log("Metadata hash:", hash);

    // Get signer (first account by default)
    const [signer] = await ethers.getSigners();

    // Attach to deployed contract
    const DNetToken = await ethers.getContractFactory("DNetToken");
    const dnetToken = await DNetToken.attach(contractAddress);

    // Store the hash (requires fee payment)
    try {
        const tx = await dnetToken.connect(signer).storeMetadataHash(hash);
        await tx.wait();
        console.log("Metadata hash stored successfully!");
    } catch (error) {
        console.error("Error storing hash:", error.message);
    }

    // Validate the hash (free)
    try {
        const isValid = await dnetToken.validateHash(hash);
        console.log("Hash validation result:", isValid);
    } catch (error) {
        console.error("Error validating hash:", error.message);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });