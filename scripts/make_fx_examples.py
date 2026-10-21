"""Render the example clips for the local effect modules from examples/driving_dance.mp4.

    uv run --extra fx scripts/make_fx_examples.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import fx  # noqa: E402

SRC = ROOT / "examples" / "driving_dance.mp4"
for name, mode in {"fx_thermal_blackhot": "black-hot", "fx_thermal_rainbow": "rainbow", "fx_crt": "crt", "fx_vhs": "vhs", "fx_nokia": "nokia"}.items():
    out = fx.process_video(SRC, ROOT / "examples" / f"{name}.mp4", mode, max_seconds=4, max_width=640)
    print(name, f"{out.stat().st_size / 1e3:.0f} KB")
