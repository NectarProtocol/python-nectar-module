import json
import types
import unittest
from unittest.mock import MagicMock, patch

from nectarpy.lib import Nectar
from nectarpy.lib_v1 import NectarClient


def build_web3_mock():
    web3 = MagicMock()
    web3.eth.get_transaction_count.return_value = 1
    web3.eth.send_raw_transaction.return_value = b"tx_hash"
    web3.eth.wait_for_transaction_receipt.return_value = {"status": 1}
    web3.eth.account.sign_transaction.return_value = types.SimpleNamespace(
        rawTransaction=b"signed_tx"
    )
    return web3


class NectarClientCategorizationTests(unittest.TestCase):
    def test_pay_query_includes_categorization_metadata(self):
        client = object.__new__(NectarClient)
        client.account = {"address": "0xabc", "private_key": "0x123"}
        client.web3 = build_web3_mock()
        client.QueryManager = MagicMock()
        client.QueryManager.functions.getUserIndex.return_value.call.return_value = 7
        client.QueryManager.functions.payQuery.return_value.build_transaction.return_value = {
            "tx": "built"
        }

        with patch("nectarpy.lib_v1.encryption.hybrid_encrypt_v1") as encrypt_mock:
            encrypt_mock.return_value = json.dumps({"cipher": "abc"})
            user_index, _ = client.pay_query(
                query_str={"k": "v"},
                price=10,
                bucket_ids=[1],
                policy_indexes=[0],
                categorize_by_do=True,
                aggregate_type="count",
            )

        self.assertEqual(user_index, 7)
        pay_args = client.QueryManager.functions.payQuery.call_args[0]
        payload = json.loads(pay_args[1])
        self.assertEqual(payload["categorizeByDO"], True)
        self.assertEqual(payload["aggregate"]["type"], "count")

    def test_byoc_query_requires_aggregate_type_when_categorized(self):
        client = object.__new__(NectarClient)
        client.check_if_is_valid_user_role = MagicMock()

        def aggregate_fn():
            return 1

        with self.assertRaises(ValueError):
            client.byoc_query(
                main_func=aggregate_fn,
                is_separate_data=False,
                bucket_ids=[1],
                policy_indexes=[0],
                categorize_by_do=True,
                aggregate_type=None,
            )

    def test_byoc_query_forwards_categorization_options(self):
        client = object.__new__(NectarClient)
        client.check_if_is_valid_user_role = MagicMock()
        client.get_pay_amount = MagicMock(return_value=10)
        client.approve_payment = MagicMock()
        client.pay_query = MagicMock(return_value=(11, {"status": 1}))
        client.wait_for_query_result = MagicMock(return_value={"ok": True})

        def aggregate_fn():
            return 1

        result = client.byoc_query(
            main_func=aggregate_fn,
            is_separate_data=False,
            bucket_ids=[1],
            policy_indexes=[0],
            categorize_by_do=True,
            aggregate_type="count",
        )

        self.assertEqual(result, {"ok": True})
        self.assertEqual(client.pay_query.call_args.kwargs["categorize_by_do"], True)
        self.assertEqual(client.pay_query.call_args.kwargs["aggregate_type"], "count")


