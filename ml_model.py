
import pandas as pd
import numpy as np
import sqlite3
import json

from database import DB_PATH

# Load analyzed transactions
df = pd.read_csv("data/analyzed_transactions.csv")

# Split data into training and testing sets
train = df.sample(frac=0.8, random_state=42)
test = df.drop(train.index)

features = [
    "amount",
    "failed_attempts",
    "transactions_last_hour"
]

# Learn statistical baselines from training data
baseline = {}

for feature in features:
    values = np.log1p(train[feature])

    baseline[feature] = {
        "mean": float(values.mean()),
        "std": float(values.std())
    }


def anomaly_score(data):

    scores = []

    for feature in features:

        mean = baseline[feature]["mean"]
        std = baseline[feature]["std"]

        z_score = (
            np.log1p(data[feature]) - mean
        ) / max(std, 0.000001)

        scores.append(z_score.clip(lower=0))

    return np.max(np.column_stack(scores), axis=1)


# Calculate anomaly threshold using training data
train_scores = anomaly_score(train)
threshold = float(np.percentile(train_scores, 95))

# Calculate anomaly scores
df["anomaly_score"] = anomaly_score(df).round(4)

# Flag unusual transactions
df["statistical_anomaly"] = (
    df["anomaly_score"] > threshold
).astype(int)

# Combine rule alerts and statistical alerts
df["combined_alert"] = (
    (df["fraud_alert"] == 1) |
    (df["statistical_anomaly"] == 1)
).astype(int)


def evaluate(actual, predicted, name):

    tp = int(((actual == 1) & (predicted == 1)).sum())
    tn = int(((actual == 0) & (predicted == 0)).sum())
    fp = int(((actual == 0) & (predicted == 1)).sum())
    fn = int(((actual == 1) & (predicted == 0)).sum())

    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)

    f1 = (
        2 * precision * recall /
        max(precision + recall, 0.000001)
    )

    accuracy = (tp + tn) / len(actual)

    print(f"\n{name}")
    print("-" * 35)
    print(f"Accuracy:  {accuracy:.2%}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall:    {recall:.2%}")
    print(f"F1 Score:  {f1:.2%}")

    print("True Positives:", tp)
    print("True Negatives:", tn)
    print("False Positives:", fp)
    print("False Negatives:", fn)


# Evaluate only on held-out test data
test_results = df.loc[test.index]

evaluate(
    test_results["is_fraud"],
    test_results["fraud_alert"],
    "Rule Engine Performance"
)

evaluate(
    test_results["is_fraud"],
    test_results["statistical_anomaly"],
    "Statistical Model Performance"
)

evaluate(
    test_results["is_fraud"],
    test_results["combined_alert"],
    "Combined Detection Performance"
)

# Save statistical model
with open("data/anomaly_model.json", "w") as file:
    json.dump({
        "baseline": baseline,
        "threshold": threshold
    }, file, indent=4)

# Save final dataset
df.to_csv(
    "data/final_transactions.csv",
    index=False
)

# Update SQLite database
conn = sqlite3.connect(DB_PATH)

try:
    df.to_sql(
        "transactions",
        conn,
        if_exists="replace",
        index=False
    )

    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_transaction_id
        ON transactions(transaction_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_risk_level
        ON transactions(risk_level)
    """)

    conn.commit()

finally:
    conn.close()

print("\nFinal Results")
print("-" * 35)
print("Total transactions:", len(df))
print("Rule-based alerts:", df["fraud_alert"].sum())
print("Statistical anomalies:", df["statistical_anomaly"].sum())
print("Combined alerts:", df["combined_alert"].sum())

print("\nAnomaly model and database saved successfully!")
