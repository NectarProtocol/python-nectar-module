# PYTHON NECTAR MODULE for Data Owner

This is a Python API module designed to add bucket information, and set policies.

---
## Installation

To install the `nectarpy` module, use the following command:

```bash
pip3 install nectarpy
```

---
## Getting started

### Importing the module
To use `nectarpy`, first import the `Nectar` class:

```python
from nectarpy import Nectar
```

### Setting up API credentials
You must provide your **API_SECRET** key to authenticate requests:

```python
API_SECRET = "<api-secret>" # Replace with your actual API secret. You can obtain the secret key when you generate the EOA key pair.
```

### Creating an Instance
Initialize the `Nectar` client using the API secret:

```python
nectar = Nectar(API_SECRET)
```

---
## Policy management

### Adding policies
> **Policies cannot be edited once saved.**  
> Ensure your policy settings and input parameters are exactly as you want them before saving.  
> To modify a policy: create a new policy with updated settings.
>
> You are responsible for keeping your own records of:
>
> - Policy content and input parameters
> - Policy index numbers (starting from 0: first policy = index 0, second policy = index 1, etc.)
> - Associated bucket ID for each policy

| Parameter          | Required | Description                                                                                       |
|--------------------|:--------:|---------------------------------------------------------------------------------------------------|
| allowed_categories |    ✔️    | List of allowed data categories (e.g., `["ONLY_PHARMA"]`, `["*"]` for all).                      |
| allowed_addresses  |    ✔️    | List of wallet addresses allowed to access this policy.                                           |
| allowed_columns    |    ✔️    | List of accessible data columns (e.g., `["age", "income"]`, or `["*"]`).                         |
| valid_days         |    ✔️    | How long (in days) the policy remains active.                                                     |
| usd_price          |    ✔️    | Price per access in USD (floating-point number).                                                  |

#### **Adding a policy for all columns**
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

#### **Adding a policy for specific columns**
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
---

---
## Bucket management

### Adding a Bucket

| Parameter       | Required | Description                                                                                                                                                                                                                                                                      |
|------------------|:--------:|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| policy_ids       |    ✔️    | List of policy IDs that define data access rules and filtering conditions for data buckets.                                                                                                                                                                                       |
| use_allowlists   |    ✔️    | Boolean setting to restrict access to approved Data Analysts only (`True`) or allow any valid Analyst with row-level filtering based on `"policy"` column (`False`). Each item in list `"use_allowlists"` maps directly to the item at the same index in list `"policy_ids"`. For example, `use_allowlists[0]` corresponds to `policy_ids[0]`, `use_allowlists[1]` corresponds to `policy_ids[1]`, and so on. |
| data_format      |    ✔️    | Data structure format specification.                                                                                                                                                                                                                                              |
| TEE_DATA_URL     |    ✔️    | The secure TLS endpoint where your dataset is hosted. This is a suggested variable name, you may define your own as needed.                                                                                                                                                       |                                                                                                                                       |


```python
TEE_DATA_URL = "tls://<ip-address>:5229"
```

```python
bucket_id = nectar.add_bucket(
    policy_ids=[policy_id],
    data_format="std1",
    use_allowlists=[True],
    node_address=TEE_DATA_URL,
)
```
---