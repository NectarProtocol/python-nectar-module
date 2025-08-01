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

```python
bucket_ids = nectar_client.get_bucket_ids()
```

---
## Functions

### Aggregate Types: Linear Regression, Mean, Count, Variance, Minimum, Maximum, Sum

#### **Use Case 1: Linear Regression analysis**

The `linear_regression_func` method performs a simple linear regression analysis on worker data, predicting **height** based on **heart rate** and **age**.

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
**Returns a dictionary containing:**
- **`coef`**: The regression coefficients for "heart_rate" and "age" (list).
- **`intercept`**: The y-intercept of the regression line (float).
- **`count`**: Total number of **age** records.

---
#### **Use Case 2: Counting records**

The `count_func` method calculates the total number of records (rows) in the **worker-data.csv** file.

```python
def count_func():
    import pandas as pd
    df = pd.read_csv("/app/data/worker-data.csv")
    return {"count": len(df)}
```
**Returns:**
- **`count`**: The total number of records.

---
#### **Use Case 3: Calculating Mean age**

The `mean_func` method calculates the **average age** of workers and the total number of records.


```python
def mean_func():
    import pandas as pd
    df = pd.read_csv("/app/data/worker-data.csv")
    count = len(df)
    mean = df['age'].mean()
    return {"count": count, "mean": mean}
```
**Returns:**
- **`count`**: Total number of records.
- **`mean`**: Average age of workers.

---
#### **Use Case 4: Calculating Variance of age**

The `variance_func` method calculates the **total number of records**, the **average age**, and the **variance of age**.

```python
def variance_func():
    import pandas as pd
    df = pd.read_csv("/app/data/worker-data.csv")
    count = len(df)
    mean = df['age'].mean()
    variance = df['age'].var()
    return {"count": count, "mean": mean, "variance": variance}
```
**Returns:**
- **`count`**: Total number of records.
- **`mean`**: Average age of workers.
- **`variance`**: Variance of the age column.

```python
def pre_compute_count_func():
    import pandas as pd
    df = pd.read_csv("/app/data/worker-data.csv")
    return {"count": len(df)}
```
**Returns:**
- **`count`**:  Total number of records.


```python
def main_count_func(list_of_partial_result):
    total_count = sum(d["count"] for d in list_of_partial_result)
    return {"total_count": total_count}
```
**Returns:**
- **`sum`**: Total value  of avg_heart_rate
- **`count`**:  Total number of records.

```python
def main_mean_func(list_of_partial_result):
    total_heart = sum(d.get("sum", 0) for d in list_of_partial_result)
    total_count = sum(d.get("count", 0) for d in list_of_partial_result)
    return {
        "avg_heart_rate": total_heart / total_count if total_count else 0,
        "total_count": total_count
    }
```
**Returns:**
- **`avg_heart_rate`**: Return average of avg_heart_rate
- **`total_count`**:  Total number of records.

```python
def pre_compute_variance_func():
    import pandas as pd
    df = pd.read_csv("/app/data/worker-data.csv")
    count = len(df)
    if count == 0:
        return {"count": 0, "sum": 0.0, "sum_sq": 0.0}
    sum_age = df['age'].sum()
    sum_sq_age = (df['age'] ** 2).sum()

    return {"count": count, "sum": sum_age, "sum_sq": sum_sq_age}
```
**Returns:**
- **`count`**: Total number of records.
- **`sum`**:   Total sum of the age values
- **`sum_sq`**:Total sum of squared age values

```python
def main_variance_func(list_of_partial_result):
    total_count = sum(d["count"] for d in list_of_partial_result)
    if total_count == 0:
        return {"count": 0, "mean": 0.0, "variance": 0.0}

    total_sum = sum(d["sum"] for d in list_of_partial_result)
    total_sum_sq = sum(d["sum_sq"] for d in list_of_partial_result)

    mean = total_sum / total_count
    # Công thức variance = (Σx² / n) − mean²
    variance = (total_sum_sq / total_count) - (mean ** 2)

    return {"count": total_count, "mean": mean, "variance": variance}
```
**Returns:**
- **`count`**: Total number of records.
- **`mean`**:  Total sum of the age values.
- **`sum_sq`**: Total sum of squared age values.


```python
def pre_compute_linear_regression_func():
    import pandas as pd
    df = pd.read_csv("/app/data/worker-data.csv")
    df_filtered = df[df['age'] > 10]
    return {
        "X": df_filtered[["heart_rate", "age"]].values.tolist(),
        "Y": df_filtered["height"].values.tolist(),
        "count": len(df_filtered),
    }
```
**Returns:**
- **`X`**: The feature matrix (list of [heart_rate, age]) after filtering on the worker.
- **`Y`**: The target values (height) corresponding to the features.
- **`count`**: The number of records in the filtered dataset on this worker.

