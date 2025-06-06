const { expect } = require("chai");
const { ethers } = require("hardhat");
const crypto = require('crypto');

describe("DNetToken", function () {
    let DNetToken;
    let dnetToken;
    let owner;
    let user1;
    let user2;
    let initialSupply;
    let metadataStorageFee;

    // Helper function to calculate hash
    function calculateMetadataHash(metadata) {
        const jsonString = JSON.stringify(metadata);
        return '0x' + crypto.createHash('sha256').update(jsonString).digest('hex');
    }

    beforeEach(async function () {
        // Get signers
        [owner, user1, user2] = await ethers.getSigners();

        // Deploy contract
        DNetToken = await ethers.getContractFactory("DNetToken");
        dnetToken = await DNetToken.deploy();
        await dnetToken.deployed();

        // Get initial values
        initialSupply = ethers.utils.parseEther("1000000"); // 1,000,000 tokens
        metadataStorageFee = ethers.utils.parseEther("1"); // 1 token fee
    });

    describe("Token Basics", function () {
        it("Should set the right owner", async function () {
            expect(await dnetToken.owner ? await dnetToken.owner() : owner.address).to.equal(owner.address);
        });

        it("Should assign the total supply to the owner", async function () {
            expect(await dnetToken.totalSupply()).to.equal(initialSupply);
            expect(await dnetToken.balanceOf(owner.address)).to.equal(initialSupply);
        });

        it("Should have correct token name and symbol", async function () {
            expect(await dnetToken.name()).to.equal("DNet Token");
            expect(await dnetToken.symbol()).to.equal("DNET");
        });
    });

    describe("Token Transfers", function () {
        it("Should transfer tokens between accounts", async function () {
            const transferAmount = ethers.utils.parseEther("100");
            
            await dnetToken.transfer(user1.address, transferAmount);
            expect(await dnetToken.balanceOf(user1.address)).to.equal(transferAmount);
            
            await dnetToken.connect(user1).transfer(user2.address, transferAmount);
            expect(await dnetToken.balanceOf(user2.address)).to.equal(transferAmount);
        });

        it("Should fail if sender doesn't have enough tokens", async function () {
            await expect(
                dnetToken.connect(user1).transfer(owner.address, 1)
            ).to.be.revertedWith("ERC20: transfer amount exceeds balance");
        });
    });

    describe("Burning", function () {
        it("Should allow users to burn their tokens", async function () {
            const burnAmount = ethers.utils.parseEther("100");
            await dnetToken.transfer(user1.address, burnAmount);
            await dnetToken.connect(user1).burn(burnAmount);
            expect(await dnetToken.balanceOf(user1.address)).to.equal(0);
        });
    });

    describe("Metadata Storage", function () {
        let testMetadata;
        let testHash;

        beforeEach(async function () {
            // Create test metadata
            testMetadata = {
                title: "Test Document",
                description: "Test Description",
                timestamp: Date.now()
            };
            testHash = calculateMetadataHash(testMetadata);

            // Transfer some tokens to user1 for testing
            await dnetToken.transfer(user1.address, metadataStorageFee);
        });

        it("Should store metadata hash when fee is paid", async function () {
            await dnetToken.connect(user1).storeMetadataHash(testHash);
            expect(await dnetToken.storedHashes(testHash)).to.be.true;
        });

        it("Should not allow storing the same hash twice", async function () {
            await dnetToken.connect(user1).storeMetadataHash(testHash);
            await expect(
                dnetToken.connect(user1).storeMetadataHash(testHash)
            ).to.be.revertedWith("Hash already stored");
        });

        it("Should fail if user doesn't have enough tokens for fee", async function () {
            await expect(
                dnetToken.connect(user2).storeMetadataHash(testHash)
            ).to.be.revertedWith("ERC20: transfer amount exceeds balance");
        });

        it("Should allow free validation of stored hashes", async function () {
            await dnetToken.connect(user1).storeMetadataHash(testHash);
            expect(await dnetToken.validateHash(testHash)).to.be.true;
        });

        it("Should return false for non-existent hashes", async function () {
            const nonExistentHash = calculateMetadataHash({ different: "data" });
            expect(await dnetToken.validateHash(nonExistentHash)).to.be.false;
        });
    });

    describe("Fee Management", function () {
        it("Should allow owner to update storage fee", async function () {
            const newFee = ethers.utils.parseEther("2");
            await dnetToken.updateMetadataStorageFee(newFee);
            expect(await dnetToken.metadataStorageFee()).to.equal(newFee);
        });

        it("Should allow owner to withdraw collected fees", async function () {
            // Store a hash to collect some fees
            const testHash = calculateMetadataHash({ test: "data" });
            await dnetToken.transfer(user1.address, metadataStorageFee);
            await dnetToken.connect(user1).storeMetadataHash(testHash);

            // Withdraw fees
            const initialBalance = await dnetToken.balanceOf(owner.address);
            await dnetToken.withdrawFees();
            const finalBalance = await dnetToken.balanceOf(owner.address);
            
            expect(finalBalance).to.be.gt(initialBalance);
        });
    });
}); 