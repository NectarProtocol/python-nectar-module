import json
import os
import time
import dill
from web3.types import TxReceipt
from web3.exceptions import ContractLogicError, TimeExhausted
from nectarpy.common import encryption
from nectarpy.common.blockchain_init import blockchain_init

current_dir = os.path.dirname(__file__)
VALID_DISCLOSURE_OPERATIONS = ["count", "sum", "mean", "min", "max"]


class NectarClient:
    """Client for sending queries to Nectar"""

    def __init__(self, api_secret: str, mode: str = "moonbeam"):
        blockchain_init(self, api_secret, mode)
        self.check_if_is_valid_user_role()

    def sans_hex_prefix(self, hexval: str) -> str:
        """Returns a hex string without the 0x prefix"""
        if hexval.startswith("0x"):
            return hexval[2:]
        return hexval

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

    def check_if_is_valid_user_role(self) -> str:
        """Getting current role"""
        roleName = self.UserRole.functions.getUserRole(self.account["address"]).call()
        if roleName not in ["DA"]:
            raise RuntimeError(
                "Unauthorized action: Your role does not have permission to perform this operation"
            )
        print(f"Current user role: {roleName}")
        return roleName

    def _next_nonce(self) -> int:
        return self.web3.eth.get_transaction_count(self.account["address"], "pending")

    def _wait_for_receipt(self, tx_hash, action: str) -> TxReceipt:
        timeout = int(os.getenv("NECTAR_TX_RECEIPT_TIMEOUT", "180"))
        poll_latency = int(os.getenv("NECTAR_TX_RECEIPT_POLL", "5"))
        try:
            return self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=timeout, poll_latency=poll_latency
            )
        except TimeExhausted as exc:
            raise TimeoutError(
                f"{action} transaction not mined within {timeout}s: {tx_hash.hex()}"
            ) from exc

    def get_pay_amount(self, bucket_ids: list, policy_indexes: list) -> int:
        policy_ids = []
        for i in range(len(bucket_ids)):
            try:
                p = self.EoaBond.functions.getPolicyIds(bucket_ids[i]).call()[
                    policy_indexes[i]
                ]
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

        approve_tx = self.USDC.functions.approve(
            self.qm_contract_addr, amount
        ).build_transaction(
            {
                "from": self.account["address"],
                "nonce": self._next_nonce(),
            }
        )
        approve_signed = self.web3.eth.account.sign_transaction(
            approve_tx, self.account["private_key"]
        )
        approve_hash = self.web3.eth.send_raw_transaction(approve_signed.rawTransaction)
        receipt = self._wait_for_receipt(approve_hash, "approve")
        if receipt.status != 1:
            raise RuntimeError(f"approve transaction reverted: {approve_hash.hex()}")
        return receipt

    def pay_query(
        self,
        query_str,
        price: int,
        bucket_ids: list,
        policy_indexes: list,
        categorize_by_do: bool = False,
        aggregate_type: str = None,
    ) -> tuple:
        """Sends a query along with a payment"""
        print("encrypting query under star node key...")
        ppcCmd = encryption.hybrid_encrypt_v1(self, query_str, policy_indexes)
        # Expose categorization metadata to backend-api (outside encrypted payload)
        if categorize_by_do or aggregate_type:
            ppc_data = json.loads(ppcCmd)
            if categorize_by_do:
                ppc_data["categorizeByDO"] = True
            if aggregate_type:
                ppc_data["aggregate"] = {"type": aggregate_type}
            ppcCmd = json.dumps(ppc_data)
        print("sending query with payment...")
        user_index = self.QueryManager.functions.getUserIndex(
            self.account["address"]
        ).call()
        query_tx = self.QueryManager.functions.payQuery(
            user_index,
            ppcCmd,
            price,
            bucket_ids,
            policy_indexes,
        ).build_transaction(
            {
                "from": self.account["address"],
                "nonce": self._next_nonce(),
            }
        )
        query_signed = self.web3.eth.account.sign_transaction(
            query_tx, self.account["private_key"]
        )
        query_hash = self.web3.eth.send_raw_transaction(query_signed.rawTransaction)
        query_receipt = self._wait_for_receipt(query_hash, "pay_query")
        if query_receipt.status != 1:
            raise RuntimeError(f"pay_query transaction reverted: {query_hash.hex()}")
        return user_index, query_receipt

    def wait_for_query_result(self, user_index) -> str:
        """Waits for the query result to be available"""
        print(f"waiting for result...")
        return self.get_result(user_index)

    def _decode_decrypted_result(self, decrypted):
        """
        Normalize decrypted query payload into a Python object.
        Supports:
        - JSON bytes/strings (categorized responses)
        - dill-serialized bytes (legacy payloads)
        - passthrough for already-decoded objects
        """
        if isinstance(decrypted, (bytes, bytearray)):
            raw = bytes(decrypted)
            try:
                text = raw.decode("utf-8")
                try:
                    return json.loads(text)
                except Exception:
                    return text
            except Exception:
                try:
                    return dill.loads(raw)
                except Exception:
                    return raw

        if isinstance(decrypted, str):
            try:
                return json.loads(decrypted)
            except Exception:
                return decrypted

        return decrypted

    def get_result(self, query_index):

        result = ""
        while not result:
            query = self.QueryManager.functions.getQueryByUserIndex(
                self.account["address"], query_index
            ).call()
            time.sleep(5)
            if query[2] != "":
                jdata = json.loads(query[2])
                if jdata.startswith("Something went wrong"):
                    raise RuntimeError(f"Query failed: {jdata}")
                result = json.loads(query[2])

        if result.startswith("Something went wrong"):
            raise RuntimeError(f"Query failed: {result}")
        else:
            existing_result = encryption.hybrid_decrypt_v1(self, result)
            existing_result = self._decode_decrypted_result(existing_result)
            print("result:")
            print("-" * 50)
            print(existing_result)
            print("-" * 50)
        return existing_result

    def byoc_query(
        self,
        pre_compute_func=None,
        main_func=None,
        is_separate_data: bool = False,
        bucket_ids: list = None,
        policy_indexes: list = None,
        categorize_by_do: bool = False,
        aggregate_type: str = None,
    ) -> tuple:
        """Sends a query along with a payment"""

        self.check_if_is_valid_user_role()

        if pre_compute_func is not None and not callable(pre_compute_func):
            raise TypeError("pre_compute_func must be a callable function or None")

        if main_func is not None and not callable(main_func):
            raise TypeError("main_func must be a callable function or None")

        if not isinstance(is_separate_data, bool):
            raise TypeError("is_separate_data must be a boolean")

        if len(bucket_ids) != len(policy_indexes):
            raise ValueError("Length of bucket_ids and policy_indexes must match")

        # Validate bucket_ids
        if not isinstance(bucket_ids, list) or len(bucket_ids) == 0:
            raise ValueError("bucket_ids must be a non-empty list")

        if not isinstance(policy_indexes, list) or len(policy_indexes) == 0:
            raise ValueError("policy_indexes must be a non-empty list")
        if len(bucket_ids) == 1:
            # Single worker
            if main_func is None or not callable(main_func):
                raise ValueError("Single worker requires a valid main_func")
        else:
            if pre_compute_func is None or not callable(pre_compute_func):
                raise ValueError("Multiple workers require a valid pre_compute_func")
            if main_func is None or not callable(main_func):
                raise ValueError("Multiple workers require a valid main_func")
        if categorize_by_do and not aggregate_type:
            raise ValueError(
                "categorize_by_do requires aggregate_type "
                "(e.g., 'count', 'sum', 'mean', 'min', 'max')"
            )
        if categorize_by_do and aggregate_type not in VALID_DISCLOSURE_OPERATIONS:
            raise ValueError(
                f"Invalid aggregate_type for categorize_by_do: {aggregate_type}. "
                f"Must be one of {VALID_DISCLOSURE_OPERATIONS}"
            )

        print("Sending query to blockchain...")
        price = self.get_pay_amount(bucket_ids, policy_indexes)

        """Approves a payment, sends a query, then fetches the result"""
        self.approve_payment(price)
        query_str = {
            "pre_compute_func": (
                dill.dumps(pre_compute_func, recurse=True) if pre_compute_func else None
            ),
            "main_func": dill.dumps(main_func, recurse=True) if main_func else None,
            "is_separate_data": is_separate_data,
            "categorizeByDO": categorize_by_do,
        }
        user_index, _ = self.pay_query(
            query_str,
            price,
            bucket_ids=bucket_ids,
            policy_indexes=policy_indexes,
            categorize_by_do=categorize_by_do,
            aggregate_type=aggregate_type,
        )
        query_res = self.wait_for_query_result(user_index)
        return query_res
