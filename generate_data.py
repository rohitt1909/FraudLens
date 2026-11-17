
import pandas as pd
import numpy as np
from pathlib import Path

# Random seed for reproducible results
np.random.seed(42)

# Number of transactions
n = 10000

# Generate transaction data
data = {
    "transaction_id": [f"TXN{i:06d}" for i in range(1, n + 1)],

    "customer_id": np.random.randint(1001, 2001, n),

    "amount": np.round(
        np.random.lognormal(8, 1.5, n), 2
    ),

    "transaction_type": np.random.choice(
        ["UPI", "NEFT", "IMPS", "Card", "ATM"], n
    ),

    "location": np.random.choice(
        ["Mumbai", "Delhi", "Pune", "Bangalore",
         "Chennai", "Hyderabad"], n
    ),

    "hour": np.random.randint(0, 24, n),

    "device_known": np.random.choice(
        [1, 0], n, p=[0.90, 0.10]
    ),

    "location_known": np.random.choice(
        [1, 0], n, p=[0.85, 0.15]
    ),

    "failed_attempts": np.random.poisson(0.5, n),

    "transactions_last_hour": np.random.poisson(2, n),

    "average_customer_spend": np.round(
        np.random.uniform(500, 20000, n), 2
    )
}

# Convert data into a DataFrame
df = pd.DataFrame(data)

# Simulate fraudulent transactions
df["is_fraud"] = np.random.choice(
    [0, 1], n, p=[0.95, 0.05]
)

# Add suspicious patterns to some fraud transactions
fraud_indices = df.index[df["is_fraud"] == 1]

for i in fraud_indices:
    pattern = np.random.choice(
        ["high_amount", "unknown_device",
         "rapid_transactions", "failed_attempts"]
    )

    if pattern == "high_amount":
        df.loc[i, "amount"] = np.random.uniform(
            100000, 500000
        )

    elif pattern == "unknown_device":
        df.loc[i, "device_known"] = 0
        df.loc[i, "location_known"] = 0

    elif pattern == "rapid_transactions":
        df.loc[i, "transactions_last_hour"] = \
            np.random.randint(10, 30)

    elif pattern == "failed_attempts":
        df.loc[i, "failed_attempts"] = \
            np.random.randint(5, 15)

# Round transaction amounts
df["amount"] = df["amount"].round(2)

# Create data directory
Path("data").mkdir(exist_ok=True)

# Save dataset
df.to_csv("data/transactions.csv", index=False)

# Display results
print("Dataset generated successfully!")
print("Total transactions:", len(df))
print("Fraudulent transactions:", df["is_fraud"].sum())
print("Normal transactions:", (df["is_fraud"] == 0).sum())
print("\nSample transactions:")
print(df.head())

