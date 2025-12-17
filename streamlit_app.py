# Path: frontend/streamlit_app.py

import streamlit as st
import pandas as pd
import os
import sys

# Allow backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import controller

st.set_page_config(
    page_title="Finance Transaction Analyzer",
    layout="wide"
)

st.title("📊 Finance Transaction Analyzer (FTA)")
st.markdown("---")

# --- Sidebar ---
st.sidebar.header("Configuration")
st.sidebar.info("🏦 **Designed for Bank of India (BOI) statements only (for now)**")

# --- Step 1: Upload ---
st.header("1️⃣ Upload Bank Statement")

uploaded_file = st.file_uploader(
    "Upload Bank Statement (PDF, CSV, Excel)",
    type=["pdf", "csv", "xlsx", "xls"]
)

if uploaded_file:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()

    # Process file only once per upload
    if (
        "current_file" not in st.session_state
        or st.session_state["current_file"] != uploaded_file.name
    ):
        with st.spinner("Parsing and cleaning data..."):
            try:
                result = controller.process_file(uploaded_file, file_ext)
                st.session_state["current_df"] = result["df"]
                st.session_state["session_id"] = result["session_id"]
                st.session_state["csv_path"] = result["csv_path"]
                st.session_state["current_file"] = uploaded_file.name
                st.success("File processed successfully!")
            except Exception as e:
                st.error(f"Processing failed: {e}")

    # --- Step 2: Preview ---
    if "current_df" in st.session_state:
        df = st.session_state["current_df"]

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("2️⃣ Data Preview")
            st.dataframe(df.head(10), width='stretch')
            st.caption(
                f"Rows: {len(df)} | Columns: {list(df.columns)}"
            )

        with col2:

            with open(st.session_state["csv_path"], "rb") as f:
                st.download_button(
                    "⬇️ Download Cleaned CSV",
                    f,
                    file_name="cleaned_transactions.csv",
                    mime="text/csv"
                )

        st.markdown("---")

        # --- Step 3: Load to Database ---
        st.subheader("3️⃣ Load to Analytics Database")

        if st.button("🚀 Load Data to DB"):
            with st.spinner("Loading data into analytics tables..."):
                success, msg = controller.load_to_database(
                    df=df,
                    table_name=None,  # ignored
                    session_id=st.session_state["session_id"],
                    filename=uploaded_file.name,
                    csv_path=st.session_state["csv_path"]
                )

                if success:
                    st.balloons()
                    st.success(msg)
                else:
                    st.error(msg)
