#!/bin/bash
set -e

echo -e "[*] ZKCP Bitcoin Regtest Simulation\n"
echo -e "======= ZKCP FLOW OVERVIEW =======\n"
echo "1. Seller creates content and encrypts it with key K"
echo "2. Seller creates hash Y of K (Y = SHA256(K))"
echo "3. Seller creates zero-knowledge proof that encrypted content is valid"
echo "4. Buyer verifies proof and creates P2SH script with hash Y"
echo "5. Buyer funds P2SH (locks BTC)"
echo "6. Seller reveals K and claims payment"
echo "7. Buyer uses K to decrypt content"
echo -e "\n===============================\n"

# 1. Start Bitcoin Daemon
echo "[*] Starting Bitcoin Daemon..."
bitcoind -regtest -fallbackfee=0.0001 -daemon -deprecatedrpc=create_bdb
sleep 3

# 2. Create wallets
echo "[*] Creating wallets..."
bitcoin-cli -regtest createwallet "sellerwallet" false false "" false false > /dev/null 2>&1
bitcoin-cli -regtest createwallet "buyerwallet" false false "" false false > /dev/null 2>&1
echo "  ✓ Wallets created"

# 3. Get new addresses
seller_address=$(bitcoin-cli -regtest -rpcwallet=sellerwallet getnewaddress) 
buyer_address=$(bitcoin-cli -regtest -rpcwallet=buyerwallet getnewaddress)
echo "[*] Seller address: $seller_address"
echo "[*] Buyer address: $buyer_address"

# 4. Fund the wallets
echo "[*] Mining blocks to fund wallets..."
bitcoin-cli -regtest generatetoaddress 101 $buyer_address > /dev/null 2>&1
bitcoin-cli -regtest generatetoaddress 101 $seller_address > /dev/null 2>&1
echo "  ✓ Wallets funded"

# 5. Get private keys
seller_privkey=$(bitcoin-cli -regtest -rpcwallet=sellerwallet dumpprivkey $seller_address)
buyer_privkey=$(bitcoin-cli -regtest -rpcwallet=buyerwallet dumpprivkey $buyer_address)

# 6. Get public keys
seller_pubkey=$(bitcoin-cli -regtest -rpcwallet=sellerwallet getaddressinfo $seller_address | jq -r .pubkey)
buyer_pubkey=$(bitcoin-cli -regtest -rpcwallet=buyerwallet getaddressinfo $buyer_address | jq -r .pubkey)
echo "[*] Public keys obtained"

# 7. ZKCP Setup - Seller creates content and encrypts it
echo -e "\n====== ZKCP SETUP PHASE ======\n"
echo "[*] 1. Seller creates valuable content (simulated)"
echo "[*] 2. Seller encrypts content with key K"

# Simulate encryption key (K) and encrypted content
# In a real implementation, this would be the actual encryption key
REAL_K="2558e68d5a"
ENCRYPTED_CONTENT="This is encrypted content that would be decrypted with K"

# Generate hash Y of K (this would be sent to buyer)
# In a real implementation, this would be the actual hash of K
HASH_K="5ca24005b740717ba4f3f6bc48a230700e68c2a4b11ecedb96f169f4efaf1f21"

echo "[*] 3. Seller creates hash Y = SHA256(K)"
echo "   K = $REAL_K"
echo "   Y = $HASH_K"

# Create timelock (simulated proof verification would happen here)
BLOCK_HEIGHT=$(bitcoin-cli -regtest getblockcount)
LOCKTIME=$((BLOCK_HEIGHT + 100))
echo "[*] 4. Locktime set to block $LOCKTIME for refund path"

# 8. ZKCP Payment Setup - Buyer creates and funds P2SH script
echo -e "\n====== PAYMENT SETUP PHASE ======\n"
echo "[*] 1. Buyer verifies seller's proof (simulated)"
echo "[*] 2. Buyer creates P2SH script with hash Y and timelock"

# Generate redeem script using Python script
REDEEM_SCRIPT=$(python3 asm.py "$HASH_K" "$seller_pubkey" "$LOCKTIME" "$buyer_pubkey")
echo "[*] Redeem Script: $REDEEM_SCRIPT"

# Decode script to get P2SH address
SCRIPT_INFO=$(bitcoin-cli -regtest decodescript "$REDEEM_SCRIPT")
P2SH_ADDRESS=$(echo "$SCRIPT_INFO" | jq -r .p2sh)
echo "[*] P2SH Address: $P2SH_ADDRESS"

# 9. Buyer funds P2SH script (locks BTC in the script)
echo "[*] 3. Buyer funds P2SH address (locks 1 BTC)"
TXID=$(bitcoin-cli -regtest -rpcwallet=buyerwallet sendtoaddress "$P2SH_ADDRESS" 1.0)
echo "   Transaction ID: $TXID"

