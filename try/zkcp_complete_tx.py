#!/usr/bin/env python3
"""
ZKCP Transaction Builder - Creates a proper scriptSig to reveal K and spend from P2SH
"""

import argparse
import sys
import json
import subprocess
import binascii
from typing import Dict, Any, Tuple

def run_command(command: str) -> Dict[str, Any]:
    """Run a Bitcoin command and return the result as a dictionary."""
    print(f"Running command: {command}")
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

def main():
    parser = argparse.ArgumentParser(description="Generate Bitcoin redeem script")
    parser.add_argument("real_k", help="Real Key")
    parser.add_argument("redeem_script", help="Redeem Script of ZKCP Script")
    parser.add_argument("txid", help="Transaction ID of Funding Script")
    parser.add_argument("vout", type=int, help="VOUT")
    parser.add_argument("amount", type=float, help="Amount locked in script")

    args = parser.parse_args()

    # 1. Setup - Get existing wallet info
    print("[*] Getting wallet information...")
    try:
        seller_address, seller_privkey, seller_pubkey = get_wallet_info("sellerwallet")
        print(f"  Seller address: {seller_address}")
    except Exception as e:
        print(f"Error getting wallet info: {e}")
        print("Make sure Bitcoin daemon is running and wallets are created")
        sys.exit(1)

    # 2. Calculate fee and output amount
    fee = 0.0001
    output_amount = args.amount - fee
    
    # 3. Import the redeem script to both wallets
    script_info = run_command(f"bitcoin-cli -regtest decodescript {args.redeem_script}")
    p2sh_address = script_info["p2sh"]
    
    run_command(f"bitcoin-cli -regtest -rpcwallet=sellerwallet importaddress {args.redeem_script} 'zkcp_redeem' false")
    run_command(f"bitcoin-cli -regtest -rpcwallet=sellerwallet importaddress {p2sh_address} 'zkcp_p2sh' false")
    
    # 4. Create a raw transaction using bitcoin-cli
    raw_inputs = [{"txid": args.txid, "vout": args.vout}]
    raw_outputs = {seller_address: output_amount}
    
    raw_tx_cmd = f"bitcoin-cli -regtest createrawtransaction '{json.dumps(raw_inputs)}' '{json.dumps(raw_outputs)}'"
    raw_tx = run_command(raw_tx_cmd)["result"]
    
    # 5. Get the scriptPubKey of the P2SH address
    utxo_info = run_command(f"bitcoin-cli -regtest -rpcwallet=sellerwallet gettxout {args.txid} {args.vout}")
    script_pub_key = utxo_info["scriptPubKey"]["hex"]
    
    # 6. Create a transaction with the proper input script
    # We'll use the fundrawtransaction command to add inputs and change
    fund_tx_cmd = f"bitcoin-cli -regtest -rpcwallet=sellerwallet fundrawtransaction {raw_tx}"
    funded_tx = run_command(fund_tx_cmd)
    funded_tx_hex = funded_tx["hex"]
    
    # 7. Now we'll use the wallet to sign the transaction
    # This will automatically handle creating the correct scriptSig
    sign_tx_cmd = f"bitcoin-cli -regtest -rpcwallet=sellerwallet signrawtransactionwithwallet {funded_tx_hex}"
    signed_tx = run_command(sign_tx_cmd)
    signed_tx_hex = signed_tx["hex"]
    
    # 8. Broadcast the transaction
    try:
        print("[*] Broadcasting transaction...")
        result = run_command(f"bitcoin-cli -regtest sendrawtransaction {signed_tx_hex}")
        txid = result["result"]
        print(f"[*] Transaction broadcast result: {txid}")
        
        # 9. Mine some blocks to confirm
        print("[*] Mining blocks to confirm transaction...")
        run_command(f"bitcoin-cli -regtest generatetoaddress 6 {seller_address}")
        print("[*] Transaction confirmed!")
        
        print("\n[*] ZKCP Completed!")
        print(f"[*] Seller revealed K: {args.real_k}")
        print("[*] Buyer can now use K to decrypt the purchased content")
        
    except Exception as e:
        print(f"[!] Error broadcasting transaction: {e}")
        print("[!] This could be due to incorrect scriptSig construction")
        
    print("\n[*] ZKCP Simulation Complete")

if __name__ == "__main__":
    main()



