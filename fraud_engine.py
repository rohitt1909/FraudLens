
import pandas as pd


def evaluate_transaction(transaction):

    risk_score = 0
    triggered_rules = []

    # Rule 1: High transaction amount
    if transaction["amount"] > 100000:
        risk_score += 30
        triggered_rules.append("R001: High transaction amount")

    # Rule 2: Unknown device
    if transaction["device_known"] == 0:
        risk_score += 20
        triggered_rules.append("R002: Unknown device")

    # Rule 3: Unknown location
    if transaction["location_known"] == 0:
        risk_score += 20
        triggered_rules.append("R003: Unknown location")

    # Rule 4: Multiple failed attempts
    if transaction["failed_attempts"] >= 5:
        risk_score += 30
        triggered_rules.append("R004: Multiple failed attempts")

    # Rule 5: Rapid transactions
    if transaction["transactions_last_hour"] >= 10:
        risk_score += 30
        triggered_rules.append("R005: Rapid transactions")

    # Rule 6: Unusual spending
    if transaction["amount"] > (
        transaction["average_customer_spend"] * 5
    ):
        risk_score += 25
        triggered_rules.append("R006: Unusual spending")

    # Rule 7: Unusual transaction time
    if 0 <= transaction["hour"] < 5:
        risk_score += 10
        triggered_rules.append("R007: Unusual transaction time")

    # Limit risk score to 100
    risk_score = min(risk_score, 100)

    # Classify transaction risk
    if risk_score >= 60:
        risk_level = "High"
    elif risk_score >= 30:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "triggered_rules": " | ".join(triggered_rules),
        "fraud_alert": int(risk_score >= 30)
    }


if __name__ == "__main__":

    # Load transaction dataset
    df = pd.read_csv("data/transactions.csv")

    # Evaluate every transaction
    results = df.apply(
        evaluate_transaction, axis=1
    ).apply(pd.Series)

    # Combine original data with risk results
    df = pd.concat([df, results], axis=1)

    # Save analyzed transactions
    df.to_csv(
        "data/analyzed_transactions.csv",
        index=False
    )

    print("Fraud detection completed!")
    print("Total transactions:", len(df))
    print("Suspicious transactions:", df["fraud_alert"].sum())

    print("\nRisk distribution:")
    print(df["risk_level"].value_counts())

    print("\nSample results:")
    print(df[[
        "transaction_id",
        "amount",
        "risk_score",
        "risk_level",
        "fraud_alert"
    ]].head(10))
