#/bin/bash
set -e

echo -e "[*] Starting Bitcoin Regtest Script...\n"

# 1. Start Bitcoin Daemon
bitcoind -regtest -fallbackfee=0.0001 -daemon -deprecatedrpc=create_bdb
sleep 3

# 2. Create wallets
bitcoin-cli -regtest createwallet "sellerwallet" false false "" false false > /dev/null 2>&1
bitcoin-cli -regtest createwallet "buyerwallet" false false "" false false > /dev/null 2>&1
echo "Seller wallet created!"
echo -e "Buyer wallet created!\n"

# 3. Get new addresses
seller_address=$(bitcoin-cli -regtest -rpcwallet=sellerwallet getnewaddress) 
buyer_address=$(bitcoin-cli -regtest -rpcwallet=buyerwallet getnewaddress)
echo "Seller address is $seller_address"
echo -e "Buyer address is $buyer_address\n"

# 4. Fund the wallets
bitcoin-cli -regtest generatetoaddress 101 $buyer_address > /dev/null 2>&1
bitcoin-cli -regtest generatetoaddress 101 $seller_address > /dev/null 2>&1

# 5. Load buyer wallet (optional as it's just created)
if ! bitcoin-cli -regtest listwallets | grep -q "buyerwallet"; then
  bitcoin-cli -regtest loadwallet buyerwallet > /dev/null 2>&1
  echo -e "Buyer wallet loaded!\n"
fi

# 6. Get private keys
seller_privkey=$(bitcoin-cli -regtest -rpcwallet=sellerwallet dumpprivkey $seller_address)
buyer_privkey=$(bitcoin-cli -regtest -rpcwallet=buyerwallet dumpprivkey $buyer_address)
echo "Private keys obtained!"

# 7. Get public keys
seller_pubkey=$(bitcoin-cli -regtest -rpcwallet=sellerwallet getaddressinfo $seller_address | jq -r .pubkey)
buyer_pubkey=$(bitcoin-cli -regtest -rpcwallet=buyerwallet getaddressinfo $buyer_address | jq -r .pubkey)
echo -e "Public keys obtained!\n"

# 8. Set encryption/hash/locktime
ENCRYPTED_K="2558e68d5a"
HASH_K="5ca24005b740717ba4f3f6bc48a230700e68c2a4b11ecedb96f169f4efaf1f21"
BLOCK_HEIGHT=$(bitcoin-cli -regtest getblockcount)
LOCKTIME=$((BLOCK_HEIGHT + 100))

echo "[*] Using Encrypted K: $ENCRYPTED_K"
echo "[*] Using Y: $HASH_K"
echo -e "[*] Using Locktime: $LOCKTIME\n"

# 9. Generate redeem script using Python script (asm.py must be available)
REDEEM_SCRIPT=$(python3 asm.py "$HASH_K" "$seller_pubkey" "$LOCKTIME" "$buyer_pubkey")
echo "[*] Redeem Script: $REDEEM_SCRIPT"

# 10. Decode script to get P2SH
P2SH_ADDRESS=$(bitcoin-cli -regtest decodescript "$REDEEM_SCRIPT" | jq -r .p2sh)
echo "[*] P2SH Address: $P2SH_ADDRESS"

# 11. Fund P2SH with 1 BTC
TXID=$(bitcoin-cli -regtest -rpcwallet=buyerwallet sendtoaddress "$P2SH_ADDRESS" 1.0)
echo -e "[*] Funded script, TXID: $TXID\n"

# 12. Import script to buyer's wallet
echo "Importing script to buyer's wallet..."
bitcoin-cli -regtest -rpcwallet=buyerwallet importaddress "$P2SH_ADDRESS" "label" false
sleep 1
echo -e "Script imported to the buyer's wallet!"

# 13 Import script to seller's wallet
echo "Importing script to seller's wallet..."
bitcoin-cli -regtest -rpcwallet=sellerwallet importaddress "$P2SH_ADDRESS" "label" false
sleep 1
echo -e "Script imported to the seller's wallet!\n"

# 14. List unspent for the script
echo "Checking list unspent for the script.."
UNSPENT=$(bitcoin-cli -regtest -rpcwallet=buyerwallet listunspent 0 9999999 "[\"$P2SH_ADDRESS\"]")
TXID=$(echo "$UNSPENT" | jq -r '.[0].txid')
VOUT=$(echo "$UNSPENT" | jq -r '.[0].vout')
echo -e "[*] UTXO TXID: $TXID"
echo -e "[*] VOUT: $VOUT\n"

# 14. Create raw transaction
# NEW_ADDR=$(bitcoin-cli -regtest -rpcwallet=buyerwallet getnewaddress)
echo "Creating a new raw transaction..."
AMOUNT=0.9995
RAW_TX=$(bitcoin-cli -regtest -rpcwallet=sellerwallet createrawtransaction \
"[{\"txid\":\"$TXID\",\"vout\":$VOUT}]" \
"{\"$seller_address\":$AMOUNT}")
echo -e "[*] Raw TX: $RAW_TX\n"

# 15. Sign raw transaction
SIGNED_TX=$(bitcoin-cli -regtest -rpcwallet=sellerwallet signrawtransactionwithkey \
"$RAW_TX" \
"[\"$seller_privkey\"]" \
"[{\"txid\":\"$TXID\",\"vout\":$VOUT,\"scriptPubKey\":\"$SCRIPT_PUBKEY\",\"redeemScript\":\"$REDEEM_SCRIPT\",\"amount\":1.0}]")

echo "[*] Signed TX: $SIGNED_TX"

echo "[*]Done."

