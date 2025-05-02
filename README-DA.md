# PYTHON NECTAR MODULE

This is a Python API module designed to run queries on Nectar and add bucket information.

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

```python
bucket_ids = nectar_client.get_bucket_ids()
```

---
## Functions

### Aggregate Types: Linear Regression, Mean, Count, Variance, Minimum, Maximum, Sum

#### **Use Case 1: Linear Regression Analysis**

The `linear_regression_func` method performs a simple linear regression analysis on worker data, predicting **height** based on **heart rate** and **age**.

**Returns a dictionary containing:**
- **`coef`**: The regression coefficients for "heart_rate" and "age" (list).
- **`intercept`**: The y-intercept of the regression line (float).
- **`count`**: Total number of **age** records.

```python
def linear_regression_func():
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    df = pd.read_csv("/app/data/worker-data.csv")
    df_filtered = df[df['age'] > 10]
    x_values = ["heart_rate", "age"]
    y_values = 'height'
    model = LinearRegression()
    X_train = df_filtered[x_values]
    Y_train = df_filtered[y_values]
    model.fit(X_train, Y_train)
    return {
        "coef": model.coef_.tolist(),
        "intercept": float(model.intercept_),
        "count": len(df_filtered),
    }
```

---
#### **Use Case 2: Counting Records**

The `count_func` method calculates the total number of records (rows) in the **worker-data.csv** file.

**Returns:**
- **`count`**: The total number of records.

```python
def count_func():
    import pandas as pd
    df = pd.read_csv("/app/data/worker-data.csv")
    return {"count": len(df)}
```

---
#### **Use Case 3: Calculating Mean Age**

The `mean_func` method calculates the **average age** of workers and the total number of records.

**Returns:**
- **`count`**: Total number of records.
- **`mean`**: Average age of workers.

```python
def mean_func():
    import pandas as pd
    df = pd.read_csv("/app/data/worker-data.csv")
    count = len(df)
    mean = df['age'].mean()
    return {"count": count, "mean": mean}
```

---
#### **Use Case 4: Calculating Variance of Age**

The `variance_func` method calculates the **total number of records**, the **average age**, and the **variance of age**.

**Returns:**
- **`count`**: Total number of records.
- **`mean`**: Average age of workers.
- **`variance`**: Variance of the age column.

```python
def variance_func():
    import pandas as pd
    df = pd.read_csv("/app/data/worker-data.csv")
    count = len(df)
    mean = df['age'].mean()
    variance = df['age'].var()
    return {"count": count, "mean": mean, "variance": variance}
```

---
## Queries

### Single Data Node

```python
result = nectar_client.byoc_query(
    linear_regression_func,                         # Custom function to execute (e.g., a count or aggregation - one of Aggregate Types)
    bucket_ids=[bucket_ids[0]],                     # List of data bucket IDs to query
    operation="linear-regression",                  # Operation name
    policy_indexes=[0, 0],                          # Indexes of access policies for each bucket
    use_allowlists=[True, False],                   # Flags to indicate whether to enforce allowlist checks per bucket
    access_indexes=[0, 0]                           # Indexes for selecting which access level (of keys) to use, if applicable
)
```

```python
result = nectar_client.byoc_query(
    count_func,                                     # Custom function to execute (e.g., a count or aggregation - one of Aggregate Types)
    bucket_ids=[bucket_ids[0]],                     # List of data bucket IDs to query
    operation="count",                              # Operation name
    policy_indexes=[0, 0],                          # Indexes of access policies for each bucket
    use_allowlists=[True, False],                   # Flags to indicate whether to enforce allowlist checks per bucket
    access_indexes=[0, 0]                           # Indexes for selecting which access level (of keys) to use, if applicable
)
```

```python
result = nectar_client.byoc_query(
    mean_func,                                      # Custom function to execute (e.g., a count or aggregation - one of Aggregate Types)
    bucket_ids=[bucket_ids[0]],                     # List of data bucket IDs to query
    operation="mean",                               # Operation name
    policy_indexes=[0, 0],                          # Indexes of access policies for each bucket
    use_allowlists=[True, False],                   # Flags to indicate whether to enforce allowlist checks per bucket
    access_indexes=[0, 0]                           # Indexes for selecting which access level (of keys) to use, if applicable
)
```

