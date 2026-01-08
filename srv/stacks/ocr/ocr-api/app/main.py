from fastapi import FastAPI, File, UploadFile
import shutil
import os

UPLOAD_DIR = "/app/uploads"
RESULT_DIR = "/app/results"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

app = FastAPI(title="OCR API")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Aquí iría enqueue al worker
    return {"filename": file.filename, "status": "uploaded"}

@app.get("/results/{filename}")
def get_result(filename: str):
    path = os.path.join(RESULT_DIR, filename)
    if not os.path.exists(path):
        return {"status": "not ready"}
    return {"filename": filename, "status": "done"}
