#!/bin/bash
set -e

echo "========= Installing dependencies ========="
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "========= Starting FastAPI (internal) ========="
python -m uvicorn backend.api:app --host 127.0.0.1 --port 9000 &

echo "========= Starting Streamlit (public) ========="
python -m streamlit run frontend/Home.py \
  --server.port ${PORT} \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --server.enableXsrfProtection false

echo "========= Startup Complete ========="
