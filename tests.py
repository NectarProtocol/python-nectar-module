import os
import unittest
from nectarpy import Nectar
from dotenv import load_dotenv

load_dotenv()

API_SECRET = os.getenv("API_SECRET")
EVM_NODE = os.getenv("EVM_NODE")


class TestNectar(unittest.TestCase):

    def test_count_query(self):
        nectar = Nectar(API_SECRET, EVM_NODE)
        result = nectar.query(
            aggregate_type="count",
            aggregate_column="smoking",
            filters="[]",
        )
        self.assertTrue(isinstance(result, float))
        print("-> count result:", result)

    def test_mean_query(self):
        nectar = Nectar(API_SECRET, EVM_NODE)
        result = nectar.query(
            aggregate_type="mean",
            aggregate_column="age",
            filters="[]",
        )
        self.assertTrue(isinstance(result, float))
        print("-> mean result:", result)

    def test_variance_query(self):
        nectar = Nectar(API_SECRET, EVM_NODE)
        result = nectar.query(
            aggregate_type="variance",
            aggregate_column="heart_rate",
            filters="[]",
        )
        self.assertTrue(isinstance(result, float))
        print("-> variance result:", result)

    def test_invalid_query(self):
        nectar = Nectar(API_SECRET, EVM_NODE)
        with self.assertRaises(ValueError):
            nectar.query(
                aggregate_type="invalid-type",  # invalid
                aggregate_column="age",
                filters="[]",
            )
        print("-> query failed as expected")

    def test_query_with_filter(self):
        nectar = Nectar(API_SECRET, EVM_NODE)
        filters = '[ { "column": "smoking", "filter": "=", "value": false } ]'
        result = nectar.query(
            aggregate_type="count",
            aggregate_column="smoking",
            filters=filters,
        )
        self.assertTrue(isinstance(result, float))
        print("-> count result with filter:", result)

    def test_add_policy(self):
        nectar = Nectar(API_SECRET, EVM_NODE)
        price = 123
        policy_id = nectar.add_policy(
            allowed_categories=["category1"],
            allowed_addresses=[],
            allowed_columns=["column1"],
            valid_days=1000,
            price=price,
        )
        policy = nectar.read_policy(policy_id)
        self.assertEqual(policy["price"], price)
        print("-> successfully added policy")

    def test_add_bucket(self):
        nectar = Nectar(API_SECRET, EVM_NODE)
        node_address = "node.example.com"
        bucket_id = nectar.add_bucket(
            policy_ids=[123],
            data_format="std1",
            node_address=node_address,
        )
        bucket = nectar.read_bucket(bucket_id)
        self.assertEqual(bucket["node_address"], node_address)
        print("-> successfully added bucket")


if __name__ == "__main__":
    unittest.main()
