# PYTHON NECTAR MODULE

## 1. Install the module

```
pip install nectarpy
```

• If you see an error, try `pip3 install nectarpy` instead.

• Wait until the installation finishes. You should see a message that it was installed successfully.

## 2. Use the module in Python

The library exports two role-specific clients:

**Data Owner (DO):** Nectar  
**Data Analyst (DA):** NectarClient

Your `API_SECRET` is your API account private key (hex string). It may start with `0x`.

Supported mode values are: `moonbeam` (default), `moonbase`, `localhost`.

### Data Owner (DO)

```python
from nectarpy import Nectar

API_SECRET = "<api-secret>"
nectar = Nectar(API_SECRET, mode="moonbeam")
```

**Role enforcement:** `Nectar` only works for accounts with the **DO** role. If your API account does not have the DO role, initialization will raise a `RuntimeError`.

### Data Analyst (DA)

```python
from nectarpy import NectarClient

API_SECRET = "<api-secret>"
nectar_client = NectarClient(API_SECRET, mode="moonbeam")
```

**Role enforcement:** `NectarClient` only works for accounts with the **DA** role. If your API account does not have the DA role, initialization will raise a `RuntimeError`.

## 3. Common operations

Below are minimal, end-to-end examples for the primary APIs exposed by the library.

### Data Owner (DO): policies & buckets

```python
from nectarpy import Nectar

API_SECRET = "<api-secret>"
nectar = Nectar(API_SECRET, mode="moonbeam")

# 1) Create a policy
policy_id = nectar.add_policy(
	allowed_categories=["*"],
	allowed_addresses=["0x0000000000000000000000000000000000000000"],
	allowed_columns=["*"],
	valid_days=30,
	usd_price=0.01,
)

# 2) Create a bucket that references one or more policies
bucket_id = nectar.add_bucket(
	policy_ids=[policy_id],
	use_allowlists=[True],
	data_format="std1",
	node_address="tls://<ip-address>:5229",
)
```

### Data Analyst (DA): run a BYOC query

```python
from nectarpy import NectarClient

API_SECRET = "<api-secret>"
nectar_client = NectarClient(API_SECRET, mode="moonbeam")

def count_func():
	import pandas as pd
	df = pd.read_csv("/app/data/worker-data.csv")
	return {"count": len(df)}

# 1) Prepare bucket/policy references (provided by the DO)
bucket_ids = ["<bucket-id>"]
policy_indexes = [0]

# 2) Execute the query
result = nectar_client.byoc_query(
	pre_compute_func=None,
	main_func=count_func,
	is_separate_data=False,
	bucket_ids=bucket_ids,
	policy_indexes=policy_indexes,
)

print(result)
```

## 4. Detailed Documentation in your Nectar account

• Data Analyst role: [API document for Data Analyst](https://nectar.tamarin.health/guidance-nectar/da)

• Data Owner role: [API document for Data Owner](https://nectar.tamarin.health/guidance-nectar/do)
