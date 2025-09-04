# PYTHON NECTAR MODULE for Data Analyst

This is a Python API module designed to run queries on Nectar.

---
## Installation

```bash
pip3 install nectarpy
```

---
## Python Example

```python
from nectarpy import NectarClient
```

```python
API_SECRET = "<api-secret>"
```

```python
nectar_client = NectarClient(API_SECRET)
```

## 3. Processing Methods

### Method 1: Single Data Source

Analyze data from a single dataset.

| Parameter      | Required | Description                                                                 |
| -------------- | :------: | --------------------------------------------------------------------------- |
| main_func      | ✔️       | The main analysis function to be applied over the merged dataset.           |
| bucket_ids     | ✔️       | List of data source identifiers used to locate and load datasets.           |
| policy_indexes | ✔️       | List of policy index values, one for each `bucket_id`, to apply policy control. |

**Example:** One hospital, one clinic.

```python
def min_func():
    import pandas as pd
    df = pd.read_csv("/app/data/worker-data.csv")
    
    if df.empty:
        return {"min_heart_rate": None, "min_age": None}

    return {
        "min_heart_rate": int(df["heart_rate"].min()),
        "min_age": int(df["age"].min()),
    }
```
### Method 2: Distributed Processing

Each dataset is processed independently at the compute node, and results are later aggregated on the scheduler.

| Parameter         | Required | Description                                                                                                                                                 |
| ----------------- | :------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| pre_compute_func  | ✔️       | A local function that runs on each worker node during distributed processing when **is_separate_data** is **True**. Otherwise, it acts as a data filter function. |
| is_separate_data  | ✔️       | Set to **True** to process each dataset independently. Default: **False** – Coordinated processing.                                                         |
| main_func         | ✔️       | The main analysis function to be applied to the merged dataset. The **list_of_partial_result** parameter represents either all raw data (coordinated) or intermediate results (distributed). |
| bucket_ids        | ✔️       | A list of data source identifiers used to locate and load datasets. When the list contains only one item, the **pre_compute_func** parameter is ignored.     |
| policy_indexes    | ✔️       | List of policy index values, one for each **bucket_id**, to apply policy control.                                                                           |

**Example:** Total patient count across hospitals, calculate averages separately then combine.

```python
def pre_compute_mean_func():
    import pandas as pd
    import logging as logger
    df = pd.read_csv("/app/data/worker-data.csv")
  
    filtered = df[(df["gender"] == "MALE") & (df["age"] > 50)]
    return {"sum": filtered["heart_rate"].sum(), "count": len(filtered)}


def main_mean_func(list_of_partial_result):
    total_heart = sum(d.get("sum", 0) for d in list_of_partial_result)
    total_count = sum(d.get("count", 0) for d in list_of_partial_result)
    return {
        "avg_heart_rate": total_heart / total_count if total_count else 0,
        "total_count": total_count
    }

result = nectar_client.byoc_query(
    pre_compute_func=pre_compute_mean_func,
    main_func=main_mean_func,
    is_separate_data=True,
    bucket_ids=[bucket_id],
    policy_indexes=[0],
)
```
### Method 3: Coordinated Processing

Data from multiple sources must be combined and processed together.

| Parameter         | Required | Description                                                                                                                                                 |
| ----------------- | :------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| pre_compute_func  | ✔️       | A local function that runs on each worker node during distributed processing when **is_separate_data** is True. Otherwise, it acts as a data filter function. |
| is_separate_data  | ✔️       | Set to **True** to process each dataset independently. Default: False – Coordinated processing.                                                             |
| main_func         | ✔️       | The main analysis function to be applied to the merged dataset. The **list_of_partial_result** parameter represents either all raw data (in coordinated) or all intermediate results (in distributed). |
| bucket_ids        | ✔️       | A list of data source identifiers used to locate and load datasets. When the list contains only one item, the **pre_compute_func** parameter is ignored.     |
| policy_indexes    | ✔️       | List of policy index values, one for each **bucket_id**, to apply policy control.                                                                           |

**Example:** Multi-source regression analysis, correlation across datasets.

```python
def main_mean_func(list_of_partial_result):
    import pandas as pd
    all_data = pd.concat(list_of_partial_result, ignore_index=True)
    total_count = len(all_data)
    heart_rate_mean = all_data['heart_rate'].mean() if total_count else 0.0
    
    if total_count == 0:
        return {"count": 0, "mean": 0.0}

    return {
        "count": int(total_count),
        "mean": float(heart_rate_mean),
    }
```