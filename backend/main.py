# Path: backend/main.py

import os
import uuid
import shutil
from sqlalchemy import text

from tools.tools import DataTransformer
from tools.load_all_tables import load_all_tables
from database.db_engine import engine


class BackendController:
    def __init__(self):
        self.transformer = DataTransformer()

    # -------------------------------------------------
    # FILE PROCESSING
    # -------------------------------------------------
    def process_file(self, uploaded_file, file_ext):
        """
        1. Save uploaded file
        2. Parse & clean
        3. Export CSV
        4. Return dataframe + metadata
        """
        session_id = str(uuid.uuid4())

        # Create session folder
        temp_dir = os.path.join("uploaded_data", session_id)
        os.makedirs(temp_dir, exist_ok=True)

        temp_path = os.path.join(temp_dir, f"raw{file_ext}")

        # Save uploaded file
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Parse & clean
        df = self.transformer.parse_file(temp_path, file_ext)

        # Export cleaned CSV
        csv_path = self.transformer.export_csv(df, session_id)

        return {
            "df": df,
            "session_id": session_id,
            "csv_path": csv_path,
        }

    # -------------------------------------------------
    # LOAD TO ORACLE DATABASE
    # -------------------------------------------------
    def load_to_database(self, df, table_name, session_id, filename, csv_path):
        """
        Loads data into existing Oracle FACT_TRANSACTIONS table.
        Table structure must already exist in Oracle DB.
        """
        try:
            load_all_tables(
                csv_path=csv_path,
                session_id=session_id
            )
            return True, f"✅ Loaded {len(df)} transactions into Oracle successfully"

        except Exception as e:
            import traceback
            print("=" * 80)
            print("ORACLE INSERT ERROR - FULL TRACEBACK:")
            print(traceback.format_exc())
            print("=" * 80)

            return False, f"❌ Oracle Insert Error: {str(e)}"

    # -------------------------------------------------
    # CLEAR SESSION / DATABASE
    # -------------------------------------------------
    def clear_database(self):
        """
        Clears analytics data ONLY.
        Does NOT drop tables.
        Safe to reuse application.
        """
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM C##FINANCE.FACT_TRANSACTIONS"))

            # Optional: clean uploaded files
            if os.path.exists("uploaded_data"):
                shutil.rmtree("uploaded_data")

            return True

        except Exception as e:
            import traceback
            print("=" * 80)
            print("DATABASE CLEAR ERROR:")
            print(traceback.format_exc())
            print("=" * 80)
            raise e


# -------------------------------------------------
# SINGLETON CONTROLLER
# -------------------------------------------------
controller = BackendController()