# 10. Import script to wallets
echo "[*] 4. Importing scripts to wallets..."
bitcoin-cli -regtest -rpcwallet=buyerwallet importaddress "$REDEEM_SCRIPT" "zkcp_redeem" false > /dev/null 2>&1
bitcoin-cli -regtest -rpcwallet=buyerwallet importaddress "$P2SH_ADDRESS" "zkcp_p2sh" false > /dev/null 2>&1
bitcoin-cli -regtest -rpcwallet=sellerwallet importaddress "$REDEEM_SCRIPT" "zkcp_redeem" false > /dev/null 2>&1
bitcoin-cli -regtest -rpcwallet=sellerwallet importaddress "$P2SH_ADDRESS" "zkcp_p2sh" false > /dev/null 2>&1
echo "   ✓ Scripts imported to both wallets"

# 11. Mine blocks to confirm transaction
echo "[*] 5. Mining blocks to confirm funding transaction..."
bitcoin-cli -regtest generatetoaddress 6 $buyer_address > /dev/null 2>&1
echo "   ✓ Funding transaction confirmed"

# 12. Seller verifies UTXO is available to spend
echo -e "\n====== PAYMENT EXECUTION PHASE ======\n"
echo "[*] 1. Seller verifies P2SH is properly funded"
UNSPENT=$(bitcoin-cli -regtest -rpcwallet=sellerwallet listunspent 0 9999999 "[\"$P2SH_ADDRESS\"]")
TXID=$(echo "$UNSPENT" | jq -r '.[0].txid')
VOUT=$(echo "$UNSPENT" | jq -r '.[0].vout')
AMOUNT=$(echo "$UNSPENT" | jq -r '.[0].amount')
SCRIPT_PUBKEY=$(echo "$UNSPENT" | jq -r '.[0].scriptPubKey')
echo "   UTXO TXID: $TXID"
echo "   Amount: $AMOUNT BTC"

# 13. Seller creates transaction to claim funds
echo "[*] 2. Seller creates transaction to claim funds"
AMOUNT_TO_SEND=0.9995  # leaving some for fees
RAW_TX=$(bitcoin-cli -regtest createrawtransaction \
"[{\"txid\":\"$TXID\",\"vout\":$VOUT}]" \
"{\"$seller_address\":$AMOUNT_TO_SEND}")
echo "   Raw transaction created"

# 14. Seller reveals K by including it in the script
echo "[*] 3. Seller reveals K to claim payment"
echo "   This would normally be part of the scriptSig to satisfy the P2SH script"
echo "   Revealing K = $REAL_K"

# In a real implementation, we would create the scriptSig with:
# 1. The actual K value (which would hash to Y)
# 2. The seller's signature
# But Bitcoin CLI doesn't give us a direct way to create custom scriptSigs

# Simulate the special scriptSig creation by using the debug interpreter

# 15. Create and sign the transaction - Simulating a proper scriptSig construction
echo "[*] 4. Creating spending transaction with K revealed"
echo "   NOTE: This script can't create the proper scriptSig in regtest mode"
echo "   In a real implementation, the scriptSig would include:"
echo "   - The actual K value ($REAL_K)"
echo "   - OP_TRUE to take the first branch of the If statement"
echo "   - The seller's signature"

# 16. Sign the transaction - this will fail because we can't properly create the scriptSig
echo "[*] 5. Attempting to sign transaction..."
SIGNED_TX=$(bitcoin-cli -regtest signrawtransactionwithkey \
"$RAW_TX" \
"[\"$seller_privkey\"]" \
"[{\"txid\":\"$TXID\",\"vout\":$VOUT,\"scriptPubKey\":\"$SCRIPT_PUBKEY\",\"redeemScript\":\"$REDEEM_SCRIPT\",\"amount\":$AMOUNT}]")

HEX=$(echo "$SIGNED_TX" | jq -r .hex)
COMPLETE=$(echo "$SIGNED_TX" | jq -r .complete)

echo "[*] Signing result:"
echo "   Complete: $COMPLETE"

# 17. Provide explanation of why it's incomplete
echo -e "\n====== ZKCP EXPLANATION ======\n"
echo "[!] The transaction signing is incomplete because:"
echo "   1. In a real ZKCP implementation, the scriptSig would contain:"
echo "      - The actual K value ($REAL_K)"
echo "      - A flag to take the first branch of the If-Else statement"
echo "      - The seller's signature"
echo ""
echo "   2. Bitcoin-cli doesn't provide a direct way to create this custom scriptSig"
echo "      in regtest mode without additional tooling"
echo ""
echo "   3. In a real ZKCP:"
echo "      - The buyer would create and fund the P2SH script (COMPLETED)"
echo "      - The seller would verify the script and funding (COMPLETED)"
echo "      - The seller would reveal K by spending from the script (SIMULATED)"
echo "      - The buyer would extract K from the blockchain transaction"
echo "      - The buyer would use K to decrypt the content"
echo ""
echo "[*] To complete the ZKCP in a real implementation:"
echo "   1. The seller would need specialized code to create the proper scriptSig"
echo "   2. The transaction would be broadcast with K revealed"
echo "   3. The buyer would extract K from the transaction on the blockchain"

echo -e "\n[*] ZKCP Simulation Complete"

