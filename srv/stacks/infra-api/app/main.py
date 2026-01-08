from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from pydantic import BaseModel
import docker, os, subprocess, time, psutil
from typing import Optional

API_TOKEN = os.getenv("INFRA_API_TOKEN")
STACKS_PATH = "/srv/stacks"
TTL_DEFAULT = int(os.getenv("TEST_CONTAINER_TTL", "3600"))

if not API_TOKEN:
    raise RuntimeError("INFRA_API_TOKEN no definido")

client = docker.from_env()
app = FastAPI(title="Infra API")

def auth(authorization: Optional[str] = Header(None)):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

class BuildReq(BaseModel):
    path: str
    tag: str

class DeployReq(BaseModel):
    stack: str

class RollbackReq(BaseModel):
    stack: str
    tag: str

def stack_path(stack):
    path = f"{STACKS_PATH}/{stack}"
    if not os.path.isdir(path):
        raise HTTPException(400, "Stack inválido")
    return path

def cleanup(name):
    try:
        c = client.containers.get(name)
        c.stop()
        c.remove(force=True)
    except:
        pass

@app.get("/containers", dependencies=[Depends(auth)])
def containers():
    return [{"name": c.name, "status": c.status} for c in client.containers.list(all=True)]

@app.post("/containers/{name}/start", dependencies=[Depends(auth)])
def start(name): client.containers.get(name).start(); return {"ok": True}

@app.post("/containers/{name}/stop", dependencies=[Depends(auth)])
def stop(name): client.containers.get(name).stop(); return {"ok": True}

@app.delete("/containers/{name}", dependencies=[Depends(auth)])
def delete(name): client.containers.get(name).remove(force=True); return {"ok": True}

@app.post("/containers/{name}/test", dependencies=[Depends(auth)])
def test(name, bg: BackgroundTasks, ttl: int = TTL_DEFAULT):
    now = int(time.time())
    exp = now + ttl
    c = client.containers.get(name)
    c.start()
    c.update(labels={**c.labels, "mode": "test", "expires_at": str(exp)})
    bg.add_task(lambda: (time.sleep(ttl), cleanup(name)))
    return {"expires_at": exp}

@app.post("/build", dependencies=[Depends(auth)])
def build(req: BuildReq, bg: BackgroundTasks):
    bg.add_task(lambda: client.images.build(path=req.path, tag=req.tag))
    return {"status": "build queued"}

@app.post("/deploy", dependencies=[Depends(auth)])
def deploy(req: DeployReq, bg: BackgroundTasks):
    path = stack_path(req.stack)
    bg.add_task(lambda: subprocess.run(["docker", "compose", "up", "-d"], cwd=path))
    return {"status": "deploy queued"}

@app.post("/rollback", dependencies=[Depends(auth)])
def rollback(req: RollbackReq):
    subprocess.run(
        ["docker", "compose", "up", "-d"],
        cwd=stack_path(req.stack),
        env={**os.environ, "IMAGE_TAG": req.tag}
    )
    return {"ok": True}

@app.post("/cleanup/tests", dependencies=[Depends(auth)])
def cleanup_tests():
    now = int(time.time())
    removed = []
    for c in client.containers.list(all=True, filters={"label": "mode=test"}):
        if int(c.labels.get("expires_at", 0)) < now:
            cleanup(c.name)
            removed.append(c.name)
    return {"removed": removed}

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/metrics", dependencies=[Depends(auth)])
def metrics():
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "containers": len(client.containers.list())
    }
