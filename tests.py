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


if __name__ == "__main__":
    unittest.main()
