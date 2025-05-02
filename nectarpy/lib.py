import os
import time
import secrets
from datetime import datetime, timedelta
from web3 import Web3
from web3.types import TxReceipt

from nectarpy.common import encryption
from nectarpy.common.blockchain_init import blockchain_init

current_dir = os.path.dirname(__file__)

class Nectar:
    """Client for sending queries to Nectar"""

    def __init__(self, api_secret: str, mode: str = "moonbeam"):
        blockchain_init(self, api_secret, mode)


    def sans_hex_prefix(self, hexval: str) -> str:
        """Returns a hex string without the 0x prefix"""
        if hexval.startswith("0x"):
            return hexval[2:]
        return hexval

    def approve_payment(self, amount: int) -> TxReceipt:
        """Approves an EC20 query payment"""
        print("approving query payment...")
        approve_tx = self.USDC.functions.approve(
            self.qm_contract_addr, amount
        ).build_transaction(
            {
                "from": self.account["address"],
                "nonce": self.web3.eth.get_transaction_count(self.account["address"]),
            }
        )
        approve_signed = self.web3.eth.account.sign_transaction(
            approve_tx, self.account["private_key"]
        )
        approve_hash = self.web3.eth.send_raw_transaction(approve_signed.rawTransaction)
        return self.web3.eth.wait_for_transaction_receipt(approve_hash)


    def pay_query(
        self,
        query: str,
        price: int,
        use_allowlists: list,
        access_indexes: list,
        bucket_ids: list,
        policy_indexes: list,
    ) -> tuple:
        """Sends a query along with a payment"""
        print("encrypting query under star node key...")
        encrypted_query = encryption.hybrid_encrypt_v1(self, query_str=query)
        print("sending query with payment...")
        user_index = self.QueryManager.functions.getUserIndex(
            self.account["address"]
        ).call()
        query_tx = self.QueryManager.functions.payQuery(
            user_index,
            encrypted_query,
            use_allowlists,
            access_indexes,
            price,
            bucket_ids,
            policy_indexes,
        ).build_transaction(
            {
                "from": self.account["address"],
                "nonce": self.web3.eth.get_transaction_count(self.account["address"]),
            }
        )
        query_signed = self.web3.eth.account.sign_transaction(
            query_tx, self.account["private_key"]
        )
        query_hash = self.web3.eth.send_raw_transaction(query_signed.rawTransaction)
        query_receipt = self.web3.eth.wait_for_transaction_receipt(query_hash)
        return user_index, query_receipt


    def wait_for_query_result(self, user_index: str) -> str:
        """Waits for the query result to be available"""
        print("waiting for mpc result...")
        result = ""
        while not result:
            query = self.QueryManager.functions.getQueryByUserIndex(
                self.account["address"], user_index
            ).call()
            time.sleep(5)
            if query[2] != '':
                result = query[2]
        print("decrypting result...")
        return encryption.hybrid_decrypt_v1(self, result)


    def get_pay_amount(self, bucket_ids: list, policy_indexes: list) -> int:
        policy_ids = []
        for i in range(len(bucket_ids)):
            p = self.EoaBond.functions.getPolicyIds(bucket_ids[i]).call()[
                policy_indexes[i]
            ]
            policy_ids.append(p)
        prices = [self.read_policy(p)["price"] for p in policy_ids]
        return sum(prices)

    def get_user_role(
        self
    ) -> str:
        """Getting current role"""
        roleName = self.UserRole.functions.getUserRole(self.account["address"]).call()
        return roleName
    

    def add_policy(
        self,
        allowed_categories: list,
        allowed_addresses: list,
        allowed_columns: list,
        valid_days: int,
        usd_price: float,
    ) -> int:
        """Set a new on-chain policy"""
        if len(allowed_addresses) == 0:
            raise RuntimeError("allowed_addresses check failed.")
        print("adding new policy...")
        roleName = self.get_user_role()
        if (roleName != 'DO'):
            raise RuntimeError("Unauthorized action: Your role does not have permission to perform this operation")
        price = Web3.to_wei(usd_price, "mwei")
        policy_id = secrets.randbits(256)
        edo = datetime.now() + timedelta(days=valid_days)
        exp_date = int(time.mktime(edo.timetuple()))
        
        for i in range(len(allowed_addresses)):
            checksum_address = Web3.to_checksum_address(allowed_addresses[i])
            allowed_addresses[i] = checksum_address
        
        tx_built = self.EoaBond.functions.addPolicy(
            policy_id,
            allowed_categories,
            allowed_addresses,
            allowed_columns,
            exp_date,
            price,
        ).build_transaction(
            {
                "from": self.account["address"],
                "nonce": self.web3.eth.get_transaction_count(self.account["address"]),
            }
        )
        tx_signed = self.web3.eth.account.sign_transaction(
            tx_built, self.account["private_key"]
        )
        tx_hash = self.web3.eth.send_raw_transaction(tx_signed.rawTransaction)
        self.web3.eth.wait_for_transaction_receipt(tx_hash)
        return policy_id


    def read_policy(self, policy_id: int) -> dict:
        """Fetches a policy on the blockchain"""
        policy_data = self.EoaBond.functions.policies(policy_id).call()
        return {
            "policy_id": policy_id,
            "allowed_categories": self.EoaBond.functions.getAllowedCategories(
                policy_id
            ).call(),
            "allowed_addresses": self.EoaBond.functions.getAllowedAddresses(
                policy_id
            ).call(),
            "allowed_columns": self.EoaBond.functions.getAllowedColumns(
                policy_id
            ).call(),
            "exp_date": policy_data[0],
            "price": policy_data[1],
            "owner": policy_data[2],
            "deactivated": policy_data[3],
        }


    def add_bucket(
        self,
        policy_ids: list,
        data_format: str,
        node_address: str,
    ) -> int:
        """Set a new on-chain bucket"""
        print("adding new bucket...")
        roleName = self.get_user_role()
        if (roleName != 'DO'):
            raise RuntimeError("Unauthorized action: Your role does not have permission to perform this operation")
        
        bucket_id = secrets.randbits(256)
        tx_built = self.EoaBond.functions.addBucket(
            bucket_id, policy_ids, data_format, node_address
        ).build_transaction(
            {
                "from": self.account["address"],
                "nonce": self.web3.eth.get_transaction_count(self.account["address"]),
            }
        )
        tx_signed = self.web3.eth.account.sign_transaction(
            tx_built, self.account["private_key"]
        )
        tx_hash = self.web3.eth.send_raw_transaction(tx_signed.rawTransaction)
        self.web3.eth.wait_for_transaction_receipt(tx_hash)
        print("adding new bucket - done")
        return bucket_id


    def read_bucket(self, bucket_id: int) -> dict:
        """Fetches a bucket from the blockchain"""
        bucket_data = self.EoaBond.functions.buckets(bucket_id).call()
        return {
            "bucket_id": bucket_id,
            "policy_ids": self.EoaBond.functions.getPolicyIds(bucket_id).call(),
            "data_format": bucket_data[0],
            "node_address": bucket_data[1],
            "owner": bucket_data[2],
            "deactivated": bucket_data[3],
        }


    def add_policy_to_bucket(
        self,
        bucket_id: int,
        policy_id: int,
    ) -> TxReceipt:
        """Add an access policy to a bucket"""
        print("adding bucket to policy...")
        tx_built = self.EoaBond.functions.addPolicyToBucket(
            bucket_id, policy_id
        ).build_transaction(
            {
                "from": self.account["address"],
                "nonce": self.web3.eth.get_transaction_count(self.account["address"]),
            }
        )
        tx_signed = self.web3.eth.account.sign_transaction(
            tx_built, self.account["private_key"]
        )
        tx_hash = self.web3.eth.send_raw_transaction(tx_signed.raw_transaction)
        return self.web3.eth.wait_for_transaction_receipt(tx_hash)


    def deactivate_policy(
        self,
        policy_id: int,
    ) -> TxReceipt:
        """Deactivates a policy"""
        print("deactivating policy...")
        tx_built = self.EoaBond.functions.deactivatePolicy(policy_id).build_transaction(
            {
                "from": self.account["address"],
                "nonce": self.web3.eth.get_transaction_count(self.account["address"]),
            }
        )
        tx_signed = self.web3.eth.account.sign_transaction(
            tx_built, self.account["private_key"]
        )
        tx_hash = self.web3.eth.send_raw_transaction(tx_signed.raw_transaction)
        return self.web3.eth.wait_for_transaction_receipt(tx_hash)