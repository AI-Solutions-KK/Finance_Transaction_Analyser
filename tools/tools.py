import pandas as pd
import numpy as np
import pdfplumber
import re
import os
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from database.db_engine import Base, SessionLocal

# NOTE: Removed UploadAudit model and table creation
# Oracle tables are pre-created via SQL script

class DataTransformer:
    """
    Handles Parsing, Cleaning, and Normalizing Data.
    Target: Dashboard-ready format.
    """

    CANONICAL_MAP = {
        'date': 'transaction_date',
        'txn date': 'transaction_date',
        'value date': 'value_date',
        'particulars': 'description',
        'narrative': 'description',
        'desc': 'description',
        'withdrawal': 'debit',
        'dr': 'debit',
        'deposit': 'credit',
        'cr': 'credit',
        'bal': 'balance',
        'ref': 'reference_no',
        'chq': 'cheque_no'
    }

    def __init__(self):
        pass

    def parse_file(self, file_path: str, file_ext: str) -> pd.DataFrame:
        """Dispatcher for file parsing"""
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)
        elif file_ext == '.pdf':
            df = self._parse_pdf(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_ext}")

        return self._clean_dataframe(df)

    def _parse_pdf(self, path: str) -> pd.DataFrame:
        """
        Heuristic PDF Parser using pdfplumber.
        Attempts to find table structures.
        """
        all_rows = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                # 1. Try extract_table (works if lines are drawn)
                table = page.extract_table()
                if table:
                    all_rows.extend(table)
                else:
                    # 2. Fallback: Extract text and try basic splitting (very naive)
                    text_content = page.extract_text()
                    if text_content:
                        lines = text_content.split('\n')
                        for line in lines:
                            # Split by multiple spaces
                            parts = re.split(r'\s{2,}', line.strip())
                            if len(parts) > 2:  # Ignore noise
                                all_rows.append(parts)

        if not all_rows:
            return pd.DataFrame()

        # Promote first row to header if it looks like one
        headers = all_rows[0]
        data = all_rows[1:]
        df = pd.DataFrame(data, columns=headers)
        return df

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies cleaning rules to make data BI-ready.
        """
        # 1. Normalize Headers
        df.columns = [str(c).strip().lower().replace('.', '') for c in df.columns]
        df.rename(columns=lambda x: self.CANONICAL_MAP.get(x, x), inplace=True)

        # 2. Remove purely empty rows/cols
        df.dropna(how='all', inplace=True)

        # 3. Standardize Dates
        if 'transaction_date' in df.columns:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')

        # 4. Standardize Numbers (Remove commas, currency symbols)
        num_cols = ['debit', 'credit', 'balance', 'amount']
        for col in num_cols:
            if col in df.columns:
                df[col] = (
                    df[col].astype(str)
                    .str.replace(',', '', regex=False)
                    .str.replace('$', '', regex=False)
                    .str.replace('Cr', '', regex=False)  # Common banking notation
                    .str.replace('Dr', '', regex=False)
                )
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        # 5. Calculation: Fill Nulls & Ensure logic
        # If Debit/Credit exist, create Net Amount
        if 'debit' in df.columns and 'credit' in df.columns:
            df['net_amount'] = df['credit'] - df['debit']
            df['transaction_type'] = df.apply(
                lambda x: 'Credit' if x['credit'] > 0 else ('Debit' if x['debit'] > 0 else 'Neutral'), axis=1
            )

        # 6. Drop Rows without critical data (Date)
        if 'transaction_date' in df.columns:
            df = df.dropna(subset=['transaction_date'])

        return df

    def generate_schema_manifest(self, df: pd.DataFrame) -> dict:
        """Returns a JSON-compatible schema description"""
        schema = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            if 'datetime' in dtype:
                schema[col] = 'TIMESTAMP'
            elif 'float' in dtype or 'int' in dtype:
                schema[col] = 'NUMERIC'
            else:
                schema[col] = 'TEXT'
        return schema

    def export_csv(self, df: pd.DataFrame, session_id: str) -> str:
        """Saves transform to specific folder"""
        output_dir = os.path.join("uploaded_data", session_id)
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, "cleaned_data.csv")
        df.to_csv(path, index=False)
        return path