```python
def main_linear_regression_func(list_of_partial_result):
    from sklearn.linear_model import LinearRegression
    import numpy as np

    # Combine X và Y từ tất cả workers
    X_all, Y_all = [], []
    total_count = 0

    for part in list_of_partial_result:
        X_all.extend(part["X"])
        Y_all.extend(part["Y"])
        total_count += part["count"]

    if total_count == 0:
        return {"coef": [], "intercept": 0.0, "count": 0}

    # Train linear regression trên dữ liệu gộp
    X_train = np.array(X_all)
    Y_train = np.array(Y_all)

    model = LinearRegression()
    model.fit(X_train, Y_train)

    return {
        "coef": model.coef_.tolist(),
        "intercept": float(model.intercept_),
        "count": total_count,
    }
```
**Returns:**
- **`coef`**: The list of coefficients learned by the linear regression model.
- **`intercept`**: The intercept (bias) term of the linear regression model.
- **`count`**: The total number of records aggregated from all workers used in training.


```python
def main_compute_node_count_func(list_of_partial_result):
    all_data = pd.concat(list_of_partial_result, ignore_index=True)

    return {
        "total_count": len(all_data)
    }
```
**Returns:**
- **`total_count`**: Total number of records.



```python
def main_compute_node_mean_func(list_of_partial_result):
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
**Returns:**
- **`count`**: Total number of records.
- **`mean`**: Average age of workers.

```python
def main_compute_node_variance_func(list_of_partial_result):
    import pandas as pd
    
    all_data = pd.concat(list_of_partial_result, ignore_index=True)

    total_count = len(all_data)
    if total_count == 0:
        return {"count": 0, "mean": 0.0, "variance": 0.0}

    mean_age = all_data['age'].mean()
    variance_age = all_data['age'].var(ddof=0) 

    return {
        "count": int(total_count),
        "mean": float(mean_age),
        "variance": float(variance_age),
    }
```
**Returns:**
- **`count`**: Total number of records.
- **`mean`**: Average age of workers.
- **`variance`**: Variance of the age column.

```python
def main_comppute_node_linear_regression_func(list_of_partial_result):
    import pandas as pd
    from sklearn.linear_model import LinearRegression

    # Gộp tất cả raw DataFrame từ workers
    all_data = pd.concat(list_of_partial_result, ignore_index=True)

    # Lọc dữ liệu và loại bỏ NaN
    df_filtered = all_data[all_data['age'] > 10].dropna(subset=["heart_rate", "age", "height"])

    total_count = len(df_filtered)
    if total_count == 0:
        return {"coef": [], "intercept": 0.0, "count": 0}

    X_train = df_filtered[["heart_rate", "age"]]
    Y_train = df_filtered["height"]

    model = LinearRegression()
    model.fit(X_train, Y_train)

    return {
        "coef": model.coef_.tolist(),
        "intercept": float(model.intercept_),
        "count": int(total_count),
    }
