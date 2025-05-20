import argparse
from bitcoin.core import x, CScript
from bitcoin.core.script import (
    OP_SHA256,
    OP_EQUAL,
    OP_IF,
    OP_ELSE,
    OP_ENDIF,
    OP_CHECKSIG
)

def main():
    parser = argparse.ArgumentParser(description="Generate Bitcoin redeem script")
    parser.add_argument("hashk", help="SHA256 hash of encryption key (K)")
    parser.add_argument("seller_pubkey", help="Seller's compressed public key (hex)")
    parser.add_argument("buyer_pubkey", help="Buyer's compressed public key (hex)")

    args = parser.parse_args()

    # Construct script
    script = CScript([
        OP_SHA256,
        x(args.hashk),
        OP_EQUAL,
        OP_IF,
            x(args.seller_pubkey),
        OP_ELSE,
            x(args.buyer_pubkey),
        OP_ENDIF,
        OP_CHECKSIG
    ])

    print(script.hex())

if __name__ == "__main__":
    main()

