"""Asset library: reusable characters, props, locations, styles and products (Higgsfield's Elements / Assets).

Files live in library/ with a small index.json. Using an asset as a tool input copies it into the uploads folder, so
the runner sees an ordinary upload id and nothing else in the app needs to know the library exists.
"""
from __future__ import annotations

import json
import shutil
import threading
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from . import runner
from .registry import ROOT

LIB = ROOT / "library"
INDEX = LIB / "index.json"
TYPES = ["Character", "Prop", "Location", "Style", "Product", "Other"]
KINDS = {"image": {".png", ".jpg", ".jpeg", ".webp", ".gif"}, "video": {".mp4", ".webm", ".mov"}, "audio": {".mp3", ".wav", ".flac", ".ogg"}}
LOCK = threading.Lock()
router = APIRouter(prefix="/api/assets")


def _kind(ext: str) -> str | None:
    return next((k for k, exts in KINDS.items() if ext in exts), None)


def _load() -> list[dict]:
    return json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else []


def _save(items: list[dict]) -> None:
    LIB.mkdir(exist_ok=True)
    INDEX.write_text(json.dumps(items, indent=1), encoding="utf-8")


def _add(src_bytes: bytes | None, src_path: Path | None, filename: str, name: str, type_: str) -> dict:
    ext = Path(filename).suffix.lower()[:8]
    kind = _kind(ext)
    if not kind:
        raise HTTPException(415, f"unsupported file type {ext or '(none)'}")
    if type_ not in TYPES:
        type_ = "Other"
    LIB.mkdir(exist_ok=True)
    fid = uuid.uuid4().hex[:12]
    file = f"{fid}{ext}"
    if src_path is not None:
        shutil.copyfile(src_path, LIB / file)
    else:
        (LIB / file).write_bytes(src_bytes or b"")
    item = {"id": fid, "name": (name or Path(filename).stem)[:60], "type": type_, "kind": kind, "file": file, "url": f"/library/{file}", "created": time.time()}
    with LOCK:
        items = _load()
        items.insert(0, item)
        _save(items)
    return item


@router.get("")
def list_assets():
    return {"types": TYPES, "items": _load()}


@router.post("", status_code=201)
async def add_asset(file: UploadFile = File(...), name: str = Form(""), type: str = Form("Other")):
    return _add(await file.read(), None, file.filename or "", name, type)


class SaveRequest(BaseModel):
    url: str
    name: str = ""
    type: str = "Other"


@router.post("/save", status_code=201)
def save_output(req: SaveRequest):
    """Save a generated output (or an example) into the library."""
    if req.url.startswith("/outputs/"):
        src = (runner.OUTPUTS / req.url.removeprefix("/outputs/")).resolve()
        if runner.OUTPUTS.resolve() not in src.parents:
            raise HTTPException(422, "bad path")
    elif req.url.startswith("/examples/"):
        src = (ROOT / "examples" / req.url.removeprefix("/examples/")).resolve()
        if (ROOT / "examples").resolve() not in src.parents:
            raise HTTPException(422, "bad path")
    else:
        raise HTTPException(422, "only generated outputs and examples can be saved")
    if not src.is_file():
        raise HTTPException(404, "file not found")
    return _add(None, src, src.name, req.name, req.type)


@router.post("/{asset_id}/use")
def use_asset(asset_id: str):
    """Copy an asset into uploads and return the upload id a tool input expects."""
    item = next((a for a in _load() if a["id"] == asset_id), None)
    if not item:
        raise HTTPException(404, "unknown asset")
    name = f"{uuid.uuid4().hex}{Path(item['file']).suffix}"
    runner.UPLOADS.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(LIB / item["file"], runner.UPLOADS / name)
    return {"id": name, "name": item["name"], "url": f"/outputs/uploads/{name}", "kind": item["kind"]}


class RenameRequest(BaseModel):
    name: str | None = None
    type: str | None = None


@router.patch("/{asset_id}")
def edit_asset(asset_id: str, req: RenameRequest):
    with LOCK:
        items = _load()
        item = next((a for a in items if a["id"] == asset_id), None)
        if not item:
            raise HTTPException(404, "unknown asset")
        if req.name is not None:
            item["name"] = req.name[:60] or item["name"]
        if req.type in TYPES:
            item["type"] = req.type
        _save(items)
    return item


@router.delete("/{asset_id}", status_code=204)
def delete_asset(asset_id: str):
    with LOCK:
        items = _load()
        item = next((a for a in items if a["id"] == asset_id), None)
        if not item:
            raise HTTPException(404, "unknown asset")
        (LIB / item["file"]).unlink(missing_ok=True)
        _save([a for a in items if a["id"] != asset_id])
