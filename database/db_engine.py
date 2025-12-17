# Path: database/db_engine.py
# Oracle DBMS version - NO AUTO TABLE CREATION

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String,
    Numeric, Date, DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Oracle connection details
DB_USER = os.getenv("DB_USER", "SYSTEM")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "1521")
DB_SERVICE = os.getenv("DB_SERVICE", "FREE")

from urllib.parse import quote_plus

# Oracle connection string with URL-encoded password
encoded_password = quote_plus(DB_PASSWORD)
ORACLE_CONNECTION_STRING = (
    f"oracle+oracledb://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/?service_name={DB_SERVICE}"
)

engine = create_engine(
    ORACLE_CONNECTION_STRING,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set True for SQL debugging
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class FactTransaction(Base):
    """
    Model matches existing Oracle table structure.
    txn_id is IDENTITY column - Oracle handles it automatically.
    """
    __tablename__ = "fact_transactions"

    txn_id = Column(Integer, primary_key=True)  # Oracle IDENTITY - no insert needed

    session_id = Column(String(64), index=True)
    txn_date = Column(Date)

    transaction_ref_id = Column(String(100))
    transaction_code = Column(String(50))
    transaction_method = Column(String(50))
    transaction_category = Column(String(50))
    transaction_nature = Column(String(50))

    counterparty_name = Column(String(255))
    counterparty_bank_code = Column(String(20))

    debit = Column(Numeric(15, 2))
    credit = Column(Numeric(15, 2))
    amount = Column(Numeric(15, 2))
    balance = Column(Numeric(15, 2))

    remarks = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """
    REMOVED: Table creation logic.
    Tables already exist in Oracle - created via SQL script.
    This function kept for compatibility but does nothing.
    """
    pass  # Tables pre-exist in Oracle