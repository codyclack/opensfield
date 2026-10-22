"""Job runners. MockRunner never touches ComfyUI; ComfyRunner uses comfy-sdk.

ComfyRunner is written against the documented comfy-sdk surface
(Comfy, workflows.from_file, assets.from_file, wf.set_input, client.run,
job.get_outputs) and has NOT been exercised yet: Comfy testing is on hold.
"""
from __future__ import annotations

import os
import random
import shutil
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
        if pr and tgt:
            choice = vals.get(spec["name"]) or spec.get("default")
            user = str(vals.get(tgt) or "").strip()
            vals[tgt] = (pr.get(choice, "") + (" " + user if user else "")).strip()
    for spec in feature["inputs"]:
        if spec.get("prefix"):
            vals[spec["name"]] = spec["prefix"] + str(vals.get(spec["name"]) or "")
        media = spec.get("media_presets")  # a gallery choice that also supplies a media file (e.g. a driving clip)
        if media and not vals.get(spec["media_target"]):
            src = ROOT / media.get(vals.get(spec["name"]) or spec.get("default"), "")
            if src.is_file():
                UPLOADS.mkdir(parents=True, exist_ok=True)
                name = f"preset_{src.name}"
                if not (UPLOADS / name).exists():
                    shutil.copyfile(src, UPLOADS / name)
                vals[spec["media_target"]] = name
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
    from . import fx_tools  # registers the Tracelab look and the multi-input tools
    loc = feature["local"]
    mode = loc.get("mode") or job["inputs"].get(loc["mode_input"]) or next(s["default"] for s in feature["inputs"] if s["name"] == loc["mode_input"])
    if mode in fx_tools.TOOLS:
        made = fx_tools.TOOLS[mode](job["inputs"], UPLOADS, OUTPUTS / job["id"], lambda p: update(progress=p))
        return [{"url": f"/outputs/{job['id']}/{name}", "kind": kind, "name": Path(name).name, "mock": False} for name, kind in made]
    out = OUTPUTS / job["id"] / f"{mode}.mp4"
    if mode == "clipify":
        fx.clipify(UPLOADS / job["inputs"]["video"], out, seconds=float(job["inputs"].get("seconds") or 10), progress=lambda p: update(progress=p))
        return [{"url": f"/outputs/{job['id']}/{mode}.mp4", "kind": "video", "name": out.name, "mock": False}]
    fx.process_video(UPLOADS / job["inputs"]["video"], out, mode, max_seconds=10, progress=lambda p: update(progress=p),
                     text=str(job["inputs"].get(loc.get("text_input", ""), "")))
    return [{"url": f"/outputs/{job['id']}/{mode}.mp4", "kind": "video", "name": out.name, "mock": False}]


def run_pipeline(feature: dict, job: dict, update: Update, steps_runner) -> list[dict]:
    """Run several existing tools in order, then combine their outputs (e.g. narration + video -> one narrated clip).
    `steps_runner(feature, job, update)` runs one step (run_comfy live, run_mock in mock mode)."""
    from .registry import load_features
    by_id = {f["id"]: f for f in load_features()}
    pipe = feature["pipeline"]
    made = {}
    for i, step in enumerate(pipe["steps"]):
        sub = by_id[step["feature"]]
        inputs = {k: str(v).format(**job["inputs"]) for k, v in step["inputs"].items()}
        sub_job = {"id": f"{job['id']}/step{i}", "inputs": inputs}
        outs = steps_runner(sub, sub_job, lambda **kw: update(progress=(i + kw.get("progress", 0)) / (len(pipe["steps"]) + 1)))
        made[step["as"]] = outs[0]
    if pipe.get("combine") == "mux" and not any(o.get("mock") for o in made.values()):
        from . import fx_tools
        video = OUTPUTS / made["video"]["url"].removeprefix("/outputs/")
        audio = OUTPUTS / made["audio"]["url"].removeprefix("/outputs/")
        dst = OUTPUTS / job["id"] / "narrated.mp4"
        fx_tools.mux(video, audio, dst)
        return [{"url": f"/outputs/{job['id']}/narrated.mp4", "kind": "video", "name": "narrated.mp4", "mock": False}]
    return list(made.values())


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
            value = random.randint(1, 2**31 - 1)  # some nodes (Chatterbox, Seedance) cap seeds at 31-32 bits
        if value in ("", None) and spec.get("clear_blank") and "node" in spec:
            value = ""  # an optional prompt left empty must not fall back to the template's demo text
        elif value in ("", None) or "node" not in spec:
            continue  # blank = keep the template default
        if spec["kind"] in ("image", "video", "audio"):
            value = client.assets.from_file(str(UPLOADS / value))  # value is the stored upload filename
        elif spec["kind"] == "number":
            value = int(value) if isinstance(spec.get("default"), int) else float(value)
        for t in [{"node": spec["node"], "field": spec["field"]}, *spec.get("also", [])]:
            wf.set_input(t["node"], t["field"], value)
    update(progress=0.1)
    result = client.run(wf, api_key=key) if key else client.run(wf)  # api_key also authorises partner (API) nodes

    out = OUTPUTS / job["id"]
    out.mkdir(parents=True, exist_ok=True)
    outputs = []
    for node in wf_meta.get("outputs", []):
        for i, o in enumerate(result.get_outputs(node)):
            # SaveVideo/SaveImage names can carry a subfolder ("video/LTX_00001_.mp4"); flatten it and keep names unique per node
            base = f"{node.replace(':', '_')}_{i}_{Path(str(o.name)).name}"
            o.to_file(str(out / base))
            ext = Path(base).suffix.lower()
            kind = ("video" if ext in (".mp4", ".webm", ".mov") else "audio" if ext in (".wav", ".mp3", ".flac", ".ogg")
                    else "3d" if ext in (".glb", ".gltf") else "image")
            outputs.append({"url": f"/outputs/{job['id']}/{base}", "kind": kind, "name": base, "mock": False})
    return outputs