class NectarPolicyDisclosureTests(unittest.TestCase):
    def test_add_policy_defaults_identity_disclosure_operations(self):
        nectar = object.__new__(Nectar)
        nectar.check_if_is_valid_user_role = MagicMock()
        nectar.account = {"address": "0xabc", "private_key": "0x123"}
        nectar.web3 = build_web3_mock()
        nectar.EoaBond = MagicMock()
        nectar.EoaBond.functions.addPolicy.return_value.build_transaction.return_value = {
            "tx": "built"
        }

        nectar.add_policy(
            allowed_categories=["*"],
            allowed_addresses=["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"],
            allowed_columns=["age"],
            valid_days=7,
            usd_price=0.01,
        )

        args = nectar.EoaBond.functions.addPolicy.call_args[0]
        self.assertEqual(args[-1], [])

    def test_read_policy_returns_identity_disclosure_operations(self):
        nectar = object.__new__(Nectar)
        nectar.EoaBond = MagicMock()
        nectar.EoaBond.functions.policies.return_value.call.return_value = [
            123,
            10,
            "0xowner",
            False,
        ]
        nectar.EoaBond.functions.getAllowedCategories.return_value.call.return_value = ["*"]
        nectar.EoaBond.functions.getAllowedAddresses.return_value.call.return_value = [
            "0x1"
        ]
        nectar.EoaBond.functions.getAllowedColumns.return_value.call.return_value = ["age"]
        nectar.EoaBond.functions.getIdentityDisclosureOperations.return_value.call.return_value = [
            "count"
        ]

        policy = nectar.read_policy(42)
        self.assertEqual(policy["identity_disclosure_operations"], ["count"])

    def test_set_identity_disclosure_operations_rejects_invalid_operation(self):
        nectar = object.__new__(Nectar)
        with self.assertRaises(ValueError):
            nectar.set_identity_disclosure_operations(1, ["variance"])

    def test_add_policy_falls_back_to_legacy_addpolicy_signature_when_only_6arg_available(self):
        nectar = object.__new__(Nectar)
        nectar.check_if_is_valid_user_role = MagicMock()
        nectar.account = {"address": "0xabc", "private_key": "0x123"}
        nectar.web3 = build_web3_mock()
        nectar.EoaBond = MagicMock()
        nectar.EoaBond.abi = [
            {
                "type": "function",
                "name": "addPolicy",
                "inputs": [{}, {}, {}, {}, {}, {}],
            }
        ]
        nectar.EoaBond.functions.addPolicy.return_value.build_transaction.return_value = {
            "tx": "built"
        }

        nectar.add_policy(
            allowed_categories=["*"],
            allowed_addresses=["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"],
            allowed_columns=["age"],
            valid_days=7,
            usd_price=0.01,
        )

        args = nectar.EoaBond.functions.addPolicy.call_args[0]
        self.assertEqual(len(args), 6)

    def test_add_policy_uses_setter_for_disclosure_on_legacy_abi(self):
        nectar = object.__new__(Nectar)
        nectar.check_if_is_valid_user_role = MagicMock()
        nectar.account = {"address": "0xabc", "private_key": "0x123"}
        nectar.web3 = build_web3_mock()
        nectar.EoaBond = MagicMock()
        nectar.EoaBond.abi = [
            {
                "type": "function",
                "name": "addPolicy",
                "inputs": [{}, {}, {}, {}, {}, {}],
            },
            {
                "type": "function",
                "name": "setIdentityDisclosureOperations",
                "inputs": [{}, {}],
            },
        ]
        nectar.EoaBond.functions.addPolicy.return_value.build_transaction.return_value = {
            "tx": "built"
        }
        nectar.set_identity_disclosure_operations = MagicMock(return_value={"status": 1})

        nectar.add_policy(
            allowed_categories=["*"],
            allowed_addresses=["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"],
            allowed_columns=["age"],
            valid_days=7,
            usd_price=0.01,
            identity_disclosure_operations=["count"],
        )

        nectar.set_identity_disclosure_operations.assert_called_once()

    def test_add_policy_rejects_disclosure_if_contract_does_not_support_it(self):
        nectar = object.__new__(Nectar)
        nectar.check_if_is_valid_user_role = MagicMock()
        nectar.account = {"address": "0xabc", "private_key": "0x123"}
        nectar.web3 = build_web3_mock()
        nectar.EoaBond = MagicMock()
        nectar.EoaBond.abi = [
            {
                "type": "function",
                "name": "addPolicy",
                "inputs": [{}, {}, {}, {}, {}, {}],
            }
        ]

        with self.assertRaises(RuntimeError):
            nectar.add_policy(
                allowed_categories=["*"],
                allowed_addresses=["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"],
                allowed_columns=["age"],
                valid_days=7,
                usd_price=0.01,
                identity_disclosure_operations=["count"],
            )

    def test_read_policy_defaults_empty_disclosure_operations_when_getter_absent(self):
        nectar = object.__new__(Nectar)
        nectar.EoaBond = MagicMock()
        nectar.EoaBond.abi = []
        nectar.EoaBond.functions.policies.return_value.call.return_value = [
            123,
            10,
            "0xowner",
            False,
        ]
        nectar.EoaBond.functions.getAllowedCategories.return_value.call.return_value = ["*"]
        nectar.EoaBond.functions.getAllowedAddresses.return_value.call.return_value = [
            "0x1"
        ]
        nectar.EoaBond.functions.getAllowedColumns.return_value.call.return_value = ["age"]

        policy = nectar.read_policy(42)
        self.assertEqual(policy["identity_disclosure_operations"], [])

    def test_set_identity_disclosure_operations_rejects_when_contract_lacks_method(self):
        nectar = object.__new__(Nectar)
        nectar.EoaBond = MagicMock()
        nectar.EoaBond.abi = []

        with self.assertRaises(RuntimeError):
            nectar.set_identity_disclosure_operations(1, ["count"])


if __name__ == "__main__":
    unittest.main()
