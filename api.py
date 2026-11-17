
from flask import Flask, jsonify, request
import sqlite3
import json
import math

from database import DB_PATH
from fraud_engine import evaluate_transaction

app = Flask(__name__)

with open("data/anomaly_model.json") as file:
    anomaly_model = json.load(file)


def query_database(query, params=()):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@app.route("/")
def home():
    return jsonify({
        "project": "FraudLens",
        "status": "API running",
        "version": "1.0"
    })


@app.route("/api/stats")
def stats():

    result = query_database("""
        SELECT
            COUNT(*) AS total_transactions,
            SUM(fraud_alert) AS rule_alerts,
            SUM(statistical_anomaly) AS anomalies,
            SUM(combined_alert) AS combined_alerts,
            SUM(CASE WHEN risk_level = 'High'
                THEN 1 ELSE 0 END) AS high_risk,
            SUM(CASE WHEN combined_alert = 1
                THEN amount ELSE 0 END)
                AS suspicious_amount
        FROM transactions
    """)

    return jsonify(result[0])


@app.route("/api/transactions")
def transactions():

    risk = request.args.get("risk", "All")

    if risk not in ["All", "Low", "Medium", "High"]:
        return jsonify({"error": "Invalid risk level"}), 400

    if risk == "All":
        result = query_database("""
            SELECT * FROM transactions
            ORDER BY risk_score DESC
            LIMIT 100
        """)
    else:
        result = query_database("""
            SELECT * FROM transactions
            WHERE risk_level = ?
            ORDER BY risk_score DESC
            LIMIT 100
        """, (risk,))

    return jsonify(result)


@app.route("/api/alerts")
def alerts():

    result = query_database("""
        SELECT * FROM transactions
        WHERE combined_alert = 1
        ORDER BY risk_score DESC
        LIMIT 100
    """)

    return jsonify(result)


@app.route("/api/analyze", methods=["POST"])
def analyze():

    data = request.get_json(silent=True)

    required_fields = [
        "amount",
        "hour",
        "device_known",
        "location_known",
        "failed_attempts",
        "transactions_last_hour",
        "average_customer_spend"
    ]

    if not isinstance(data, dict):
        return jsonify({"error": "JSON object required"}), 400

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Missing field: {field}"
            }), 400

        value = data[field]

        if (
            type(value) not in (int, float)
            or not math.isfinite(value)
            or value < 0
        ):
            return jsonify({
                "error": f"Invalid value: {field}"
            }), 400

    for field in [
        "hour", "device_known", "location_known",
        "failed_attempts", "transactions_last_hour"
    ]:
        if data[field] != int(data[field]):
            return jsonify({
                "error": f"{field} must be an integer"
            }), 400

    if (
        data["hour"] > 23
        or data["device_known"] not in [0, 1]
        or data["location_known"] not in [0, 1]
        or data["average_customer_spend"] <= 0
    ):
        return jsonify({
            "error": "Invalid transaction details"
        }), 400

    # Evaluate rule-based fraud risk
    result = evaluate_transaction(data)

    # Evaluate statistical anomaly score
    scores = []

    for feature, values in anomaly_model["baseline"].items():

        score = (
            math.log1p(data[feature]) - values["mean"]
        ) / max(values["std"], 0.000001)

        scores.append(max(score, 0))

    anomaly_score = round(max(scores), 4)

    statistical_anomaly = int(
        anomaly_score > anomaly_model["threshold"]
    )

    result["anomaly_score"] = anomaly_score
    result["statistical_anomaly"] = statistical_anomaly

    result["combined_alert"] = int(
        result["fraud_alert"] == 1
        or statistical_anomaly == 1
    )

    return jsonify(result)


@app.route("/api/risk-distribution")
def risk_distribution():

    result = query_database("""
        SELECT risk_level, COUNT(*) AS total
        FROM transactions
        GROUP BY risk_level
    """)

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
