import os
import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ===== ENV VARIABLES =====
DB_SERVER = os.getenv("DB_SERVER")        # e.g. financeanalytics.database.windows.net
DB_NAME = os.getenv("DB_NAME")            # e.g. finance_analytics_db
DB_USER = os.getenv("DB_USER")            # e.g. developer
DB_PASSWORD = os.getenv("DB_PASSWORD")    # your password
DB_DRIVER = os.getenv("DB_DRIVER")        # e.g. ODBC Driver 18 for SQL Server

# ===== SAFETY CHECK =====
missing = [k for k, v in {
    "DB_SERVER": DB_SERVER,
    "DB_NAME": DB_NAME,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_DRIVER": DB_DRIVER,
}.items() if not v]

if missing:
    raise RuntimeError(f"Missing environment variables: {missing}")

# ===== ODBC CONNECTION STRING =====
odbc_str = (
    f"DRIVER={{{DB_DRIVER}}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=30;"
)

params = urllib.parse.quote_plus(odbc_str)

# ===== SQLALCHEMY ENGINE =====
engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={params}",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    future=True,
)

# ===== SESSION FACTORY =====
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ===== SIMPLE HEALTH CHECK =====
def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Azure SQL connection OK")
    except Exception as e:
        print("❌ Azure SQL connection FAILED")
        raise e


# Run directly for testing
if __name__ == "__main__":
    test_connection()
