
import pytest
from app import app


@pytest.fixture
def client():

    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def normal_transaction():

    return {
        "amount": 2000,
        "hour": 14,
        "device_known": 1,
        "location_known": 1,
        "failed_attempts": 0,
        "transactions_last_hour": 2,
        "average_customer_spend": 5000
    }


# Test 1: API availability

def test_api_home(client):

    response = client.get("/")

    assert response.status_code == 200
    assert response.json["project"] == "FraudLens"


# Test 2: Dashboard statistics

def test_stats(client):

    response = client.get("/api/stats")

    assert response.status_code == 200
    assert response.json["total_transactions"] == 10000
    assert response.json["combined_alerts"] == 1468


# Test 3: Transaction retrieval

def test_transactions(client):

    response = client.get("/api/transactions")

    assert response.status_code == 200
    assert len(response.json) > 0
    assert len(response.json) <= 100


# Test 4: High-risk filtering

def test_high_risk_filter(client):

    response = client.get(
        "/api/transactions?risk=High"
    )

    assert response.status_code == 200
    assert len(response.json) > 0

    for transaction in response.json:
        assert transaction["risk_level"] == "High"


# Test 5: Invalid risk filter

def test_invalid_risk_filter(client):

    response = client.get(
        "/api/transactions?risk=Invalid"
    )

    assert response.status_code == 400


# Test 6: Fraud alerts

def test_alerts(client):

    response = client.get("/api/alerts")

    assert response.status_code == 200
    assert len(response.json) > 0

    for transaction in response.json:
        assert transaction["combined_alert"] == 1


# Test 7: Risk distribution

def test_risk_distribution(client):

    response = client.get(
        "/api/risk-distribution"
    )

    assert response.status_code == 200

    total = sum(
        row["total"] for row in response.json
    )

    assert total == 10000


# Test 8: Normal transaction analysis

def test_normal_analysis(client):

    response = client.post(
        "/api/analyze",
        json=normal_transaction()
    )

    assert response.status_code == 200
    assert response.json["risk_level"] == "Low"
    assert response.json["risk_score"] == 0


# Test 9: Suspicious transaction analysis

def test_suspicious_analysis(client):

    transaction = normal_transaction()

    transaction.update({
        "amount": 250000,
        "hour": 2,
        "device_known": 0,
        "location_known": 0,
        "failed_attempts": 6,
        "transactions_last_hour": 12
    })

    response = client.post(
        "/api/analyze",
        json=transaction
    )

    assert response.status_code == 200
    assert response.json["risk_level"] == "High"
    assert response.json["risk_score"] == 100
    assert response.json["combined_alert"] == 1


# Test 10: Missing required fields

def test_missing_fields(client):

    response = client.post(
        "/api/analyze",
        json={"amount": 5000}
    )

    assert response.status_code == 400


# Test 11: Negative transaction amount

def test_negative_amount(client):

    transaction = normal_transaction()
    transaction["amount"] = -5000

    response = client.post(
        "/api/analyze",
        json=transaction
    )

    assert response.status_code == 400


# Test 12: Invalid transaction hour

def test_invalid_hour(client):

    transaction = normal_transaction()
    transaction["hour"] = 25

    response = client.post(
        "/api/analyze",
        json=transaction
    )

    assert response.status_code == 400


# Test 13: Invalid device status

def test_invalid_device(client):

    transaction = normal_transaction()
    transaction["device_known"] = 5

    response = client.post(
        "/api/analyze",
        json=transaction
    )

    assert response.status_code == 400


# Test 14: Dashboard availability

def test_dashboard(client):

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"FraudLens" in response.data
