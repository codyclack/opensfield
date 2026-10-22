"""OpenSfield API + static UI.

Run (mock mode, default):   uv run uvicorn app.main:app --port 8765
Real runs (later):          OPENSFIELD_MODE=comfy COMFY_BASE_URL=... uv run --extra comfy uvicorn app.main:app
"""
from __future__ import annotations

import json
import os
import secrets
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import assets, fx, runner
from .registry import MEDIA, ROOT, STUDIO_ORDER, load_features

MODE = os.environ.get("OPENSFIELD_MODE", "mock")  # mock | comfy
PARTNER = os.environ.get("OPENSFIELD_PARTNER") != "0"  # partner-model tools (Comfy Cloud API nodes) are on by default; set OPENSFIELD_PARTNER=0 to hide
STATIC = Path(__file__).parent / "static"

if MODE not in ("mock", "comfy"):
    raise SystemExit(f"OPENSFIELD_MODE must be mock or comfy, got {MODE!r}")

app = FastAPI(title="OpenSfield")
FEATURES = {f["id"]: f for f in load_features()}
LOCK = threading.Lock()
JOBS_FILE = Path(os.environ.get("OPENSFIELD_JOBS_FILE", runner.OUTPUTS / "jobs.json"))  # generation history survives restarts (the Generations gallery reads it)
CREATED_THIS_RUN = 0


def _load_jobs() -> dict[str, dict]:
    try:
        jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    for j in jobs.values():
        if j["status"] in ("queued", "running"):  # the server stopped mid-job
            j.update(status="error", error="interrupted: the server restarted")
    return jobs


def _save_jobs():
    runner.OUTPUTS.mkdir(parents=True, exist_ok=True)
    tmp = JOBS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(JOBS), encoding="utf-8")
    tmp.replace(JOBS_FILE)


JOBS: dict[str, dict] = _load_jobs()
POOL = ThreadPoolExecutor(max_workers=1)  # one GPU: renders are serialized
runner.UPLOADS.mkdir(parents=True, exist_ok=True)


@app.middleware("http")
async def access_gate(request: Request, call_next):
    """Optional shared-secret gate for a public deployment: set OPENSFIELD_ACCESS_KEY, share /?key=<value> once (it sets a cookie)."""
    key = os.environ.get("OPENSFIELD_ACCESS_KEY")
    if not key:
        return await call_next(request)
    given = request.query_params.get("key", "")
    if not (secrets.compare_digest(request.cookies.get("osf", ""), key) or secrets.compare_digest(given, key)):
        return JSONResponse({"detail": "access key required: open the link you were given"}, status_code=401)
    resp = await call_next(request)
    if given:
        resp.set_cookie("osf", key, httponly=True, samesite="lax")
    return resp


class JobRequest(BaseModel):
    feature_id: str
    inputs: dict = {}
    project: str | None = None  # Cinema Studio project the result is filed under


class JobPatch(BaseModel):
    fav: bool | None = None
    project: str | None = None


class ProjectRequest(BaseModel):
    name: str


def _public(feature: dict) -> dict:
    return {k: v for k, v in feature.items() if k != "workflow"}


@app.get("/api/config")
def config():
    return {"mode": MODE, "partner_enabled": PARTNER, "studios": STUDIO_ORDER, "features": len(FEATURES),
            "mock_notice": "Mock mode: no ComfyUI calls are made." if MODE == "mock" else None}


@app.get("/api/features")
def features():
    return [_public(f) for f in FEATURES.values() if PARTNER or f["track"] != "partner"]


@app.get("/api/apps")
def apps():
    """Higgsfield's Apps catalog as OpenSfield apps: each points at the tool that runs it (registry/apps.py)."""
    from registry.apps import APPS, CATEGORIES
    out = []
    for a in APPS:
        fid = a["feature"] if a["mode"] == "tool" else f"app.{a['slug']}"
        f = FEATURES.get(fid)
        if not f or (f["track"] == "partner" and not PARTNER and a["mode"] != "pair"):
            fid = f"app.{a['slug']}-open" if f"app.{a['slug']}-open" in FEATURES else fid
            f = FEATURES.get(fid)
        if not f:
            continue
        examples = (f.get("workflow") or {}).get("examples") or (FEATURES.get(f"app.{a['slug']}-open", {}).get("workflow") or {}).get("examples", [])
        out.append({"slug": a["slug"], "name": a["name"], "cat": a["cat"], "desc": a["desc"], "tag": a["tag"], "mode": a["mode"],
                    "feature": fid, "preset": a.get("preset", {}), "status": f["status"], "output_kind": f["output_kind"],
                    "examples": list(examples)})
    return {"categories": CATEGORIES, "apps": out}


@app.get("/api/features/{feature_id}")
def feature(feature_id: str):
    f = FEATURES.get(feature_id)
    if not f:
        raise HTTPException(404, "unknown feature")
    return _public(f)


