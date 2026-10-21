"""Promote partner-model tools that passed a live smoke run: copy their output into examples/models/ and record it.

Reads outputs/smoke_model_<id>/ (written by scripts/smoke_cloud.py), writes registry/models_examples.json, which
scripts/gen_models.py and registry/wiring.py use to mark those tools verified. Run build_registry.py afterwards.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
EX = ROOT / "examples" / "models"
VIA = "App path: runner.run_comfy -> comfy-sdk -> Comfy Cloud, 2026-10-21"
ex_path = ROOT / "registry" / "models_examples.json"
gen_path = ROOT / "registry" / "models_gen.json"

examples = json.loads(ex_path.read_text(encoding="utf-8")) if ex_path.exists() else {}
gen = json.loads(gen_path.read_text(encoding="utf-8"))
EX.mkdir(parents=True, exist_ok=True)
for d in sorted(OUT.glob("smoke_model_*")):
    fid = "model." + d.name.removeprefix("smoke_model_")
    files = [f for f in sorted(d.iterdir()) if f.suffix.lower() in {".png", ".jpg", ".webp", ".mp4", ".webm", ".mp3", ".flac", ".wav"}]
    if not files or fid not in gen["wiring"]:
        continue
    src = files[0]
    dst = EX / f"{fid.removeprefix('model.')}{src.suffix.lower()}"
    shutil.copyfile(src, dst)
    examples[fid] = [f"examples/models/{dst.name}"]
    gen["wiring"][fid].update(verified_via=VIA, examples=examples[fid])
    print("promoted", fid, dst.name)
ex_path.write_text(json.dumps(examples, indent=1), encoding="utf-8")
gen_path.write_text(json.dumps(gen, indent=1), encoding="utf-8")
