import os
import hpke
import json
from web3 import Web3
from pathlib import Path
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

def req_json(rel_path):
    parent_folder_path =  Path(__file__).resolve().parent.parent
    config_path = os.getenv('BLOCKCHAIN_CREDENTIAL',parent_folder_path)
    file_path = config_path / rel_path
    with open(file_path, 'r', encoding='utf-8') as file:
        jsonStr = file.read()
    return json.loads(jsonStr)

def blockchain_init(self, api_secret: str, mode: str = "moonbeam"):
    print("network mode:", mode)
    self.suite = hpke.Suite__DHKEM_P256_HKDF_SHA256__HKDF_SHA256__AES_128_GCM
    hkdf = HKDF(
        algorithm=self.suite.KDF.HASH,
        length=self.suite.KEM.NSECRET,
        salt=None,
        info=b"nectar-client-v1",
        backend=default_backend(),
    )
    skey_bytes = bytes.fromhex(sans_hex_prefix(self, api_secret))
    derived_key_bytes = hkdf.derive(skey_bytes)
    skey_int = int.from_bytes(derived_key_bytes, "big")
    self.skey = ec.derive_private_key(
        skey_int, self.suite.KEM.CURVE, default_backend()
    )
    self.hex_pubkey = self.suite.KEM._encode_public_key(
        self.skey.public_key()
    ).hex()
    sn_pubkey_bytes = bytes.fromhex(req_json("config/starnode.json")["public_key"])
    self.sn_pubkey = self.suite.KEM.decode_public_key(sn_pubkey_bytes)
    
    # blockchain
    blockchain = req_json("config/blockchain.json")[mode]
    qm_abi = req_json("config/QueryManager.json")["abi"]
    eb_abi = req_json("config/EoaBond.json")["abi"]
    nt_abi = req_json("config/USDC.json")["abi"]
    user_role_abi = req_json("config/UserRole.json")["abi"]
    
    self.web3 = Web3(Web3.HTTPProvider(blockchain["url"]))
    self.account = {
        "private_key": api_secret,
        "address": self.web3.eth.account.from_key(api_secret).address,
    }
    self.web3.eth.set_gas_price_strategy(rpc_gas_price_strategy)
    self.USDC = self.web3.eth.contract(address=blockchain["usdc"], abi=nt_abi)
    self.QueryManager = self.web3.eth.contract(
        address=blockchain["queryManager"], abi=qm_abi
    )
    self.EoaBond = self.web3.eth.contract(address=blockchain["eoaBond"], abi=eb_abi)
    self.qm_contract_addr = blockchain["queryManager"]
    self.UserRole = self.web3.eth.contract(address=blockchain["userRole"], abi=user_role_abi)
    print("api account address:", self.account["address"])

def sans_hex_prefix(self, hexval: str) -> str:
    """Returns a hex string without the 0x prefix"""
    if hexval.startswith("0x"):
        return hexval[2:]
    return hexval
