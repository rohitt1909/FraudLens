
from fraud_engine import evaluate_transaction


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


# Test 1: Normal transaction

def test_normal_transaction():

    result = evaluate_transaction(normal_transaction())

    assert result["risk_score"] == 0
    assert result["risk_level"] == "Low"
    assert result["fraud_alert"] == 0


# Test 2: High transaction amount

def test_high_amount():

    transaction = normal_transaction()
    transaction["amount"] = 150000

    result = evaluate_transaction(transaction)

    assert "R001" in result["triggered_rules"]
    assert result["fraud_alert"] == 1


# Test 3: Unknown device

def test_unknown_device():

    transaction = normal_transaction()
    transaction["device_known"] = 0

    result = evaluate_transaction(transaction)

    assert result["risk_score"] == 20
    assert "R002" in result["triggered_rules"]


# Test 4: Unknown location

def test_unknown_location():

    transaction = normal_transaction()
    transaction["location_known"] = 0

    result = evaluate_transaction(transaction)

    assert result["risk_score"] == 20
    assert "R003" in result["triggered_rules"]


# Test 5: Multiple failed attempts

def test_failed_attempts():

    transaction = normal_transaction()
    transaction["failed_attempts"] = 5

    result = evaluate_transaction(transaction)

    assert result["risk_score"] == 30
    assert result["risk_level"] == "Medium"
    assert result["fraud_alert"] == 1


# Test 6: Rapid transactions

def test_rapid_transactions():

    transaction = normal_transaction()
    transaction["transactions_last_hour"] = 10

    result = evaluate_transaction(transaction)

    assert result["risk_score"] == 30
    assert "R005" in result["triggered_rules"]


# Test 7: Unusual spending

def test_unusual_spending():

    transaction = normal_transaction()
    transaction["amount"] = 30000

    result = evaluate_transaction(transaction)

    assert result["risk_score"] == 25
    assert "R006" in result["triggered_rules"]


# Test 8: Unusual transaction time

def test_unusual_time():

    transaction = normal_transaction()
    transaction["hour"] = 2

    result = evaluate_transaction(transaction)

    assert result["risk_score"] == 10
    assert "R007" in result["triggered_rules"]


# Test 9: Multiple fraud indicators

def test_high_risk_transaction():

    transaction = {
        "amount": 250000,
        "hour": 2,
        "device_known": 0,
        "location_known": 0,
        "failed_attempts": 6,
        "transactions_last_hour": 12,
        "average_customer_spend": 5000
    }

    result = evaluate_transaction(transaction)

    assert result["risk_level"] == "High"
    assert result["risk_score"] == 100
    assert result["fraud_alert"] == 1


# Test 10: Risk score boundary

def test_high_risk_boundary():

    transaction = normal_transaction()
    transaction["failed_attempts"] = 5
    transaction["transactions_last_hour"] = 10

    result = evaluate_transaction(transaction)

    assert result["risk_score"] == 60
    assert result["risk_level"] == "High"


# Test 11: Amount threshold boundary

def test_amount_boundary():

    transaction = normal_transaction()
    transaction["amount"] = 100000
    transaction["average_customer_spend"] = 50000

    result = evaluate_transaction(transaction)

    assert "R001" not in result["triggered_rules"]


# Test 12: Failed attempts boundary

def test_failed_attempts_boundary():

    transaction = normal_transaction()
    transaction["failed_attempts"] = 4

    result = evaluate_transaction(transaction)

    assert result["risk_score"] == 0
    assert result["fraud_alert"] == 0
