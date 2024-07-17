import json
import time
import os
from web3 import Web3
from web3.types import TxReceipt
from web3.gas_strategies.rpc import rpc_gas_price_strategy

current_dir = os.path.dirname(__file__)

BLOCKCHAIN_URL = "http://127.0.0.1:8545/"
NT_CONTRACT_ADDR = "0x941c42263080E3fec35F52A344DfCa0bEda103F4"
QM_CONTRACT_ADDR = "0xE6f79f5fC9752Aa833c9aA0d4C1BE3cE2AfF746E"


class Nectar:
    """Client for sending queries to Nectar"""

    def __init__(
        self,
        api_secret: str,
        blockchain_url: str = BLOCKCHAIN_URL,
        nt_contract_addr: str = NT_CONTRACT_ADDR,
        qm_contract_addr: str = QM_CONTRACT_ADDR,
    ):
        with open(os.path.join(current_dir, "QueryManager.json")) as f:
            qm_info = json.load(f)
        qm_abi = qm_info["abi"]
        with open(os.path.join(current_dir, "NToken.json")) as f:
            nt_info = json.load(f)
        nt_abi = nt_info["abi"]
        self.web3 = Web3(Web3.HTTPProvider(blockchain_url))
        self.account = {
            "private_key": api_secret,
            "address": self.web3.eth.account.from_key(api_secret).address,
        }
        self.web3.eth.set_gas_price_strategy(rpc_gas_price_strategy)
        self.NToken = self.web3.eth.contract(address=nt_contract_addr, abi=nt_abi)
        self.QueryManager = self.web3.eth.contract(address=qm_contract_addr, abi=qm_abi)
        self.qm_contract_addr = qm_contract_addr

    def approve_payment(self) -> TxReceipt:
        """Approves an EC20 query payment"""
        print("approving query payment...")
        query_price = self.QueryManager.functions.queryPrice().call()
        approve_tx = self.NToken.functions.approve(
            self.qm_contract_addr, query_price
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

    def pay_query(self, query: str) -> tuple:
        """Sends a query along with a payment"""
        print("sending query with payment...")
        user_index = self.QueryManager.functions.getUserIndex(
            self.account["address"]
        ).call()
        query_tx = self.QueryManager.functions.payQuery(
            user_index,
            query,
            "",
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

    def wait_for_query_result(self, user_index: str) -> float:
        """Waits for the query result to be available"""
        print("waiting for mpc result...")
        result = ""
        while not result:
            query = self.QueryManager.functions.getQueryByUserIndex(
                self.account["address"], user_index
            ).call()
            time.sleep(5)
            result = query[3]
        return float(result)

    def query(self, aggregate_type: str, aggregate_column: str, filters: str) -> float:
        """Approves a payment, sends a query, then fetches the result"""
        query_str = json.dumps(
            {
                "aggregate": {"type": aggregate_type, "column": aggregate_column},
                "filters": json.loads(filters),
            }
        )
        self.approve_payment()
        user_index, _ = self.pay_query(query_str)
        return self.wait_for_query_result(user_index)
