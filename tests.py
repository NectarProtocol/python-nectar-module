import os
import unittest
from nectarpy import Nectar
from dotenv import load_dotenv

load_dotenv()

API_SECRET = os.getenv("API_SECRET")
NETWORK_MODE = os.getenv("NETWORK_MODE")
TEE_DATA_URL = os.getenv("TEE_DATA_URL")


def setup_bucket(nectar: Nectar) -> int:
    policy_id = nectar.add_policy(
        allowed_categories=["*"],
        allowed_addresses=[],
        allowed_columns=["*"],
        valid_days=1000,
        usd_price=0.0123,
    )
    bucket_id = nectar.add_bucket(
        policy_ids=[policy_id],
        data_format="std1",
        node_address=TEE_DATA_URL,
    )
    return bucket_id


class TestNectar(unittest.TestCase):

    def test_count_query(self):
        nectar = Nectar(API_SECRET, NETWORK_MODE)
        bucket_id = setup_bucket(nectar)
        result = nectar.query(
            aggregate_type="count",
            aggregate_column="smoking",
            filters="[]",
            use_allowlists=[False],
            access_indexes=[0],
            bucket_ids=[bucket_id],
            policy_indexes=[0],
        )
        self.assertTrue(isinstance(result, float))
        print("-> count result:", result)

    def test_mean_query(self):
        nectar = Nectar(API_SECRET, NETWORK_MODE)
        bucket_id = setup_bucket(nectar)
        result = nectar.query(
            aggregate_type="mean",
            aggregate_column="age",
            filters="[]",
            use_allowlists=[False],
            access_indexes=[0],
            bucket_ids=[bucket_id],
            policy_indexes=[0],
        )
        self.assertTrue(isinstance(result, float))
        print("-> mean result:", result)

    def test_variance_query(self):
        nectar = Nectar(API_SECRET, NETWORK_MODE)
        bucket_id = setup_bucket(nectar)
        result = nectar.query(
            aggregate_type="variance",
            aggregate_column="heart_rate",
            filters="[]",
            use_allowlists=[False],
            access_indexes=[0],
            bucket_ids=[bucket_id],
            policy_indexes=[0],
        )
        self.assertTrue(isinstance(result, float))
        print("-> variance result:", result)

    def test_invalid_query(self):
        nectar = Nectar(API_SECRET, NETWORK_MODE)
        bucket_id = setup_bucket(nectar)
        with self.assertRaises(ValueError):
            nectar.query(
                aggregate_type="invalid-type",  # invalid
                aggregate_column="age",
                filters="[]",
                use_allowlists=[False],
                access_indexes=[0],
                bucket_ids=[bucket_id],
                policy_indexes=[0],
            )
        print("-> query failed as expected")

    def test_query_with_filter(self):
        nectar = Nectar(API_SECRET, NETWORK_MODE)
        bucket_id = setup_bucket(nectar)
        filters = '[{"column":"smoking","filter":"=","value":false}]'
        result = nectar.query(
            aggregate_type="count",
            aggregate_column="smoking",
            filters=filters,
            use_allowlists=[False],
            access_indexes=[0],
            bucket_ids=[bucket_id],
            policy_indexes=[0],
        )
        self.assertTrue(isinstance(result, float))
        print("-> count result with filter:", result)

    def test_linear_regression(self):
        nectar = Nectar(API_SECRET, NETWORK_MODE)
        bucket_id = setup_bucket(nectar)
        result = nectar.train_model(
            type="linear-regression",
            parameters='{"xcols":["heart_rate","age"],"ycol":"height"}',
            filters="[]",
            use_allowlists=[False],
            access_indexes=[0],
            bucket_ids=[bucket_id],
            policy_indexes=[0],
        )
        self.assertTrue(isinstance(result, dict))
        print("-> linear regression result:", result)

    def test_add_policy(self):
        nectar = Nectar(API_SECRET, NETWORK_MODE)
        price = 0.0123
        policy_id = nectar.add_policy(
            allowed_categories=["category1"],
            allowed_addresses=[],
            allowed_columns=["column1"],
            valid_days=1000,
            usd_price=price,
        )
        policy = nectar.read_policy(policy_id)
        self.assertEqual(policy["price"], price)
        print("-> successfully added policy")

    def test_add_bucket(self):
        nectar = Nectar(API_SECRET, NETWORK_MODE)
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
