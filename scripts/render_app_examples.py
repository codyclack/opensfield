"""Render one example per Higgsfield app through the app's own path (runner.run_comfy -> comfy-sdk -> ComfyUI).

Uses each app's open-weights version: Qwen-Image-Edit 2511 for photo apps (two photos for the swap / try-on apps) and
LTX-2.3 at 3 s for video apps. Point COMFY_BASE_URL at a local ComfyUI (no credits) or leave it unset for Comfy Cloud.
Resumable: apps that already have an example are skipped.

    $env:COMFY_BASE_URL="http://127.0.0.1:8188"; uv run --extra comfy --extra fx python scripts/render_app_examples.py [--only shots,relight] [--limit 3] [--mode image]
"""
import argparse
import json
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("OPENSFIELD_MODE", "comfy")
from app import runner  # noqa: E402
from app.registry import load_features  # noqa: E402
from registry.apps import APPS  # noqa: E402

EX = ROOT / "examples"
OUT = EX / "apps"
RECORD = ROOT / "registry" / "apps_examples.json"
PERSON, PERSON_B, PRODUCT = "char_a.png", "char_b.png", "t2i_flux3_sneakers.png"
GARMENT = "garment_puffer.png"  # scripts/make_garment.py
FIXTURE = {"sketch-to-real": "sketch_input.png", "japanese-show": PERSON_B, "plushies": PERSON_B, "game-dump": PERSON_B, "pixel-game": PERSON_B,
           "3d-figure": PERSON_B, "mascot": PERSON_B, "comic-book": PERSON_B, "relight": "influencer_cafe.png", "behind-the-scenes": "influencer_cafe.png",
           "shots": "influencer_cafe.png", "zooms": "influencer_cafe.png", "whats-next": "influencer_cafe.png", "color-grading": "style_reference_alley.png"}
EXTRA = {"meme-generator": "WHEN THE RENDER FINALLY WORKS"}
VIA = os.environ.get("OPENSFIELD_EXAMPLE_VIA", "Rendered through the app's own runner (comfy-sdk) with open weights, 2026-10-22")


def make_sketch():
    """A line drawing for Sketch-to-Real, traced from an example image (edges on white)."""
    dst = EX / "sketch_input.png"
    if dst.exists():
        return
    import cv2
    img = cv2.imread(str(EX / PRODUCT), cv2.IMREAD_GRAYSCALE)
    edges = cv2.Canny(cv2.GaussianBlur(img, (5, 5), 0), 60, 140)
    cv2.imwrite(str(dst), 255 - cv2.dilate(edges, None))


def upload(name):
    runner.UPLOADS.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(EX / name, runner.UPLOADS / f"app_{name}")
    return f"app_{name}"


def inputs_for(app, f):
    vals = {}
    imgs = [s for s in f["inputs"] if s["kind"] == "image"]
    first = FIXTURE.get(app["slug"], PRODUCT if app["cat"] == "Ads & Products" else PERSON)
    second = GARMENT if app["slug"] in ("ai-stylist", "outfit-swap") else PERSON_B  # try-on takes a garment photo
    for i, s in enumerate(imgs):
        vals[s["name"]] = upload(first if i == 0 else second)
    for s in f["inputs"]:
        if s["kind"] == "text" and app["slug"] in EXTRA:
            vals[s["name"]] = EXTRA[app["slug"]]
        if s["name"] == "duration":
            vals[s["name"]] = 3  # short clips: these are examples
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--mode", default="", help="image | video | pair: render only this kind of app")
    args = ap.parse_args()
    make_sketch()
    feats = {f["id"]: f for f in load_features()}
    record = json.loads(RECORD.read_text(encoding="utf-8")) if RECORD.exists() else {}
    only = {s for s in args.only.split(",") if s}
    todo = [a for a in APPS if a["mode"] != "tool" and (not only or a["slug"] in only) and (not args.mode or a["mode"] == args.mode) and a["slug"] not in record]
    if args.limit:
        todo = todo[: args.limit]
    OUT.mkdir(parents=True, exist_ok=True)
    for a in todo:
        fid = f"app.{a['slug']}-open" if f"app.{a['slug']}-open" in feats else f"app.{a['slug']}"
        f = feats[fid]
        job = {"id": f"apps/{a['slug']}", "inputs": inputs_for(a, f)}
        t0 = time.time()
        try:
            outs = runner.run_comfy(f, job, lambda **kw: None)
            o = next(x for x in outs if x["kind"] in ("image", "video"))
            src = runner.OUTPUTS / o["url"].removeprefix("/outputs/")
            dst = OUT / f"{a['slug']}{src.suffix.lower()}"
            shutil.copyfile(src, dst)
            record = json.loads(RECORD.read_text(encoding="utf-8")) if RECORD.exists() else {}  # re-read: someone may have dropped an example to redo
            record[a["slug"]] = {"feature": fid, "example": f"examples/apps/{dst.name}", "via": VIA}
            RECORD.write_text(json.dumps(record, indent=1), encoding="utf-8")
            print(f"OK    {a['slug']:<26} {round(time.time() - t0):>4}s  {fid}", flush=True)
        except Exception as e:  # noqa: BLE001 - keep going, report at the end
            print(f"FAIL  {a['slug']:<26} {round(time.time() - t0):>4}s  {type(e).__name__}: {str(e)[:200]}", flush=True)
            if "10061" in str(e) or "10054" in str(e):
                break  # the server is gone: stop here and let the caller restart it instead of failing every app
        if os.environ.get("OPENSFIELD_FREE_BETWEEN") and os.environ.get("COMFY_BASE_URL"):
            # LTX-2.3 on a shared 24 GB card: unload everything between clips, or the next load runs out of memory
            req = urllib.request.Request(os.environ["COMFY_BASE_URL"].rstrip("/") + "/free", data=b'{"unload_models": true, "free_memory": true}',
                                         headers={"Content-Type": "application/json"})
            try:
                urllib.request.urlopen(req, timeout=30).read()
                time.sleep(5)
            except OSError:
                pass
    print(f"done: {len(record)} apps have examples", flush=True)


if __name__ == "__main__":
    main()
