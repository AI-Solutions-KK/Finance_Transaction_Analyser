from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from backend.main import get_backend_service

app = FastAPI(
    title="Finance Transaction Analyzer API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

backend = get_backend_service()


@app.get("/")
def health():
    return {"status": "OK", "message": "Backend running"}


@app.post("/process")
def process_file(
    file: UploadFile = File(...),
    file_ext: str = Form(...)
):
    result = backend.process_file(file, file_ext)
    return {
        "session_id": result["session_id"],
        "rows": len(result["df"]),
        "csv_path": result["csv_path"]
    }


@app.post("/load")
def load_to_db(
    session_id: str = Form(...),
    csv_path: str = Form(...)
):
    success, message = backend.load_to_database(session_id, csv_path)
    return {"success": success, "message": message}


@app.post("/clear")
def clear_db():
    backend.clear_database()
    return {"status": "cleared"}
