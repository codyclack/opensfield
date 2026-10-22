"""Make examples/garment_puffer.png, the garment photo the try-on app examples use (AI Stylist, Outfit Swap).

It is cut from char_b.png by the app's own open image-edit path, so a try-on example shows a real garment-only input.

    $env:COMFY_BASE_URL="http://127.0.0.1:8191"; uv run python scripts/make_garment.py
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import runner  # noqa: E402
from app.registry import load_features  # noqa: E402

f = next(x for x in load_features() if x["id"] == "app.relight-open")
f = {**f, "inputs": [{k: v for k, v in s.items() if k != "prefix"} for s in f["inputs"]]}  # same graph, no app prompt
runner.UPLOADS.mkdir(parents=True, exist_ok=True)
shutil.copyfile(ROOT / "examples" / "char_b.png", runner.UPLOADS / "app_char_b.png")
job = {"id": "apps/garment", "inputs": {"image": "app_char_b.png", "seed": 11,
       "prompt": "Show only the orange puffer jacket from this photo as a flat product photo on a plain white background, no person, no mannequin."}}
out = runner.run_comfyui(os.environ["COMFY_BASE_URL"], f, job, lambda **kw: None)
src = runner.OUTPUTS / out[0]["url"].removeprefix("/outputs/")
shutil.copyfile(src, ROOT / "examples" / "garment_puffer.png")
print("wrote examples/garment_puffer.png")
