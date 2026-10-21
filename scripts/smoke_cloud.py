"""Run every ComfyUI-workflow module once through the app's real path (runner.run_comfy -> comfy-sdk -> Comfy Cloud).

Needs a Comfy API key in the environment and spends a small amount of credits (a few seconds to ~2 minutes of GPU per module).

    $env:COMFY_API_KEY = Read-Host "key" -MaskInput
    uv run --extra comfy scripts/smoke_cloud.py                      # all modules, cheapest first
    uv run --extra comfy scripts/smoke_cloud.py --only image.bg-remove,soul.t2i
    uv run --extra comfy scripts/smoke_cloud.py --skip-slow          # skip the multi-minute video modules

Prints one PASS/FAIL line per module and a summary you can paste back; writes outputs/smoke_report.json.
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("OPENSFIELD_MODE", "comfy")
from app import runner  # noqa: E402
from app.registry import load_features  # noqa: E402

EX = ROOT / "examples"
FIXTURE = {"image": "char_a.png", "image_b": "char_b.png", "character": "char_b.png", "start_image": "char_a.png", "end_image": "char_b.png",
           "video": "driving_dance.mp4", "driving_video": "driving_dance.mp4", "audio": "music_lofi.mp3", "voice": "voice_sample.wav"}
PER_MODULE = {  # fixtures that need to be special for a sensible run
    "image.reframe": {"image": "t2i_flux3_sneakers.png"}, "image.inpaint-brush": {"image": "inpaint_input.png"}, "video.upscale": {"video": "motion_transfer.mp4"},
    "soul.styles": {"style": "style_reference_alley.png"}, "genjutsu.styles": {"image": "style_yarn_frame.png"},
    "video.edit": {"image": "ad_social.png"}, "marketing.studio-presets": {"start_image": "t2i_flux3_sneakers.png"}, "marketing.ugc-video": {"start_image": "t2i_flux3_sneakers.png"}, "marketing.click-to-ad": {"start_image": "t2i_flux3_sneakers.png"}, "marketing.ad-multiplier": {"image": "ad_social.png"}, "reshoot.novel-view": {"image": "char_b.png"},
    "marketing.product-photoshoot": {"image": "t2i_flux3_sneakers.png"}, "genjutsu.replace-object": {"image": "char_b.png"},
}
TEXT = {"prompt": "a pair of white sneakers on a wet city street at dusk, soft light", "character_prompt": "a young man with curly hair in an orange puffer jacket",
        "motion_prompt": "an energetic street dance", "target": "woman", "tags": "lo-fi hip hop, 80 BPM, mellow piano, instrumental", "lyrics": "[Instrumental]",
        "text": "hello from OpenSfield"}
SLOW = {"video.reframe", "genjutsu.motion-control", "genjutsu.replace-object", "video.edit", "genjutsu.styles", "video.upscale"}
ORDER = {"image": 0, "audio": 1, "3d": 2, "video": 3}


def inputs_for(feature):
    vals = {}
    for spec in feature["inputs"]:
        name, kind = spec["name"], spec["kind"]
        if kind in ("image", "video", "audio"):
            src = EX / PER_MODULE.get(feature["id"], {}).get(name, FIXTURE.get(name, FIXTURE[kind]))
            runner.UPLOADS.mkdir(parents=True, exist_ok=True)
            dst = runner.UPLOADS / f"smoke_{src.name}"
            shutil.copyfile(src, dst)
            vals[name] = dst.name
        elif kind == "text" and spec.get("required"):
            vals[name] = TEXT.get(name, TEXT["prompt"])
    return vals  # choices, numbers and seeds keep their defaults


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--skip-slow", action="store_true")
    args = ap.parse_args()
    if not os.environ.get("COMFY_API_KEY") and not os.environ.get("COMFY_BASE_URL"):
        sys.exit("Set COMFY_API_KEY first (see the top of this file).")
    only = {s for s in args.only.split(",") if s}
    feats = [f for f in load_features() if f.get("runnable") and not f.get("local") and ((f["status"] == "tested" and not only) or f["id"] in only)]
    feats = [f for f in feats if not (args.skip_slow and f["id"] in SLOW)]
    feats.sort(key=lambda f: (f["id"] in SLOW, ORDER.get(f["output_kind"], 9), f["id"]))
    report = []
    for f in feats:
        t0 = time.time()
        job = {"id": f"smoke_{f['id'].replace('.', '_')}", "inputs": inputs_for(f)}
        try:
            outs = runner.run_comfy(f, job, lambda **kw: None)
            ok = bool(outs) and all((runner.OUTPUTS / job["id"] / o["name"]).exists() for o in outs)
            res = {"id": f["id"], "ok": ok, "outputs": [o["name"] for o in outs], "error": None if ok else "no output files"}
        except Exception as e:  # noqa: BLE001 - report every failure, keep going
            res = {"id": f["id"], "ok": False, "outputs": [], "error": f"{type(e).__name__}: {str(e)[:300]}"}
        res["seconds"] = round(time.time() - t0)
        report.append(res)
        print(f"{'PASS' if res['ok'] else 'FAIL'}  {res['id']:<32} {res['seconds']:>4}s  {res['error'] or ', '.join(res['outputs'])}", flush=True)
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "smoke_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    bad = [r["id"] for r in report if not r["ok"]]
    print(f"\n{len(report) - len(bad)}/{len(report)} passed." + (f" FAILED: {', '.join(bad)}" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
