# Path: tools/cleanup_utils.py

import os
import shutil
from sqlalchemy import text
from database.connection import engine


def cleanup_session_data(session_id=None, cleanup_all=False):
    """
    Cleans database records and uploaded files.

    Args:
        session_id (str): specific session to clean
        cleanup_all (bool): wipe everything

    Returns:
        (success: bool, message: str)
    """
    try:
        with engine.begin() as conn:
            if cleanup_all:
                result = conn.execute(
                    text("DELETE FROM FACT_TRANSACTIONS")
                )
                deleted = result.rowcount

            elif session_id:
                result = conn.execute(
                    text(
                        "DELETE FROM FACT_TRANSACTIONS WHERE session_id = :sid"
                    ),
                    {"sid": session_id}
                )
                deleted = result.rowcount
            else:
                return False, "No cleanup option provided"

        # ---------- FILE SYSTEM CLEANUP ----------
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        uploaded_dir = os.path.join(base_dir, "uploaded_data")

        if cleanup_all and os.path.exists(uploaded_dir):
            shutil.rmtree(uploaded_dir)
            os.makedirs(uploaded_dir, exist_ok=True)

        elif session_id:
            session_dir = os.path.join(uploaded_dir, session_id)
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)

        return True, f"Cleanup completed ({deleted} records removed)"

    except Exception as e:
        return False, f"Cleanup failed: {str(e)}"


def get_active_sessions():
    """
    Returns active session summary for sidebar.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        session_id,
                        COUNT(*) AS record_count,
                        MIN(txn_date) AS first_upload,
                        MAX(txn_date) AS last_upload
                    FROM FACT_TRANSACTIONS
                    GROUP BY session_id
                    ORDER BY last_upload DESC
                """)
            )

            sessions = []
            for row in result:
                sessions.append({
                    "session_id": row.session_id,
                    "record_count": row.record_count,
                    "first_upload": row.first_upload,
                    "last_upload": row.last_upload,
                })

            return sessions

    except Exception:
        return []
