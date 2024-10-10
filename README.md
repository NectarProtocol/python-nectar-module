# PYTHON NECTAR MODULE

This is a Python API module designed to run queries on Nectar, add bucket information, and set policies.

## Install

```bash
pip3 install nectarpy
```

## Python Example

```python
from nectarpy import Nectar
```

```python
API_SECRET = "<api-secret>"
```

```python
nectar = Nectar(API_SECRET)
```

```python
policy_id = nectar.add_policy(
    allowed_categories=["*"],
    allowed_addresses=[],
    allowed_columns=["*"],
    valid_days=1000,
    usd_price=0.0123,
)
```

```python
TEE_DATA_URL = "https://<ip-address>:5229/"
```

```python
bucket_id = nectar.add_bucket(
    policy_ids=[policy_id],
    data_format="std1",
    node_address=TEE_DATA_URL,
)
```

```python
result = nectar.train_model(
    type="linear-regression",
    parameters='{"xcols":["heart_rate","age"],"ycol":"height"}',
    filters='[{"column":"smoking","filter":"=","value":false}]',
    use_allowlists=[False],
    access_indexes=[0],
    bucket_ids=[bucket_id],
    policy_indexes=[0],
)
```

```python
print(result)
```

## Integration Tests

### 1: Create a .env file

```
API_SECRET=0x123...
NETWORK_MODE=<localhost | moonbase | moonbeam>
TEE_DATA_URL=https://<ip-address>:5229/
```

### 2: Run

```bash
python3 tests.py
```
