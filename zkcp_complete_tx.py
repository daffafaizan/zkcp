#!/usr/bin/env python3
"""
ZKCP Transaction Builder - Creates a proper scriptSig to reveal K and spend from P2SH
"""

import argparse
import sys
import json
import subprocess
from typing import Dict, Any, Tuple
from bitcoin.core import (
    x, b2x, lx, CMutableTransaction, 
    CMutableTxIn, CMutableTxOut, COutPoint, CScript
)
from bitcoin.core.script import (
    SignatureHash,
    SIGHASH_ALL
)
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress
import bitcoin.rpc

# Initialize Bitcoin Regtest connection
bitcoin.SelectParams('regtest')
rpc_connection = bitcoin.rpc.Proxy("http://localhost:18443")

def run_command(command: str) -> Dict[str, Any]:
    """Run a Bitcoin command and return the result as a dictionary."""
    result = subprocess.run(
        command, shell=True, text=True, capture_output=True
    )
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"result": result.stdout.strip()}

def get_wallet_info(wallet_name: str) -> Tuple[str, str, str]:
    """Get address, private key, and public key from wallet."""
    address = run_command(f"bitcoin-cli -regtest -rpcwallet={wallet_name} getnewaddress")["result"]
    privkey = run_command(f"bitcoin-cli -regtest -rpcwallet={wallet_name} dumpprivkey {address}")["result"]
    pubkey = run_command(f"bitcoin-cli -regtest -rpcwallet={wallet_name} getaddressinfo {address}")["pubkey"]
    return address, privkey, pubkey

def get_p2sh_utxo(p2sh_address: str) -> Dict[str, Any]:
    """Find an unspent output for the P2SH address."""
    unspent = run_command(f'bitcoin-cli -regtest listunspent 0 9999999 "[\"{p2sh_address}\"]"')
    if not unspent or len(unspent) == 0:
        print(f"No unspent outputs found for {p2sh_address}")
        sys.exit(1)
    return unspent[0]

def main():
    parser = argparse.ArgumentParser(description="Generate Bitcoin redeem script")
    parser.add_argument("real_k", help="Real Key")
    parser.add_argument("locktime", type=int, help="Lock time")
    parser.add_argument("redeem_script", help="Redeem Script of ZKCP Script")
    parser.add_argument("txid", help="Transaction ID of Funding Script")
    parser.add_argument("vout", type=int, help="VOUT")
    parser.add_argument("amount", type=float, help="Amount locked in script")

    args = parser.parse_args()

    # 1. Setup - Get existing wallet info or create new ones
    print("[*] Getting wallet information...")
    try:
        seller_address, seller_privkey, _ = get_wallet_info("sellerwallet")
        buyer_address, _, _ = get_wallet_info("buyerwallet")
        print(f"  Seller address: {seller_address}")
        print(f"  Buyer address: {buyer_address}")
    except Exception as e:
        print(f"Error getting wallet info: {e}")
        print("Make sure Bitcoin daemon is running and wallets are created")
        sys.exit(1)

    # 2. Create transaction spending from P2SH to seller's address
    fee = 0.0001
    output_amount = args.amount - fee

    # 2.1 Other Setups
    seller_key = CBitcoinSecret(seller_privkey)
    seller_pubkey = seller_key.pub
    seller_address = P2PKHBitcoinAddress.from_pubkey(seller_pubkey)
    script_pub_key = seller_address.to_scriptPubKey()
    redeem_script = CScript(x(args.redeem_script))
    
    # 3. Create the raw transaction
    txin = CMutableTxIn(COutPoint(lx(args.txid), args.vout))
    txout = CMutableTxOut(int(output_amount * 100000000), script_pub_key)
    tx = CMutableTransaction([txin], [txout])

    tx.nLockTime = args.locktime
    txin.nSequence = 0xfffffffe

    # 4. Create the signature hash for signing
    sighash = SignatureHash(redeem_script, tx, 0, SIGHASH_ALL)
    
    # 8. Sign with seller's private key
    # seller_key = CBitcoinSecret(seller_privkey)
    sig = seller_key.sign(sighash) + bytes([SIGHASH_ALL])
    
    # 9. Create the proper scriptSig that reveals K and takes the IF branch
    # The scriptSig structure for the IF branch is:
    # <signature> <K> <TRUE> <redeemScript>
    script_sig = CScript([
        sig,           # Seller's signature
        args.real_k.encode(),        # Reveal K (the decryption key)
        1,             # TRUE to take the IF branch
        redeem_script  # The complete redeem script
    ])
    
    # 10. Set the scriptSig in the transaction
    tx.vin[0].scriptSig = script_sig
    
    # 11. Convert transaction to hex
    tx_hex = b2x(tx.serialize())
    print(f"[*] Complete transaction hex: {tx_hex}")
    
    # 12. Broadcast the transaction
    try:
        print("[*] Broadcasting transaction...")
        result = run_command(f"bitcoin-cli -regtest sendrawtransaction {tx_hex}")
        txid = result["result"] if "result" in result else result["error"]
        print(f"[*] Transaction broadcast result: {txid}")
        
        # 13. Mine some blocks to confirm
        print("[*] Mining blocks to confirm transaction...")
        run_command(f"bitcoin-cli -regtest generatetoaddress 6 {seller_address}")
        print("[*] Transaction confirmed!")
        
        # 14. Extract K from transaction for buyer
        print("\n[*] ZKCP Completed!")
        print(f"[*] Seller revealed K: {args.real_k.decode()}")
        print("[*] Buyer can now use K to decrypt the purchased content")
        
    except Exception as e:
        print(f"[!] Error broadcasting transaction: {e}")
        print("[!] This could be due to incorrect scriptSig construction")
        
    print("\n[*] ZKCP Simulation Complete")

if __name__ == "__main__":
    main()


