#!/usr/bin/env python3
"""
Simple hash function for ZKCP demo
"""

import sys
import hashlib

def sha256(data):
    """Return SHA256 hash of input data"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <data>")
        sys.exit(1)
    
    input_data = sys.argv[1]
    hash_result = sha256(input_data)
    print(hash_result)