```
**Returns a dictionary containing:**
- **`coef`**: The regression coefficients for "heart_rate" and "age" (list).
- **`intercept`**: The y-intercept of the regression line (float).
- **`count`**: Total number of **age** records.

## Queries

### Single Data Node

```python
result = nectar_client.byoc_query(                                                                 
    main_func=linear_regression_func,                                                         # Custom function to execute(e.g.,a count or aggregation - one of Aggregate Types)
    bucket_ids=[82907351435983860892388544000730676991410427895802844146331593263117007585780], # List of data bucket IDs to query
    policy_indexes=[0]                                                                          # Indexes of access policies for each bucket
)
```

```python
result = nectar_client.byoc_query(
    main_func=count_func,                                                                      # Custom function to execute(e.g.,a count or aggregation - one of Aggregate Types)
    bucket_ids=[82907351435983860892388544000730676991410427895802844146331593263117007585780] # List of data bucket IDs to query
    policy_indexes=[0],                                                                        # Indexes of access policies for each bucket
)
```

```python
result = nectar_client.byoc_query(
    main_func=mean_func,                                                                       
    bucket_ids=[82907351435983860892388544000730676991410427895802844146331593263117007585780] # List of data bucket IDs to query
    policy_indexes=[0],                                                                        # Indexes of access policies for each bucket
)
```

```python
result = nectar_client.byoc_query(
    main_func=variance_func,                                                                   
    bucket_ids=[82907351435983860892388544000730676991410427895802844146331593263117007585780] # List of data bucket IDs to query
    policy_indexes=[0],                                                                        # Indexes of access policies for each bucket
)
```

### Multiple Data Nodes and Compute on Scheduler Client

```python
result = nectar_client.byoc_query(
    pre_compute_func = pre_compute_count_func,   
    main_func=main_count_func,                  
    is_separate_data = True,                   
    bucket_ids=[9689146321410733197144258861072383043162670963292692165216323769409616974260,47158569605347845291258717936608941587831527325131971018140298621183841813182],
    policy_indexes=[0, 0],                     
)
```

```python
result = nectar_client.byoc_query(
    pre_compute_func = pre_compute_mean_func,   
    main_func=main_mean_func,                  
    is_separate_data = True,                   
    bucket_ids=[9689146321410733197144258861072383043162670963292692165216323769409616974260,47158569605347845291258717936608941587831527325131971018140298621183841813182],
    policy_indexes=[0, 0],                     
)
```

```python
result = nectar_client.byoc_query(
    pre_compute_func = pre_compute_variance_func, 
    main_func=main_variance_func,                            
    is_separate_data = True,                        
    bucket_ids=[9689146321410733197144258861072383043162670963292692165216323769409616974260,47158569605347845291258717936608941587831527325131971018140298621183841813182],
    policy_indexes=[0, 0],                     

)
```

```python
result = nectar_client.byoc_query(
    pre_compute_func = pre_compute_linear_regression_func,   # pre_compute_func needs to be provided to perform aggregation on the worker 
    main_func=main_linear_regression_func,                   # Custom function to execute (e.g., a count or aggregation - one of Aggregate Types)
    is_separate_data = True,                          # this param is used to indicate that the DA will combine data on the client side, and an additional 
    bucket_ids=[9689146321410733197144258861072383043162670963292692165216323769409616974260,47158569605347845291258717936608941587831527325131971018140298621183841813182],
    policy_indexes=[0, 0],                      # Indexes of access policies for each bucket
)
```

```python
result = nectar_client.byoc_query(
    main_func=variance_func,                                  # Custom aggregation function to be executed (e.g., variance, count, sum)
    bucket_ids=[bucket_ids[0], bucket_ids[1]],      # List of bucket IDs containing the data to query
    policy_indexes=[0, 0],                          # Indexes of the policies to apply for each respective bucket

)

```

### Multiple Data Nodes and Compute on Compute Node

```python
result = nectar_client.byoc_query(    
    main_func=main_compute_node_count_func,  
    is_separate_data = False,                
    bucket_ids=[9689146321410733197144258861072383043162670963292692165216323769409616974260,47158569605347845291258717936608941587831527325131971018140298621183841813182],
    policy_indexes=[0, 0],                    
)
```

```python
result = nectar_client.byoc_query(    
    main_func=main_compute_node_mean_func,  
    is_separate_data = False,                
    bucket_ids=[9689146321410733197144258861072383043162670963292692165216323769409616974260,47158569605347845291258717936608941587831527325131971018140298621183841813182],
    policy_indexes=[0, 0],                    
)
```

```python
result = nectar_client.byoc_query(    
    main_func=main_compute_node_variance_func,   # Custom function to execute (e.g., a count or aggregation - one of Aggregate Types)
    is_separate_data = False,                # this param is used to indicate that the DA will combine data on the Compute Node
    bucket_ids=[9689146321410733197144258861072383043162670963292692165216323769409616974260,47158569605347845291258717936608941587831527325131971018140298621183841813182],
    policy_indexes=[0, 0],                      # Indexes of access policies for each bucket
)
```

```python
result = nectar_client.byoc_query(    
    main_func=main_comppute_node_linear_regression_func,   # Custom function to execute (e.g., a count or aggregation - one of Aggregate Types)
    is_separate_data = False,                # this param is used to indicate that the DA will combine data on the Compute Node
    bucket_ids=[9689146321410733197144258861072383043162670963292692165216323769409616974260,47158569605347845291258717936608941587831527325131971018140298621183841813182],
    policy_indexes=[0, 0],                      # Indexes of access policies for each bucket
)
```


### **Parameters**

| Parameter        | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| `<your function>` | A user-defined Python function (e.g., `lambda df: df.count()` - one of Aggregate Types) to run over the datasets. |
| `bucket_ids`      | List of bucket IDs (strings or ints) to query from.                          |
| `policy_indexes`  | A list of integers referencing policy positions matching each bucket.        |

---

```python
print(result)
```

---
## Exception handling

### **Bucket ID does not exist**

```python
bucket_not_exist = "30551459429423590702715106722240816746282150213228561545827912304803497819734"
```

```python
result = nectar_client.byoc_query(
    main_func=variance_func,
    bucket_ids=[bucket_not_exist],
    policy_indexes=[0],
)
```

### **Incorrect operation name**

```python
result = nectar_client.byoc_query(
    main_func=mean_func,
    bucket_ids=[bucket_ids[0]],
    policy_indexes=[0],
)
```


## Refer to the example in the sample folder

```python
test_da_exception_case.ipynb
test_da_exception_case.ipynb
```