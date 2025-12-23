# Path: backend/main.py

import os
import uuid
import shutil
from sqlalchemy import text

from tools.tools import DataTransformer
from database.connection import engine


class BackendService:
    def __init__(self):
        self.transformer = DataTransformer()

    # -------------------------------------------------
    # FILE PROCESSING
    # -------------------------------------------------
    def process_file(self, uploaded_file, file_ext):
        session_id = str(uuid.uuid4())

        temp_dir = os.path.join("uploaded_data", session_id)
        os.makedirs(temp_dir, exist_ok=True)

        temp_path = os.path.join(temp_dir, f"raw{file_ext}")

        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        df = self.transformer.parse_file(temp_path, file_ext)
        csv_path = self.transformer.export_csv(df, session_id)

        return {
            "df": df,
            "session_id": session_id,
            "csv_path": csv_path,
        }

    # -------------------------------------------------
    # LOAD DATA INTO AZURE SQL
    # -------------------------------------------------
    def load_to_database(self, session_id, csv_path):
        try:
            # 🔧 LAZY IMPORT (fixes your error)
            from tools.load_all_tables import load_all_tables

            load_all_tables(
                csv_path=csv_path,
                session_id=session_id
            )

            return True, "✅ Analytics loaded into Azure SQL successfully"

        except Exception as e:
            import traceback
            print("=" * 80)
            print("AZURE SQL LOAD ERROR")
            print(traceback.format_exc())
            print("=" * 80)
            return False, f"❌ Load failed: {str(e)}"

    # -------------------------------------------------
    # CLEAR DATABASE
    # -------------------------------------------------
    def clear_database(self):
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM FACT_TRANSACTIONS"))

            if os.path.exists("uploaded_data"):
                shutil.rmtree("uploaded_data")

            return True

        except Exception as e:
            raise e


# -------------------------------------------------
# SINGLETON FACTORY (CRITICAL FIX)
# -------------------------------------------------
_backend_instance = None


def get_backend_service():
    global _backend_instance
    if _backend_instance is None:
        _backend_instance = BackendService()
    return _backend_instance
