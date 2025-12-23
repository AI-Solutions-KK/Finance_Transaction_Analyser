# Path: frontend/Home.py

import streamlit as st
import os
import sys

# -------------------------------------------------
# Allow backend imports (DO NOT CHANGE PATH LOGIC)
# -------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 🔧 FIX: controller is now created via factory
from backend.main import get_backend_service
from tools.cleanup_utils import cleanup_session_data, get_active_sessions

# Create backend service instance (same role as old controller)
controller = get_backend_service()

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Finance Transaction Analyzer",
    layout="wide"
)

st.title("📊 Finance Transaction Analytics (FTA)")
st.markdown("---")

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.header("Configuration")
st.sidebar.info("🏦 Designed for **Bank of India (BOI)** statements")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Flow")

st.sidebar.markdown(
    """
<div style="font-size:14px; line-height:1.6;">
<div> 1️⃣ 📤 <b>Upload Statement</b> &nbsp;➡️</div>
<div style="margin-left:80px;">│</div>
<div> 2️⃣ 👁️ <b>Preview Transactions</b> &nbsp;➡️</div>
<div style="margin-left:80px;">│</div>
<div> 3️⃣ 📊 <b>Load Analytics</b> &nbsp;➡️</div>
<div style="margin-left:80px;">│</div>
<div> 4️⃣ 📈 <b>View Dashboard</b> &nbsp;➡️</div>
</div>
""",
    unsafe_allow_html=True
)

# -------------------------------------------------
# SESSION STATE INIT
# -------------------------------------------------
SESSION_KEYS = [
    "current_file",
    "current_df",
    "session_id",
    "csv_path",
    "db_loaded"
]

for key in SESSION_KEYS:
    if key not in st.session_state:
        st.session_state[key] = None

# -------------------------------------------------
# CLEANUP OPTIONS (SIDEBAR)
# -------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 🧹 Data Management")

# Option 1: Clear current session only
if st.sidebar.button("🔄 Clear Current Session"):
    if st.session_state["session_id"]:
        success, msg = cleanup_session_data(session_id=st.session_state["session_id"])
        if success:
            for key in SESSION_KEYS:
                st.session_state[key] = None
            st.success("✅ Current session cleared")
        else:
            st.error(f"❌ {msg}")
    else:
        st.warning("No active session to clear")
    st.rerun()

# Option 2: Clear ALL data
if st.sidebar.button("🗑️ Clear All Data", type="secondary"):
    success, msg = cleanup_session_data(cleanup_all=True)
    if success:
        for key in SESSION_KEYS:
            st.session_state[key] = None
        st.success("✅ All data cleared from database and files")
    else:
        st.error(f"❌ {msg}")
    st.rerun()

# Show active sessions
with st.sidebar.expander("📊 Active Sessions"):
    sessions = get_active_sessions()
    if sessions:
        for s in sessions:
            st.text(f"ID: {s['session_id'][:8]}...")
            st.caption(f"Records: {s['record_count']} | Last: {s['last_upload']}")
    else:
        st.caption("No active sessions")

# -------------------------------------------------
# STEP 1: UPLOAD
# -------------------------------------------------
st.header("1️⃣ Upload Bank Statement")

uploaded_file = st.file_uploader(
    "Upload Bank Statement (PDF, CSV, Excel)",
    type=["pdf", "csv", "xlsx", "xls"]
)

st.caption("— OR —")

if st.button("📄 Use Default Sample Statement"):
    sample_path = os.path.join(
        os.path.dirname(__file__),
        "samples",
        "sample_statement.pdf"
    )

    with open(sample_path, "rb") as f:
        class DummyUpload:
            def __init__(self, file):
                self.file = file
                self.name = "sample_statement.pdf"

            def getbuffer(self):
                return self.file.read()

        uploaded_file = DummyUpload(f)
        file_ext = ".pdf"

        # Reset state like a fresh upload
        st.session_state["current_file"] = uploaded_file.name
        st.session_state["db_loaded"] = False

        with st.spinner("Loading sample statement..."):
            result = controller.process_file(uploaded_file, file_ext)
            st.session_state["current_df"] = result["df"]
            st.session_state["session_id"] = result["session_id"]
            st.session_state["csv_path"] = result["csv_path"]

        st.success("✅ Sample statement loaded")



if uploaded_file:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()

    if st.session_state["current_file"] != uploaded_file.name:
        st.session_state["current_file"] = uploaded_file.name
        st.session_state["db_loaded"] = False

        with st.spinner("Parsing and cleaning statement..."):
            try:
                result = controller.process_file(uploaded_file, file_ext)
                st.session_state["current_df"] = result["df"]
                st.session_state["session_id"] = result["session_id"]
                st.session_state["csv_path"] = result["csv_path"]
                st.success("✅ Statement processed successfully")
            except Exception as e:
                st.error(f"❌ Processing failed: {e}")

# -------------------------------------------------
# STEP 2: PREVIEW
# -------------------------------------------------
if st.session_state["current_df"] is not None:
    df = st.session_state["current_df"]

    st.markdown("---")
    st.subheader("2️⃣ Data Preview")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.dataframe(df.head(10), use_container_width=True)
        st.caption(f"Rows: {len(df)} | Columns: {list(df.columns)}")

    with col2:
        with open(st.session_state["csv_path"], "rb") as f:
            st.download_button(
                "⬇️ Download Cleaned CSV",
                f,
                file_name="cleaned_transactions.csv",
                mime="text/csv"
            )

# -------------------------------------------------
# STEP 3: LOAD ANALYTICS
# -------------------------------------------------
if st.session_state["current_df"] is not None and not st.session_state["db_loaded"]:
    st.markdown("---")
    st.subheader("3️⃣ 📊 Load Analytics")

    st.info("💡 **Tip**: Use 'Clear All Data' in sidebar before loading new statement to avoid mixing data")

    if st.button("📊 Load Analytics"):
        with st.spinner("Loading analytics data..."):
            success, msg = controller.load_to_database(
                session_id=st.session_state["session_id"],
                csv_path=st.session_state["csv_path"]
            )

            if success:
                st.session_state["db_loaded"] = True
                st.success(msg)
            else:
                st.error(msg)

# -------------------------------------------------
# STEP 4: VIEW DASHBOARD
# -------------------------------------------------
if st.session_state["db_loaded"]:
    st.markdown("---")
    st.subheader("4️⃣ 📈 View Dashboard")

    if st.button("📈 View Dashboard"):
        st.switch_page("pages/2_Analytics_Dashboard.py")
