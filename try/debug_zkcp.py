#!/usr/bin/env python3
"""
Debug helper for ZKCP transactions
This script helps analyze and debug Bitcoin transactions related to ZKCP
"""

import sys
import json
import subprocess
import binascii
from bitcoin.core import (
    x, b2x, lx, CTransaction
)

def run_command(command):
    """Run a Bitcoin command and return the result."""
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

def decode_transaction(txid):
    """Decode and display a transaction in detail."""
    tx_hex = run_command(f"bitcoin-cli -regtest getrawtransaction {txid}")["result"]
    tx_details = run_command(f"bitcoin-cli -regtest decoderawtransaction {tx_hex}")
    
    print(f"\n=== Transaction Details for {txid} ===")
    print(f"Version: {tx_details['version']}")
    print(f"Locktime: {tx_details['locktime']}")
    
    print("\nInputs:")
    for i, inp in enumerate(tx_details["vin"]):
        print(f"  Input #{i}:")
        print(f"    Previous TXID: {inp.get('txid', 'N/A')}")
        print(f"    Previous VOUT: {inp.get('vout', 'N/A')}")
        print(f"    Sequence: {inp.get('sequence', 'N/A')}")
        
        if "scriptSig" in inp:
            print(f"    ScriptSig ASM: {inp['scriptSig'].get('asm', 'N/A')}")
            print(f"    ScriptSig Hex: {inp['scriptSig'].get('hex', 'N/A')}")
        else:
            print("    ScriptSig: None")
            
    print("\nOutputs:")
    for i, out in enumerate(tx_details["vout"]):
        print(f"  Output #{i}:")
        print(f"    Value: {out['value']} BTC")
        print(f"    ScriptPubKey Type: {out['scriptPubKey'].get('type', 'N/A')}")
        print(f"    ScriptPubKey ASM: {out['scriptPubKey'].get('asm', 'N/A')}")
        print(f"    ScriptPubKey Hex: {out['scriptPubKey'].get('hex', 'N/A')}")
        if "addresses" in out["scriptPubKey"]:
            print(f"    Addresses: {', '.join(out['scriptPubKey']['addresses'])}")

def decode_redeem_script(script_hex):
    """Decode and display a redeem script."""
    try:
        script_details = run_command(f"bitcoin-cli -regtest decodescript {script_hex}")
        
        print(f"\n=== Redeem Script Details ===")
        print(f"ASM: {script_details.get('asm', 'N/A')}")
        print(f"Type: {script_details.get('type', 'N/A')}")
        print(f"P2SH Address: {script_details.get('p2sh', 'N/A')}")
        
        return script_details
    except Exception as e:
        print(f"Error decoding script: {e}")
        return None

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <txid or script_hex>")
        sys.exit(1)
    
    input_value = sys.argv[1]
    
    # Determine if input is a transaction ID or script hex
    if len(input_value) == 64 and all(c in '0123456789abcdefABCDEF' for c in input_value):
        # Looks like a transaction ID
        decode_transaction(input_value)
    else:
        # Assume it's a script hex
        decode_redeem_script(input_value)

if __name__ == "__main__":
    main()
