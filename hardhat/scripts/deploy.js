const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function waitForNode(maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const provider = hre.ethers.provider;
      await provider.getNetwork();
      console.log("Connected to Hardhat node");
      return true;
    } catch (error) {
      console.log(`Waiting for Hardhat node... Attempt ${i + 1}/${maxAttempts}`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  throw new Error("Failed to connect to Hardhat node after maximum attempts");
}

async function main() {
  // Wait for node to be ready
  await waitForNode();

  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);

  const DNetToken = await hre.ethers.getContractFactory("DNetToken");
  const dnetToken = await DNetToken.deploy();
  await dnetToken.deployed();

  console.log("DNetToken deployed to:", dnetToken.address);

  // Save the contract address to a file
  const contractInfo = {
    address: dnetToken.address,
    deployer: deployer.address,
    network: hre.network.name,
    timestamp: new Date().toISOString()
  };

  const outputPath = path.join("/app/data/contract-address.json");
  fs.writeFileSync(outputPath, JSON.stringify(contractInfo, null, 2));
  console.log("Contract address saved to:", outputPath);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });



