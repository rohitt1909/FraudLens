
import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "fraudlens.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():

    # Read analyzed transaction data
    df = pd.read_csv(
        DB_PATH.parent / "analyzed_transactions.csv"
    )

    # Connect to SQLite database
    conn = get_connection()

    try:
        # Store transactions in SQL table
        df.to_sql(
            "transactions",
            conn,
            if_exists="replace",
            index=False
        )

        # Create indexes for faster queries
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

        print("Database created successfully!")

        # Count total transactions
        result = conn.execute("""
            SELECT COUNT(*) FROM transactions
        """).fetchone()

        print("Total stored transactions:", result[0])

        # Display risk distribution
        print("\nRisk distribution from SQL:")

        results = conn.execute("""
            SELECT risk_level, COUNT(*) AS total
            FROM transactions
            GROUP BY risk_level
            ORDER BY total DESC
        """).fetchall()

        for row in results:
            print(row[0], ":", row[1])

        # Calculate total suspicious transaction amount
        suspicious_amount = conn.execute("""
            SELECT SUM(amount)
            FROM transactions
            WHERE fraud_alert = 1
        """).fetchone()[0]

        print(
            "\nTotal suspicious transaction amount:",
            f"INR {suspicious_amount:,.2f}"
        )

    finally:
        conn.close()


if __name__ == "__main__":
    initialize_database()
