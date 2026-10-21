"""Render the example clips for the local effect modules from examples/driving_dance.mp4.

    uv run --extra fx scripts/make_fx_examples.py
"""
import subprocess
import sys
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import fx  # noqa: E402

EX = ROOT / "examples"
SRC = EX / "driving_dance.mp4"

for name, mode in {"fx_thermal_blackhot": "black-hot", "fx_thermal_rainbow": "rainbow", "fx_crt": "crt", "fx_vhs": "vhs", "fx_nokia": "nokia"}.items():
    out = fx.process_video(SRC, EX / f"{name}.mp4", mode, max_seconds=4, max_width=640)
    print(name, f"{out.stat().st_size / 1e3:.0f} KB")

TEXT = {"fx_captions": ("captions", "Open source Higgsfield\nbuilt on ComfyUI\n33 modules, open weights only"),
        "fx_typewriter": ("typewriter", "OpenSfield rebuilds Higgsfield's creative apps as open-source ComfyUI workflows."),
        "fx_wordstack": ("wordstack", "Open weights only")}
for name, (mode, text) in TEXT.items():
    out = fx.process_video(SRC, EX / f"{name}.mp4", mode, max_seconds=4, max_width=640, text=text)
    print(name, f"{out.stat().st_size / 1e3:.0f} KB")

# deflicker: inject random brightness flicker, then remove it and report how much the per-frame brightness jitter dropped
cap = cv2.VideoCapture(str(SRC))
fps = cap.get(cv2.CAP_PROP_FPS)
rng = np.random.default_rng(3)
cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "640x352", "-r", f"{fps:.3f}", "-i", "-",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(EX / "flicker_input.mp4")]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for _ in range(int(4 * fps)):
    ok, fr = cap.read()
    if not ok:
        break
    fr = cv2.resize(fr, (640, 352), interpolation=cv2.INTER_AREA).astype(np.float32) * rng.uniform(0.7, 1.3)
    p.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
p.stdin.close()
p.wait()
fx.process_video(EX / "flicker_input.mp4", EX / "fx_deflicker.mp4", "deflicker", max_width=640)


def jitter(path):
    c, means = cv2.VideoCapture(str(path)), []
    while True:
        ok, f = c.read()
        if not ok:
            break
        means.append(float(f.mean()))
    return float(np.std(np.diff(means)))


print("brightness jitter (std of frame-to-frame change):", round(jitter(EX / "flicker_input.mp4"), 2), "->", round(jitter(EX / "fx_deflicker.mp4"), 2))
