import hashlib

def sha256_stream_cipher_encrypt(secret_bytes, key_k):
    ciphertext = bytearray()
    counter = 0
    while len(ciphertext) < len(secret_bytes):
        # Generate keystream block
        block = hashlib.sha256(key_k + counter.to_bytes(4, 'big')).digest()
        # XOR block with secret bytes
        for i in range(min(len(secret_bytes) - len(ciphertext), len(block))):
            ciphertext.append(secret_bytes[len(ciphertext)] ^ block[i])
        counter += 1
    return bytes(ciphertext)

if __name__ == "__main__":
    secret = input("Input secret: ")
    key = input("Input key: ")

    print(sha256_stream_cipher_encrypt(secret.encode(), key.encode()).hex())
