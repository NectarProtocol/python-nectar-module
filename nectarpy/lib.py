import json
import time
import os
import secrets
import time
from datetime import datetime, timedelta
from web3 import Web3
from web3.types import TxReceipt
from web3.gas_strategies.rpc import rpc_gas_price_strategy

current_dir = os.path.dirname(__file__)

BLOCKCHAIN_URL = "http://127.0.0.1:8545/"
NT_CONTRACT_ADDR = "0x941c42263080E3fec35F52A344DfCa0bEda103F4"
QM_CONTRACT_ADDR = "0xE6f79f5fC9752Aa833c9aA0d4C1BE3cE2AfF746E"
EB_CONTRACT_ADDR = "0x2741607B0aF9C40c72a07d5e66f6d09B3da1d4D6"


class Nectar:
    """Client for sending queries to Nectar"""

    def __init__(
        self,
        api_secret: str,
        blockchain_url: str = BLOCKCHAIN_URL,
        nt_contract_addr: str = NT_CONTRACT_ADDR,
        qm_contract_addr: str = QM_CONTRACT_ADDR,
        eb_contract_addr: str = EB_CONTRACT_ADDR,
    ):
        with open(os.path.join(current_dir, "QueryManager.json")) as f:
            qm_info = json.load(f)
        qm_abi = qm_info["abi"]
        with open(os.path.join(current_dir, "USDC.json")) as f:
            nt_info = json.load(f)
        nt_abi = nt_info["abi"]
        with open(os.path.join(current_dir, "EoaBond.json")) as f:
            eb_info = json.load(f)
        eb_abi = eb_info["abi"]
        self.web3 = Web3(Web3.HTTPProvider(blockchain_url))
        self.account = {
            "private_key": api_secret,
            "address": self.web3.eth.account.from_key(api_secret).address,
        }
        self.web3.eth.set_gas_price_strategy(rpc_gas_price_strategy)
        self.USDC = self.web3.eth.contract(address=nt_contract_addr, abi=nt_abi)
        self.QueryManager = self.web3.eth.contract(address=qm_contract_addr, abi=qm_abi)
        self.EoaBond = self.web3.eth.contract(address=eb_contract_addr, abi=eb_abi)
        self.qm_contract_addr = qm_contract_addr

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
        print("sending query with payment...")
        user_index = self.QueryManager.functions.getUserIndex(
            self.account["address"]
        ).call()
        query_tx = self.QueryManager.functions.payQuery(
            user_index,
            query,
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
            result = query[2]
        return result

    def get_pay_amount(self, bucket_ids: list, policy_indexes: list) -> int:
        policy_ids = []
        for i in range(len(bucket_ids)):
            p = self.EoaBond.functions.getPolicyIds(bucket_ids[i]).call()[
                policy_indexes[i]
            ]
            policy_ids.append(p)
        prices = [self.read_policy(p)["price"] for p in policy_ids]
        return sum(prices)

    def query(
        self,
        aggregate_type: str,
        aggregate_column: str,
        filters: str,
        use_allowlists: list,
        access_indexes: list,
        bucket_ids: list,
        policy_indexes: list,
    ) -> float:
        """Approves a payment, sends a query, then fetches the result"""
        query_str = json.dumps(
            {
                "aggregate": {"type": aggregate_type, "column": aggregate_column},
                "filters": json.loads(filters),
            }
        )
        price = self.get_pay_amount(bucket_ids, policy_indexes)
        self.approve_payment(price)
        user_index, _ = self.pay_query(
            query_str, price, use_allowlists, access_indexes, bucket_ids, policy_indexes
        )
        query_res = self.wait_for_query_result(user_index)
        return float(query_res)

    def train_model(
        self,
        type: str,
        parameters: str,
        filters: str,
        use_allowlists: list,
        access_indexes: list,
        bucket_ids: list,
        policy_indexes: list,
    ) -> dict:
        """Approves a payment, sends a training request, then fetches the result"""
        query_str = json.dumps(
            {
                "operation": type,
                "parameters": json.loads(parameters),
                "filters": json.loads(filters),
            }
        )
        price = self.get_pay_amount(bucket_ids, policy_indexes)
        self.approve_payment(price)
        user_index, _ = self.pay_query(
            query_str, price, use_allowlists, access_indexes, bucket_ids, policy_indexes
        )
        query_res = self.wait_for_query_result(user_index)
        return json.loads(query_res)

    def add_policy(
        self,
        allowed_categories: list,
        allowed_addresses: list,
        allowed_columns: list,
        valid_days: int,
        price: int,
    ) -> int:
        """Set a new on-chain policy"""
        print("adding new policy...")
        policy_id = secrets.randbits(256)
        edo = datetime.now() + timedelta(days=valid_days)
        exp_date = int(time.mktime(edo.timetuple()))
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
