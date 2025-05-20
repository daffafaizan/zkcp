import argparse
import hashlib

def main():
    parser = argparse.ArgumentParser(description="Hash parser")
    parser.add_argument("k", help="Key (K)")

    args = parser.parse_args()

    hash_k = hashlib.sha256(args.k.encode()).hexdigest()

    print(hash_k)

if __name__ == "__main__":
    main()

