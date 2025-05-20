
import subprocess
import json
import binascii
import hashlib

# Parameters
txid = "7f4c8a2c913f98ba23b522a8bdddfd13b974ccefdbccd3fee8138496f7392f90"
vout = 0
amount = 0.9999
redeem_script = "a8203733cd977ff8eb18b987357e22ced99f46097f31ecb239e878ae63760e83e4d58763210236a3d5555b8620b05b0d6ecebd537b1b95e23850fa84488bd5d8c9993c354c2b6721037f8b7b205f05f5ea5845fea13637118c7f8b7a5d550bf0eeec218bd9e26a38cf68ac"
real_k = "HELLO"
privkey = "cPi7yTh9mNCePeoXmnX3RiqDMLgyUJXZs5dRvpdscaLxuHvmB9xe"

# Calculate redeem script hash
redeem_script_hash = hashlib.new("ripemd160", hashlib.sha256(bytes.fromhex(redeem_script)).digest()).hexdigest()

# Get seller address
seller_cmd = "bitcoin-cli -regtest -rpcwallet=sellerwallet getnewaddress"
seller_result = subprocess.run(seller_cmd, shell=True, text=True, capture_output=True)
seller_address = json.loads(seller_result.stdout)

# Create raw transaction
input_json = json.dumps([{"txid": txid, "vout": vout}])
output_json = json.dumps([{seller_address: amount}])
create_cmd = f'bitcoin-cli -regtest createrawtransaction \'[{"txid": "7f4c8a2c913f98ba23b522a8bdddfd13b974ccefdbccd3fee8138496f7392f90", "vout": 0}]\' \'[{"bcrt1qfuk35pksvumgm5yv5xwf235zlxaret72u866n5": 0.9999}]\''

create_result = subprocess.run(create_cmd, shell=True, text=True, capture_output=True)
rawtx = create_result.stdout.strip()

# Sign with the redeem script
prevtx_json = json.dumps([{"txid": txid, "vout": vout, "scriptPubKey": f"a914{redeem_script_hash}87", "redeemScript": redeem_script}])
sign_cmd = f'bitcoin-cli -regtest signrawtransactionwithkey {rawtx} \'["cPi7yTh9mNCePeoXmnX3RiqDMLgyUJXZs5dRvpdscaLxuHvmB9xe"]\'  \'{prevtx_json}\' "ALL"'

print(sign_cmd)
sign_result = subprocess.run(sign_cmd, shell=True, text=True, capture_output=True)
print(sign_result.stdout)
print(sign_result.stderr)
