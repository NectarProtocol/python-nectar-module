import json
import os
import unittest
from pathlib import Path

from web3 import Web3

from nectarpy import Nectar, NectarClient


def make_count_func():
    # Use a locally created callable so dill serializes code payload for remote worker.
    def _count_func():
        with open("/app/data/worker-data.csv", "r", encoding="utf-8", newline="") as f:
            # Skip header row and count remaining lines.
            next(f, None)
            return float(sum(1 for _ in f))

    return _count_func


def ensure_role(web3: Web3, user_role, admin_address: str, admin_private_key: str, target: str, role_name: str) -> None:
    current_role = user_role.functions.getUserRole(target).call()
    if current_role == role_name:
        return

    role_value = getattr(user_role.functions, role_name)().call()
    tx = user_role.functions.assignUserRole(target, role_value).build_transaction(
        {
            "from": admin_address,
            "nonce": web3.eth.get_transaction_count(admin_address),
            "gas": 300000,
            "gasPrice": web3.eth.gas_price,
        }
    )
    signed = web3.eth.account.sign_transaction(tx, admin_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    current_role = user_role.functions.getUserRole(target).call()
    if current_role != role_name:
        raise RuntimeError(f"Role assignment failed: expected {role_name}, got {current_role}")


@unittest.skipUnless(
    os.getenv("RUN_LIVE_CATEGORIZATION_INTEGRATION") == "1",
    "Set RUN_LIVE_CATEGORIZATION_INTEGRATION=1 to run live chain/backend integration tests.",
)
class TestCategorizationIntegrationLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo_root = Path(__file__).resolve().parent
        contracts_dir = repo_root.parent / "contracts"
        config_dir = repo_root / "nectarpy" / "config"

        network = os.getenv("NETWORK_MODE", "localhost")
        with open(config_dir / "blockchain.json", "r", encoding="utf-8") as f:
            chain_cfg = json.load(f)[network]

        contracts_chain = contracts_dir / "blockchain.json"
        if contracts_chain.exists():
            with open(contracts_chain, "r", encoding="utf-8") as f:
                contracts_cfg = json.load(f).get(network)
            if contracts_cfg:
                chain_cfg = {**chain_cfg, **contracts_cfg}

        wallet_path = Path(os.getenv("WALLET_PATH", contracts_dir / "wallet.json"))
        with open(wallet_path, "r", encoding="utf-8") as f:
            wallet_cfg = json.load(f)

        cls.network = network
        cls.worker_url = os.getenv("WORKER_URL", "tls://worker-proxy-1:5229")
        cls.do_private_key = os.getenv("DO_PRIVATE_KEY", wallet_cfg["adminPrivateKey"])
        cls.da_private_key = os.getenv("DA_PRIVATE_KEY", wallet_cfg["ppcPrivateKey"])

        rpc_url = os.getenv("RPC_URL", chain_cfg["url"])
        cls.web3 = Web3(Web3.HTTPProvider(rpc_url))
        if not cls.web3.is_connected():
            raise RuntimeError(f"RPC not reachable: {rpc_url}")

        cls.admin_address = cls.web3.eth.account.from_key(cls.do_private_key).address
        cls.da_address = cls.web3.eth.account.from_key(cls.da_private_key).address

        with open(config_dir / "UserRole.json", "r", encoding="utf-8") as f:
            user_role_abi = json.load(f)["abi"]
        user_role = cls.web3.eth.contract(
            address=Web3.to_checksum_address(chain_cfg["userRole"]),
            abi=user_role_abi,
        )
        ensure_role(
            cls.web3,
            user_role,
            cls.admin_address,
            cls.do_private_key,
            cls.admin_address,
            "DO",
        )
        ensure_role(
            cls.web3,
            user_role,
            cls.admin_address,
            cls.do_private_key,
            cls.da_address,
            "DA",
        )

        cls.nectar_do = Nectar(cls.do_private_key, cls.network)
        cls.nectar_da = NectarClient(cls.da_private_key, cls.network)

    def test_full_consent_response_contract(self):
        policy_id = self.nectar_do.add_policy(
            allowed_categories=["*"],
            allowed_addresses=[self.da_address],
            allowed_columns=["age", "heart_rate", "smoking"],
            valid_days=7,
            usd_price=0.01,
            identity_disclosure_operations=["count"],
        )
        bucket_id = self.nectar_do.add_bucket(
            policy_ids=[policy_id],
            use_allowlists=[False],
            data_format="std1",
            node_address=self.worker_url,
        )

        result = self.nectar_da.byoc_query(
            main_func=make_count_func(),
            is_separate_data=False,
            bucket_ids=[bucket_id],
            policy_indexes=[0],
            categorize_by_do=True,
            aggregate_type="count",
        )

        bucket_key = f"bucket_{bucket_id}"
        self.assertEqual(result["categorizedByDO"], True)
        self.assertIn(bucket_key, result["results"])
        self.assertIn("count", result["results"][bucket_key])
        self.assertIn("aggregatedTotal", result)
        self.assertNotIn("nonConsenting", result)

    def test_partial_consent_response_contract(self):
        policy_id = self.nectar_do.add_policy(
            allowed_categories=["*"],
            allowed_addresses=[self.da_address],
            allowed_columns=["age", "heart_rate", "smoking"],
            valid_days=7,
            usd_price=0.01,
            identity_disclosure_operations=[],
        )
        bucket_id = self.nectar_do.add_bucket(
            policy_ids=[policy_id],
            use_allowlists=[False],
            data_format="std1",
            node_address=self.worker_url,
        )

        result = self.nectar_da.byoc_query(
            main_func=make_count_func(),
            is_separate_data=False,
            bucket_ids=[bucket_id],
            policy_indexes=[0],
            categorize_by_do=True,
            aggregate_type="count",
        )

        bucket_key = f"bucket_{bucket_id}"
        self.assertEqual(result["categorizedByDO"], "partial")
        self.assertEqual(result["results"], {})
        self.assertEqual(result["nonConsenting"], [bucket_key])
        self.assertIn("aggregatedTotal", result)

    def test_unauthorized_bucket_hard_fails(self):
        policy_id = self.nectar_do.add_policy(
            allowed_categories=["*"],
            allowed_addresses=[self.admin_address],
            allowed_columns=["age", "heart_rate", "smoking"],
            valid_days=7,
            usd_price=0.01,
            identity_disclosure_operations=["count"],
        )
        bucket_id = self.nectar_do.add_bucket(
            policy_ids=[policy_id],
            use_allowlists=[True],
            data_format="std1",
            node_address=self.worker_url,
        )

        with self.assertRaises(Exception) as exc:
            self.nectar_da.byoc_query(
                main_func=make_count_func(),
                is_separate_data=False,
                bucket_ids=[bucket_id],
                policy_indexes=[0],
                categorize_by_do=True,
                aggregate_type="count",
            )
        err = str(exc.exception)
        self.assertTrue(
            "Unauthorized access" in err
            or "Query failed" in err
            or "Something went wrong" in err
        )

    def test_backward_compatibility_without_categorization(self):
        policy_id = self.nectar_do.add_policy(
            allowed_categories=["*"],
            allowed_addresses=[self.da_address],
            allowed_columns=["age", "heart_rate", "smoking"],
            valid_days=7,
            usd_price=0.01,
            identity_disclosure_operations=["count"],
        )
        bucket_id = self.nectar_do.add_bucket(
            policy_ids=[policy_id],
            use_allowlists=[False],
            data_format="std1",
            node_address=self.worker_url,
        )

        result = self.nectar_da.byoc_query(
            main_func=make_count_func(),
            is_separate_data=False,
            bucket_ids=[bucket_id],
            policy_indexes=[0],
            categorize_by_do=False,
            aggregate_type=None,
        )
        self.assertFalse(isinstance(result, dict) and "categorizedByDO" in result)


if __name__ == "__main__":
    unittest.main()
