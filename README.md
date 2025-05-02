# PYTHON NECTAR MODULE

This is a Python API module designed to run queries on Nectar, add bucket information, and set policies.

---
## Installation

To install the `nectarpy` module, use the following command:

```bash
pip3 install nectarpy
```

---
## Getting Started

### Importing the Module
To use `nectarpy`, first import the `Nectar` class:

```python
from nectarpy import Nectar
```

### Setting Up API Credentials
You must provide your **API_SECRET** key to authenticate requests:

```python
API_SECRET = "<api-secret>"
```

### Creating an Instance
Initialize the `Nectar` client using the API secret:

```python
nectar = Nectar(API_SECRET)
```

---
## Policy Management

### Adding Policies
Policies define which columns can be accessed and under what conditions.

#### **Adding a Policy for All Columns**
Allows access to all columns with a validity period of **1000 days** and a price of **0.0123 USD**:

```python
policy_id = nectar.add_policy(
    allowed_categories=["*"],                   # All data categories are allowed
    allowed_addresses=["<address-value>"],      # Only this wallet address is allowed to query. Example: 0x39Ccc3519e16ec309Fe89Eb782792faFfB1b399d
    allowed_columns=["*"],                      # All columns in the dataset are accessible
    valid_days=1000,                            # Policy is valid for 1000 days
    usd_price=0.0123,                           # Cost per query in USD
)
```

#### **Adding a Policy for Specific Columns**
Restricts access to only the `age` and `height` columns:

```python
policy_id = nectar.add_policy(
    allowed_categories=["*"],                   # All data categories are allowed
    allowed_addresses=["<address-value>"],      # Only this wallet address is allowed to query. Example: 0x39Ccc3519e16ec309Fe89Eb782792faFfB1b399d
    allowed_columns=["age", "height"],          # Only the age and height column in the dataset are accessible
    valid_days=1000,                            # Policy is valid for 1000 days
    usd_price=0.0123,                           # Cost per query in USD
)
```

#### **Parameters**

| Parameter          | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `allowed_categories` | List of allowed data categories (e.g., `["ONLY_PHARMA"]`, `["*"]` for all).       |
| `allowed_addresses`  | List of wallet addresses allowed to access this policy, this address can be found at https://nectar.tamarin.health. **Required**        |
| `allowed_columns`    | List of accessible data columns (e.g., `["age", "income"]`, or `["*"]`).     |
| `valid_days`         | How long (in days) the policy remains active.                               |
| `usd_price`          | Price per access in USD (floating-point number).                            |

---

---
## Bucket Management

### Adding a Bucket
The **TEE_DATA_URL** represents the secure enclave node where the data is stored.

```python
TEE_DATA_URL = "tls://<ip-address>:5229"
```

```python
bucket_id = nectar.add_bucket(
    policy_ids=[policy_id],
    data_format="std1",
    node_address=TEE_DATA_URL,
)
```

---
## Executing Queries

You can retrieve results from stored data using defined policies and bucket IDs.

```python
print(bucket_id)
```

---
## Exception Handling

### **Case 1: API_SECRET Has No Balance**
If your **API_SECRET** does not have sufficient funds, transactions will fail.

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
