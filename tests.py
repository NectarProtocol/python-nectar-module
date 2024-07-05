import unittest
from nectar import Nectar

# Test Vector
API_SECRET = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"


class TestNectar(unittest.TestCase):

    def test_count_query(self):
        nectar = Nectar(API_SECRET)
        result = nectar.query(
            aggregate_type="count",
            aggregate_column="smoking",
            filters="[]",
        )
        self.assertTrue(isinstance(result, float))
        print("-> count result:", result)

    def test_mean_query(self):
        nectar = Nectar(API_SECRET)
        result = nectar.query(
            aggregate_type="mean",
            aggregate_column="age",
            filters="[]",
        )
        self.assertTrue(isinstance(result, float))
        print("-> mean result:", result)

    def test_variance_query(self):
        nectar = Nectar(API_SECRET)
        result = nectar.query(
            aggregate_type="variance",
            aggregate_column="heart_rate",
            filters="[]",
        )
        self.assertTrue(isinstance(result, float))
        print("-> variance result:", result)

    def test_invalid_query(self):
        nectar = Nectar(API_SECRET)
        with self.assertRaises(ValueError):
            nectar.query(
                aggregate_type="invalid-type",  # invalid
                aggregate_column="age",
                filters="[]",
            )
        print("-> query failed as expected")

    def test_query_with_filter(self):
        nectar = Nectar(API_SECRET)
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