@app.post("/api/uploads")
async def upload(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()[:8]
    name = f"{uuid.uuid4().hex}{ext}"
    (runner.UPLOADS / name).write_bytes(await file.read())
    return {"id": name, "name": file.filename, "url": f"/outputs/uploads/{name}"}


def _update(job_id: str):
    def update(**kw):
        with LOCK:
            JOBS[job_id].update(kw)
            if "status" in kw:
                _save_jobs()
    return update


def _execute(job_id: str):
    job = JOBS[job_id]
    feature = FEATURES[job["feature_id"]]
    update = _update(job_id)
    update(status="running", started=time.time())
    try:
        # CPU effects never touch ComfyUI, so they run for real in every mode whenever the fx extra is installed
        step = runner.run_mock if MODE == "mock" else runner.run_comfy
        run = runner.run_local if feature.get("local") and fx.cv2 is not None \
            else (lambda f, j, u: runner.run_pipeline(f, j, u, step)) if feature.get("pipeline") else step
        outputs = run(feature, job, update)
        update(status="done", outputs=outputs, progress=1.0, finished=time.time())
    except Exception as e:  # surfaced to the UI, not swallowed
        update(status="error", error=str(e), finished=time.time())


@app.post("/api/jobs", status_code=202)
def create_job(req: JobRequest):
    f = FEATURES.get(req.feature_id)
    if not f:
        raise HTTPException(404, "unknown feature")
    if f["track"] == "partner" and not PARTNER:
        raise HTTPException(403, "partner pack is disabled (set OPENSFIELD_PARTNER=1 (default on; 0 hides))")
    cap = int(os.environ.get("OPENSFIELD_MAX_JOBS", "0"))  # 0 = unlimited; protects credits on a public link
    global CREATED_THIS_RUN
    if cap and CREATED_THIS_RUN >= cap:
        raise HTTPException(429, f"this demo allows {cap} runs per server start; it has reached the limit")
    missing = [i["label"] for i in f["inputs"] if i.get("required") and not req.inputs.get(i["name"])]
    if missing:
        raise HTTPException(422, f"missing required input(s): {', '.join(missing)}")
    for i in f["inputs"]:  # media inputs must be upload ids we issued, never paths
        v = req.inputs.get(i["name"])
        if i["kind"] in MEDIA and v and (Path(v).name != v or not (runner.UPLOADS / v).exists()):
            raise HTTPException(422, f"{i['label']}: unknown upload")
    job = {"id": uuid.uuid4().hex[:12], "feature_id": f["id"], "feature_name": f["name"], "kind": f["output_kind"], "status": "queued",
           "progress": 0.0, "inputs": req.inputs, "outputs": [], "error": None, "mode": MODE, "created": time.time(),
           "fav": False, "project": req.project}
    with LOCK:
        JOBS[job["id"]] = job
        CREATED_THIS_RUN += 1
        _save_jobs()
    POOL.submit(_execute, job["id"])
    return job


@app.get("/api/jobs")
def jobs():
    with LOCK:
        return sorted(JOBS.values(), key=lambda j: j["created"], reverse=True)


@app.delete("/api/jobs/{job_id}", status_code=204)
def delete_job(job_id: str):
    """Remove a finished generation from the history (its files stay in outputs/)."""
    with LOCK:
        j = JOBS.get(job_id)
        if not j:
            raise HTTPException(404, "unknown job")
        if j["status"] in ("queued", "running"):
            raise HTTPException(409, "job is still running")
        del JOBS[job_id]
        _save_jobs()


@app.patch("/api/jobs/{job_id}")
def patch_job(job_id: str, req: JobPatch):
    """Favorite a generation or file it under a project (Higgsfield's My favorites / Projects)."""
    with LOCK:
        j = JOBS.get(job_id)
        if not j:
            raise HTTPException(404, "unknown job")
        if req.fav is not None:
            j["fav"] = req.fav
        if "project" in req.model_fields_set:
            j["project"] = req.project or None
        _save_jobs()
        return j


PROJECTS_FILE = JOBS_FILE.with_name("projects.json")


def _projects() -> list[dict]:
    try:
        return json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


@app.get("/api/projects")
def list_projects():
    return _projects()


@app.post("/api/projects", status_code=201)
def create_project(req: ProjectRequest):
    p = {"id": uuid.uuid4().hex[:10], "name": req.name.strip()[:60] or "Untitled project", "created": time.time()}
    with LOCK:
        items = [p, *_projects()]
        PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PROJECTS_FILE.write_text(json.dumps(items), encoding="utf-8")
    return p


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: str):
    with LOCK:
        items = _projects()
        if not any(p["id"] == project_id for p in items):
            raise HTTPException(404, "unknown project")
        PROJECTS_FILE.write_text(json.dumps([p for p in items if p["id"] != project_id]), encoding="utf-8")
        for j in JOBS.values():  # its generations stay, just unfiled
            if j.get("project") == project_id:
                j["project"] = None
        _save_jobs()


BLOG = ROOT / "blog"


def _post(path: Path) -> dict:
    """A blog post is markdown with a small 'key: value' front-matter block between --- lines."""
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---"):
        head, _, body = text[3:].partition("\n---")
        for line in head.strip().splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    meta["slug"] = path.stem
    meta["minutes"] = max(1, round(len(body.split()) / 220))
    return {"meta": meta, "body": body.lstrip("-\n")}


@app.get("/api/blog")
def blog_list():
    posts = [_post(p)["meta"] for p in BLOG.glob("*.md")] if BLOG.exists() else []
    return sorted(posts, key=lambda m: m.get("date", ""), reverse=True)


@app.get("/api/blog/{slug}")
def blog_post(slug: str):
    path = BLOG / f"{slug}.md"
    if Path(slug).name != slug or not path.exists():
        raise HTTPException(404, "unknown post")
    return _post(path)


@app.get("/api/jobs/{job_id}")
def job(job_id: str):
    with LOCK:
        j = JOBS.get(job_id)
    if not j:
        raise HTTPException(404, "unknown job")
    return j


assets.LIB.mkdir(exist_ok=True)
app.include_router(assets.router)
app.mount("/library", StaticFiles(directory=assets.LIB), name="library")
runner.OUTPUTS.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=runner.OUTPUTS), name="outputs")
app.mount("/examples", StaticFiles(directory=ROOT / "examples"), name="examples")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
