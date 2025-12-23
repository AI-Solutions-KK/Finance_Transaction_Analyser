# tools/load_all_tables.py
import pandas as pd
from sqlalchemy import text
from database.connection import engine

# -----------------------------
# SAME RULES AS ORACLE PHASE
# -----------------------------
CATEGORY_RULES = {
    "EMI": ["emi"],
    "FOOD": ["hotel", "food", "restaurant"],
    "SHOPPING": ["amazon", "flipkart", "mall"],
    "UTILITY": ["electric", "mobile", "bill", "recharge"],
    "MEDICAL": ["hospital", "medical"],
    "INVESTMENT": ["mutual", "sip", "policy", "lic"],
    "TRANSFER": ["transfer", "self"],
    "REFUND": ["refund"]
}

BANK_CODES = ["BOI", "HDFC", "SBI", "AXIS", "ICICI", "YES", "KOTAK"]

# -----------------------------
# HELPERS
# -----------------------------
def detect_category(remarks: str) -> str:
    r = remarks.lower()
    for cat, keys in CATEGORY_RULES.items():
        if any(k in r for k in keys):
            return cat
    return "OTHER"

def detect_nature(debit: float, credit: float) -> str:
    if credit > 0 and debit == 0:
        return "INCOME"
    if debit > 0 and credit == 0:
        return "EXPENSE"
    return "TRANSFER"

def extract_bank_code(remarks: str) -> str:
    for bank in BANK_CODES:
        if f"/{bank}/" in remarks.upper():
            return bank
    return "UNKNOWN"

def extract_counterparty(remarks: str) -> str:
    parts = remarks.split("/")
    return parts[3] if len(parts) > 3 else "UNKNOWN"

#
# MAIN LOADER (FIXED)
# -----------------------------
# MAIN LOADER (FIXED)
# -----------------------------
def load_all_tables(csv_path: str, session_id: str):
    df = pd.read_csv(csv_path)

    df["remarks"] = df["remarks"].fillna("").astype(str)
    df["debit"] = df.get("debit", 0).fillna(0)
    df["credit"] = df.get("credit", 0).fillna(0)
    df["balance"] = df.get("balance", 0).fillna(0)

    df["txn_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df = df.dropna(subset=["txn_date"])

    with engine.begin() as conn:
        for _, row in df.iterrows():
            remarks = row["remarks"]

            parts = remarks.split("/") if remarks else []

            transaction_ref_id = parts[1] if len(parts) > 1 else None
            transaction_code = parts[0] if len(parts) > 0 else "UNKNOWN"
            counterparty = parts[3] if len(parts) > 3 else "UNKNOWN"
            bank_code = parts[4] if len(parts) > 4 else "UNKNOWN"

            conn.execute(
                text("""
                    INSERT INTO dbo.fact_transactions (
                        session_id,
                        txn_date,
                        transaction_ref_id,
                        transaction_code,
                        transaction_method,
                        transaction_category,
                        transaction_nature,
                        counterparty_name,
                        counterparty_bank_code,
                        debit,
                        credit,
                        amount,
                        balance,
                        remarks,
                        created_at
                    )
                    VALUES (
                        :session_id,
                        :txn_date,
                        :ref_id,
                        :code,
                        :method,
                        :category,
                        :nature,
                        :counterparty,
                        :bank_code,
                        :debit,
                        :credit,
                        :amount,
                        :balance,
                        :remarks,
                        GETDATE()
                    )
                """),
                {
                    "session_id": session_id,
                    "txn_date": row["txn_date"],
                    "ref_id": transaction_ref_id,          # ✅ FIXED
                    "code": transaction_code,
                    "method": "UPI" if "UPI" in transaction_code.upper() else "BANK",
                    "category": detect_category(remarks),
                    "nature": detect_nature(row["debit"], row["credit"]),
                    "counterparty": counterparty,
                    "bank_code": bank_code,
                    "debit": float(row["debit"]),
                    "credit": float(row["credit"]),
                    "amount": float(row["credit"]) - float(row["debit"]),
                    "balance": float(row["balance"]),
                    "remarks": remarks,
                }
            )
