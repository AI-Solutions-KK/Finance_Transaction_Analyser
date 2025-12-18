# Path: frontend/Home.py

import streamlit as st
import os
import sys

# -------------------------------------------------
# Allow backend imports
# -------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.main import controller

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Finance Transaction Analyzer",
    layout="wide"
)

st.title("📊 Finance Transaction Analyzer (FTA)")
st.markdown("---")

# -------------------------------------------------
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

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
🧹 **Before a new upload:**  
Clear the session to reset analytics.
"""
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
# CLEAR SESSION (WORKING - DO NOT TOUCH)
# -------------------------------------------------
st.sidebar.markdown("---")
if st.sidebar.button("🧹 Clear Session"):
    for key in SESSION_KEYS:
        st.session_state[key] = None
    st.success("Session cleared. Upload a new statement.")
    st.rerun()

# -------------------------------------------------
# STEP 1: UPLOAD
# -------------------------------------------------
st.header("1️⃣ Upload Bank Statement")

uploaded_file = st.file_uploader(
    "Upload Bank Statement (PDF, CSV, Excel)",
    type=["pdf", "csv", "xlsx", "xls"]
)

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
                st.success("Statement processed successfully")
            except Exception as e:
                st.error(f"Processing failed: {e}")

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
# -------------------------------------------------
# STEP 3: LOAD ANALYTICS
# -------------------------------------------------
# STEP 3: LOAD ANALYTICS
# -------------------------------------------------
if st.session_state["current_df"] is not None and not st.session_state["db_loaded"]:
    st.markdown("---")
    st.subheader("3️⃣ 📊 Load Analytics")

    if st.button("📊 Load Analytics"):
        with st.spinner("Loading analytics data..."):
            success, msg = controller.load_to_database(
                df=st.session_state["current_df"],
                table_name=None,
                session_id=st.session_state["session_id"],
                filename=st.session_state["current_file"],
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
# STEP 4: VIEW DASHBOARD
# -------------------------------------------------
if st.session_state["db_loaded"]:
    st.markdown("---")
    st.subheader("4️⃣ 📈 View Dashboard")

    if st.button("📈 View Dashboard"):
        st.switch_page("pages/2_Analytics_Dashboard.py")
