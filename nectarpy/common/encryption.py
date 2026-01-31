import os
import json
import dill

current_dir = os.path.dirname(__file__)

def hybrid_encrypt_v1(self, query_str, *args, **kwargs):
    """Encrypts plaintext using the public key"""
    func_bytes = dill.dumps(query_str)
    enc, ciphertext = self.suite.seal(
        peer_pubkey= self.sn_pubkey,
        info=b"",
        aad=b"",
        message=func_bytes
    )
    secret = {
        "cipher": ciphertext.hex(),
        "encapsulatedKey": enc.hex(),
        "returnPubkey": self.hex_pubkey,
        "args": args,
        "kwargs": kwargs
    }
    print("Encryption completed using the public key")
    return json.dumps(secret)


def hybrid_decrypt_v1(self, secret) -> str:
    """Decrypts ciphertext using the API secret-derived key"""
    data = json.loads(secret)
    try:
        encapsulatedKey = data["encapsulatedKey"]
        cipher = data["cipher"]
        msg = self.suite.open(
            encap=bytes.fromhex(encapsulatedKey),
            our_privatekey= self.skey,
            info=b"",
            aad=b"",
            ciphertext=bytes.fromhex(cipher))
        print("done")
        return msg
    except Exception as e:
        print("Decryption failed: " + e)