from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import shutil, os, redis, uuid
from fastapi.middleware.cors import CORSMiddleware

UPLOAD_DIR = "/app/uploads"
RESULT_DIR = "/app/results"
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

app = FastAPI(title="OCR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://ui.solsticio.local"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Upload
# -----------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    allowed_ext = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="Formato no soportado")
    
    job_id = str(uuid.uuid4())
    stored_filename = f"{job_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    job_data = {
        "job_id": job_id,
        "filename": file.filename,
        "stored_filename": stored_filename,
        "filepath": file_path,
        "status": "queued"
    }
    redis_client.lpush("ocr_queue", job_id)
    redis_client.hset(f"job:{job_id}", mapping=job_data)
    
    return {"job_id": job_id, "filename": file.filename, "status": "queued"}

# -----------------------------
# Estado de un trabajo
# -----------------------------
@app.get("/status/{job_id}")
def get_status(job_id: str):
    job_info = redis_client.hgetall(f"job:{job_id}")
    if not job_info:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    result_path = os.path.join(RESULT_DIR, f"{job_id}.txt")
    status = "completed" if os.path.exists(result_path) else job_info.get("status", "processing")
    
    return {"job_id": job_id, "filename": job_info.get("filename"), "status": status}

# -----------------------------
# Listar todos los trabajos en curso
# -----------------------------
@app.get("/jobs/queued")
def get_all_jobs():
    keys = redis_client.keys("job:*")
    jobs = []
    for k in keys:
        j = redis_client.hgetall(k)
        # Safely get the job_id with .get() method to avoid KeyError
        job_id = j.get("job_id")
        if not job_id:
            continue  # Skip invalid entries
        
        result_path = os.path.join(RESULT_DIR, f"{job_id}.txt")
        jobs.append({
            "job_id": job_id,
            "filename": j.get("filename", ""),
            "status": "completed" if os.path.exists(result_path) else j.get("status", "queued")
        })
    return jobs

# -----------------------------
# Listar todos los resultados disponibles
# -----------------------------
@app.get("/results")
def get_all_results():
    results = []
    for f in os.listdir(RESULT_DIR):
        if f.endswith(".txt"):
            # Extract job_id from filename (remove .txt extension)
            job_id = f.replace(".txt", "")
            job_info = redis_client.hgetall(f"job:{job_id}")
            results.append({
                "job_id": job_id,
                "filename": job_info.get("filename", f"{job_id}.txt"),
                "download_url": f"/results/download/{job_id}"
            })
    return results

# -----------------------------
# Obtener contenido de resultado
# -----------------------------
@app.get("/results/{job_id}")
def get_result(job_id: str):
    result_path = os.path.join(RESULT_DIR, f"{job_id}.txt")
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Resultado no disponible")
    
    with open(result_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"job_id": job_id, "content": content, "status": "completed"}

# -----------------------------
# Descargar archivo con nombre original
# -----------------------------
@app.get("/results/download/{job_id}")
def download_result(job_id: str):
    result_path = os.path.join(RESULT_DIR, f"{job_id}.txt")
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Resultado no disponible")
    
    job_info = redis_client.hgetall(f"job:{job_id}")
    # Devolver .txt con el nombre original + .txt
    filename = job_info.get("filename", f"{job_id}.txt") if job_info else f"{job_id}.txt"
    # Ensure filename ends with .txt
    if not filename.endswith(".txt"):
        filename = f"{filename}.txt"
    
    return FileResponse(result_path, media_type="text/plain", filename=filename)

# -----------------------------
# Health check
# -----------------------------
@app.get("/health")
def health():
    try:
        redis_health = "ok" if redis_client.ping() else "error"
    except:
        redis_health = "error"
    
    return {
        "status": "ok",
        "redis": redis_health,
        "upload_dir": os.path.isdir(UPLOAD_DIR),
        "result_dir": os.path.isdir(RESULT_DIR)
    }

# -----------------------------
# Debug endpoint (optional - can be removed in production)
# -----------------------------
@app.get("/debug/redis/{job_id}")
def debug_redis(job_id: str):
    job_info = redis_client.hgetall(f"job:{job_id}")
    return {"exists": bool(job_info), "data": job_info}