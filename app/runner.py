"""Job runners. MockRunner never touches ComfyUI; ComfyRunner uses comfy-sdk.

ComfyRunner is written against the documented comfy-sdk surface
(Comfy, workflows.from_file, assets.from_file, wf.set_input, client.run,
job.get_outputs) and has NOT been exercised yet: Comfy testing is on hold.
"""
from __future__ import annotations

import os
import random
import time
from html import escape
from pathlib import Path
from typing import Callable

from .registry import ROOT

OUTPUTS = ROOT / "outputs"
UPLOADS = OUTPUTS / "uploads"

Update = Callable[..., None]


class RunError(Exception):
    pass


def _svg(feature: dict, job: dict) -> str:
    inputs = job["inputs"]
    lines = [f"{k}: {str(v)[:60]}" for k, v in inputs.items() if v not in ("", None)][:6]
    rows = "".join(f'<text x="64" y="{420 + 34 * i}" font-size="22" fill="#9aa4b2">{escape(t)}</text>' for i, t in enumerate(lines))
    hue = sum(map(ord, feature["id"])) % 360
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="Segoe UI, sans-serif">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="hsl({hue},60%,18%)"/><stop offset="1" stop-color="hsl({(hue + 60) % 360},70%,8%)"/></linearGradient></defs>
<rect width="1280" height="720" fill="url(#g)"/>
<text x="64" y="120" font-size="22" letter-spacing="6" fill="#f5b942">MOCK OUTPUT - NO COMFYUI CALL</text>
<text x="64" y="230" font-size="64" font-weight="700" fill="#fff">{escape(feature['name'])}</text>
<text x="64" y="290" font-size="26" fill="#c3cad5">{escape(feature['studio'])} / {escape(feature['id'])}</text>
<text x="64" y="350" font-size="22" fill="#c3cad5">would produce: {escape(feature['output_kind'])}</text>
{rows}
</svg>"""


def resolve_values(feature: dict, inputs: dict) -> dict:
    """Expand preset inputs: a choice with `presets` writes its text into the input named by `apply_to`,
    and a text input with `prefix` gets it prepended. Preset modules reuse another module's workflow this way."""
    vals = dict(inputs)
    for spec in feature["inputs"]:
        pr, tgt = spec.get("presets"), spec.get("apply_to")
        if pr and tgt and spec["name"] in vals:
            user = str(vals.get(tgt) or "").strip()
            vals[tgt] = (pr.get(vals[spec["name"]], "") + (" " + user if user else "")).strip()
    for spec in feature["inputs"]:
        if spec.get("prefix"):
            vals[spec["name"]] = spec["prefix"] + str(vals.get(spec["name"]) or "")
    return vals


def run_mock(feature: dict, job: dict, update: Update) -> list[dict]:
    delay = float(os.environ.get("OPENSFIELD_MOCK_DELAY", "3"))
    steps = 10
    for i in range(steps):
        time.sleep(delay / steps)
        update(progress=(i + 1) / steps)
    out = OUTPUTS / job["id"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "out.svg").write_text(_svg(feature, job), encoding="utf-8")
    return [{"url": f"/outputs/{job['id']}/out.svg", "kind": "image", "name": "out.svg", "mock": True}]


def run_local(feature: dict, job: dict, update: Update) -> list[dict]:
    """CPU effects (app/fx.py). Works in any mode: it never touches ComfyUI."""
    from . import fx
    loc = feature["local"]
    mode = loc.get("mode") or job["inputs"].get(loc["mode_input"]) or next(s["default"] for s in feature["inputs"] if s["name"] == loc["mode_input"])
    out = OUTPUTS / job["id"] / f"{mode}.mp4"
    fx.process_video(UPLOADS / job["inputs"]["video"], out, mode, max_seconds=10, progress=lambda p: update(progress=p),
                     text=str(job["inputs"].get(loc.get("text_input", ""), "")))
    return [{"url": f"/outputs/{job['id']}/{mode}.mp4", "kind": "video", "name": out.name, "mock": False}]


def run_comfy(feature: dict, job: dict, update: Update) -> list[dict]:
    wf_meta = feature.get("workflow") or {}
    if not feature["runnable"]:
        raise RunError(f"{feature['id']} has no workflow yet (status: {feature['status']}). Use mock mode.")
    try:
        from comfy_sdk import Comfy  # lazy: only needed for real runs
    except ImportError as e:
        raise RunError("comfy-sdk not installed: run `uv sync --extra comfy`") from e

    key = os.environ.get("COMFY_API_KEY")
    client = Comfy(api_key=key) if key else Comfy()  # base url comes from COMFY_BASE_URL (Comfy Cloud if unset, which needs a key)
    wf = client.workflows.from_file(str(ROOT / wf_meta["api"]))
    values = resolve_values(feature, job["inputs"])
    for spec in feature["inputs"]:
        value = values.get(spec["name"])
        if spec["kind"] == "seed" and not value:
            value = random.randint(1, 2**48)
        if value in ("", None) or "node" not in spec:
            continue  # blank = keep the template default
        if spec["kind"] in ("image", "video", "audio"):
            value = client.assets.from_file(str(UPLOADS / value))  # value is the stored upload filename
        elif spec["kind"] == "number":
            value = int(value) if isinstance(spec.get("default"), int) else float(value)
        for t in [{"node": spec["node"], "field": spec["field"]}, *spec.get("also", [])]:
            wf.set_input(t["node"], t["field"], value)
    update(progress=0.1)
    result = client.run(wf)

    out = OUTPUTS / job["id"]
    out.mkdir(parents=True, exist_ok=True)
    outputs = []
    for node in wf_meta.get("outputs", []):
        for o in result.get_outputs(node):
            o.to_file(str(out / o.name))
            ext = Path(o.name).suffix.lower()
            kind = ("video" if ext in (".mp4", ".webm", ".mov") else "audio" if ext in (".wav", ".mp3", ".flac", ".ogg")
                    else "3d" if ext in (".glb", ".gltf") else "image")
            outputs.append({"url": f"/outputs/{job['id']}/{o.name}", "kind": kind, "name": o.name, "mock": False})
    return outputs