```python
result = nectar_client.byoc_query(
    variance_func,                                  # Custom function to execute (e.g., a count or aggregation - one of Aggregate Types)
    bucket_ids=[bucket_ids[0]],                     # List of data bucket IDs to query
    operation="variance",                           # Operation name
    policy_indexes=[0, 0],                          # Indexes of access policies for each bucket
    use_allowlists=[True, False],                   # Flags to indicate whether to enforce allowlist checks per bucket
    access_indexes=[0, 0]                           # Indexes for selecting which access level (of keys) to use, if applicable
)
```

### Multiple Data Nodes

```python
result = nectar_client.byoc_query(
    linear_regression_func,                         # Custom function to execute (e.g., a count or aggregation - one of Aggregate Types)
    bucket_ids=[bucket_ids[0], bucket_ids[1]],      # List of data bucket IDs to query
    operation="linear-regression",                  # Operation name
    policy_indexes=[0, 0],                          # Indexes of access policies for each bucket
    use_allowlists=[True, False],                   # Flags to indicate whether to enforce allowlist checks per bucket
    access_indexes=[0, 0]                           # Indexes for selecting which access level (of keys) to use, if applicable
)
```

```python
result = nectar_client.byoc_query(
    count_func,                                     # Custom function to execute (e.g., a count or aggregation - one of Aggregate Types)
    bucket_ids=[bucket_ids[0], bucket_ids[1]],      # List of data bucket IDs to query
    operation="count",                              # Operation name
    policy_indexes=[0, 0],                          # Indexes of access policies for each bucket
    use_allowlists=[True, False],                   # Flags to indicate whether to enforce allowlist checks per bucket
    access_indexes=[0, 0]                           # Indexes for selecting which access level (of keys) to use, if applicable
)
```

```python
result = nectar_client.byoc_query(
    mean_func,                                      # Custom function to execute (e.g., a count or aggregation - one of Aggregate Types)
    bucket_ids=[bucket_ids[0], bucket_ids[1]],      # List of data bucket IDs to query
    operation="mean",                               # Operation name
    policy_indexes=[0, 0],                          # Indexes of access policies for each bucket
    use_allowlists=[True, False],                   # Flags to indicate whether to enforce allowlist checks per bucket
    access_indexes=[0, 0]                           # Indexes for selecting which access level (of keys) to use, if applicable
)
```

```python
result = nectar_client.byoc_query(
    variance_func,                                  # Custom aggregation function to be executed (e.g., variance, count, sum)
    bucket_ids=[bucket_ids[0], bucket_ids[1]],      # List of bucket IDs containing the data to query
    operation="variance",                           # Name of the aggregation operation to perform
    policy_indexes=[0, 0],                          # Indexes of the policies to apply for each respective bucket
    use_allowlists=[True, False],                   # Flags to indicate whether to enforce allowlist checks per bucket
    access_indexes=[0, 0]                           # Indexes for selecting which access level (of keys) to use, if applicable
)

```

---

### **Parameters**

| Parameter        | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| `<your function>` | A user-defined Python function (e.g., `lambda df: df.count()` - one of Aggregate Types) to run over the datasets. |
| `bucket_ids`      | List of bucket IDs (strings or ints) to query from.                          |
| `operation`       | A string representing the operation name (for combination purposes).    |
| `policy_indexes`  | A list of integers referencing policy positions matching each bucket.        |
| `use_allowlists`  | Flags to indicate whether to enforce allowlist checks per bucket  |
| `access_indexes`  | Indexes for selecting which access level (of keys) to use, if applicable     |

---

```python
print(result)
```

---
## Exception Handling

### **Bucket ID Does Not Exist**

```python
bucket_not_exist = "30551459429423590702715106722240816746282150213228561545827912304803497819734"
```

```python
result = nectar_client.byoc_query(
    variance_func,
    bucket_ids=[bucket_not_exist],
    operation="variance",
    policy_indexes=[0],
    use_allowlists=[True],
    access_indexes=[0]
)
```

### **Incorrect Operation Name**

```python
result = nectar_client.byoc_query(
    mean_func,
    bucket_ids=[bucket_ids[0]],
    operation="variance",
    policy_indexes=[0],
    use_allowlists=[True],
    access_indexes=[0]
)
```

