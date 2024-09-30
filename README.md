# PYTHON NECTAR MODULE

This is a Python API module designed to run queries on Nectar, add bucket information, and set policies.

## Install

```bash
pip3 install nectarpy
```

## Example

```python
from nectarpy import Nectar

nectar = Nectar("API-SECRET")

result = nectar.query(
    aggregate_type="variance",
    aggregate_column="heart_rate",
    filters='[ { "column": "smoking", "filter": "=", "value": false } ]',
)

print(result) # 1234.5
```

## Integration Tests

### Step 1: Create a .env file

```
API_SECRET=0x123...
EVM_NODE=http://127.0.0.1:8545/
TEE_DATA_URL=https://<ip-address>:5229/
```

### Step 2: Run!

```bash
python3 tests.py
```
