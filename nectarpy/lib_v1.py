import json
import os
import time
import dill
from web3.types import TxReceipt
from web3.exceptions import ContractLogicError

from nectarpy.common import encryption
from nectarpy.common.blockchain_init import blockchain_init

current_dir = os.path.dirname(__file__)

class NectarClient:
    """Client for sending queries to Nectar"""
    def __init__(self, api_secret: str, mode: str = "moonbeam"):
        blockchain_init(self, api_secret, mode)


    def sans_hex_prefix(self, hexval: str) -> str:
        """Returns a hex string without the 0x prefix"""
        if hexval.startswith("0x"):
            return hexval[2:]
        return hexval


    def get_bucket_ids(
        self
    ) -> list:
        """Get all bucket ids from blockchain"""
        result = self.EoaBond.functions.getAllBucketIds().call()
        return result


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


    def get_user_role(
        self
    ) -> str:
        """Getting current role"""
        roleName = self.UserRole.functions.getUserRole(self.account["address"]).call()
        return roleName


    def get_pay_amount(self, bucket_ids: list, policy_indexes: list) -> int:
        policy_ids = []
        for i in range(len(bucket_ids)):
            try:
                p = self.EoaBond.functions.getPolicyIds(bucket_ids[i]).call()[policy_indexes[i]]
                policy_ids.append(p)
            except ContractLogicError as e:
                error_message = str(e)
                if "BucketNotFound" in error_message:
                    print(f"Error: Bucket ID {bucket_ids[i]} does not exist.")
                elif "NoPolicyIdsInBucket" in error_message:
                    print(f"Error: Bucket ID {bucket_ids[i]} has no policy IDs.")
                else:
                    print(f"Smart contract error: {e}")
                return 0

        prices = [self.read_policy(p)["price"] for p in policy_ids]
        return sum(prices)


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
        query_str,
        price: int,
        use_allowlists: list,
        access_indexes: list,
        bucket_ids: list,
        policy_indexes: list,
    ) -> tuple:
        """Sends a query along with a payment"""
        print("encrypting query under star node key...")
        ppcCmd = encryption.hybrid_encrypt_v1(self, query_str, policy_indexes, access_indexes, use_allowlists)
        print("sending query with payment...")
        user_index = self.QueryManager.functions.getUserIndex(
            self.account["address"]
        ).call()
        query_tx = self.QueryManager.functions.payQuery(
            user_index,
            ppcCmd,
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


    def wait_for_query_result(self, user_index) -> str:
        """Waits for the query result to be available"""
        print(f"waiting for mpc result...")
        return self.get_result(user_index)
    

    def get_result(self, query_index):
        print(f"query number: {query_index}" )
        result = ""
        while not result:
            query = self.QueryManager.functions.getQueryByUserIndex(self.account["address"], query_index).call()
            time.sleep(5)
            if query[2] != '':
                jdata = json.loads(query[2])
                if jdata.startswith("Something went wrong"):
                    raise RuntimeError(f"Query failed: {jdata}")
                result = json.loads(query[2])
        print("decrypting result...")
        if result.startswith("Something went wrong"):
            raise RuntimeError(f"Query failed: {result}")
        else:
            existing_result = encryption.hybrid_decrypt_v1(self, result)
            print("result:")
            print("-" * 50)
            print(existing_result)
            print("-" * 50)
        return query_index


    def byoc_query(
        self,
        func,
        bucket_ids: list,
        operation: str = None,
        policy_indexes: list = None,
        use_allowlists: list = None,
        access_indexes: list = None,
    ) -> tuple:
        """Sends a query along with a payment"""
        print("Checking the current logged-in user's role.")
        roleName = self.get_user_role()
        if (roleName != 'DA'):
            raise RuntimeError("Unauthorized action: Your role does not have permission to perform this operation")
        print("Sending query to blockchain...")
        price = self.get_pay_amount(bucket_ids, policy_indexes)
        """Approves a payment, sends a query, then fetches the result"""
        self.approve_payment(price)
        query_str = {
            "func": dill.dumps(func),
            "operation": operation
        }
        user_index, _ = self.pay_query(
            query_str, price, use_allowlists=use_allowlists, access_indexes=access_indexes, bucket_ids=bucket_ids, policy_indexes=policy_indexes
        )
        query_res = self.wait_for_query_result(user_index)
        return query_res