"""Local video effects for the Match Cut + Tracelab looks. CPU only: no ComfyUI, no GPU, no network.

Needs the `fx` extra (numpy, opencv-python-headless, imageio-ffmpeg): `uv sync --extra fx`.
Every effect is a pure function frame(BGR uint8) -> frame, seeded by the frame index so renders are reproducible.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

try:
    import cv2
    import numpy as np
except ImportError:  # pragma: no cover - exercised only without the extra
    cv2 = np = None

THERMAL = ["black-hot", "white-hot", "rainbow", "iron"]
RETRO = ["crt", "crt-glitch", "vhs", "glitch", "nokia", "retropop", "night-vision"]


def _need():
    if cv2 is None:
        raise RuntimeError("local effects need the fx extra: uv sync --extra fx")


def _u8(a):
    return np.clip(a, 0, 255).astype(np.uint8)


def _vignette(h, w, strength):
    yy, xx = np.ogrid[:h, :w]
    d = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    return (1 - strength * d)[..., None].astype(np.float32)


def thermal(frame, palette, idx=0):
    _need()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(2.0, (8, 8)).apply(cv2.GaussianBlur(gray, (0, 0), 1.2))
    if palette == "black-hot":
        out = cv2.cvtColor(255 - gray, cv2.COLOR_GRAY2BGR)
    elif palette == "white-hot":
        out = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    elif palette == "rainbow":
        out = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
    elif palette == "iron":
        out = cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)
    else:
        raise ValueError(f"unknown palette {palette!r}")
    noise = np.random.default_rng(idx).normal(0, 5, gray.shape).astype(np.float32)[..., None]
    return _u8(out.astype(np.float32) + noise)


def crt(frame, idx=0, glitch=False):
    _need()
    h, w = frame.shape[:2]
    b, g, r = cv2.split(frame.astype(np.float32))
    s = max(1, w // 320)
    out = cv2.merge([np.roll(b, -s, 1), g, np.roll(r, s, 1)])  # chromatic aberration
    out = out * 0.85 + cv2.GaussianBlur(out, (0, 0), max(1.0, w / 80)) * 0.35  # bloom
    scan = np.ones((h, 1, 1), np.float32)
    scan[::3] = 0.7
    out = out * scan * _vignette(h, w, 0.35)
    if glitch:
        rng = np.random.default_rng(idx)
        for _ in range(3):
            y0, hh = int(rng.integers(0, max(1, h - 8))), int(rng.integers(4, max(5, h // 12)))
            out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], int(rng.integers(-w // 20, w // 20 + 1)), 1)
    return _u8(out)


def vhs(frame, idx=0):
    _need()
    h, w = frame.shape[:2]
    rng = np.random.default_rng(idx)
    ycc = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    for c in (1, 2):  # chroma bleed
        ycc[..., c] = cv2.GaussianBlur(ycc[..., c], (0, 0), max(1.0, w / 50))
    out = cv2.cvtColor(ycc, cv2.COLOR_YCrCb2BGR).astype(np.float32)
    gray = out.mean(axis=2, keepdims=True)
    out = gray + (out - gray) * 0.8  # desaturate a little
    out += rng.normal(0, 9, out.shape[:2]).astype(np.float32)[..., None]
    band = slice(int(h * 0.88), h)  # tracking error near the bottom
    out[band] = np.roll(out[band], int(rng.integers(-w // 25, w // 25 + 1)), 1)
    out[::2] *= 0.92
    return _u8(out + 6)


def glitch(frame, idx=0):
    _need()
    h, w = frame.shape[:2]
    rng = np.random.default_rng(idx)
    out = frame.copy()
    for c in range(3):  # channel offsets
        out[..., c] = np.roll(out[..., c], int(rng.integers(-w // 40, w // 40 + 1)), 1)
    for _ in range(int(rng.integers(2, 6))):
        y0 = int(rng.integers(0, max(1, h - 10)))
        hh = int(rng.integers(6, max(7, h // 8)))
        blk = np.roll(out[y0:y0 + hh], int(rng.integers(-w // 8, w // 8 + 1)), 1)
        out[y0:y0 + hh] = 255 - blk if rng.random() < 0.15 else blk
    return out


_NOKIA = np.array([[61, 82, 67], [97, 130, 109], [140, 184, 159], [216, 240, 199]], np.uint8) if np is not None else None  # BGR, dark to light
_POP = np.array([[40, 15, 25], [170, 45, 255], [60, 225, 255], [255, 240, 80]], np.uint8) if np is not None else None  # BGR


def _quantize(gray, palette):
    idx = np.minimum(gray.astype(np.int32) * len(palette) // 256, len(palette) - 1)
    return palette[idx]


def nokia(frame, idx=0):
    _need()
    h, w = frame.shape[:2]
    cols = 84
    rows = max(1, round(cols * h / w))
    small = cv2.cvtColor(cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    small = cv2.equalizeHist(small)
    out = cv2.resize(_quantize(small, _NOKIA), (w, h), interpolation=cv2.INTER_NEAREST)
    cell_x, cell_y = max(1, w // cols), max(1, h // rows)
    out[::cell_y] = (out[::cell_y] * 0.8).astype(np.uint8)  # LCD pixel gaps
    out[:, ::cell_x] = (out[:, ::cell_x] * 0.8).astype(np.uint8)
    return out


def retropop(frame, idx=0):
    _need()
    gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    return _quantize(cv2.GaussianBlur(gray, (0, 0), 1.0), _POP)


def night_vision(frame, idx=0):
    _need()
    h, w = frame.shape[:2]
    rng = np.random.default_rng(idx)
    lum = np.clip(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32) * 1.5 + 25, 0, 255)
    lum += rng.normal(0, 14, lum.shape).astype(np.float32)
    lum *= 1 + 0.04 * np.sin(idx * 0.9)
    out = np.dstack([lum * 0.25, lum, lum * 0.3]) * _vignette(h, w, 0.8)
    out[::4] *= 0.85
    return _u8(out)


MODES: dict[str, Callable] = {
    **{p: (lambda fr, i, p=p: thermal(fr, p, i)) for p in THERMAL},
    "crt": lambda fr, i: crt(fr, i),
    "crt-glitch": lambda fr, i: crt(fr, i, glitch=True),
    "vhs": vhs, "glitch": glitch, "nokia": nokia, "retropop": retropop, "night-vision": night_vision,
}


def process_video(src: Path, dst: Path, mode: str, max_seconds: float | None = None, max_width: int | None = 960,
                  progress: Callable[[float], None] | None = None) -> Path:
    """Apply one effect to every frame of `src` and write an H.264 mp4 to `dst`."""
    _need()
    import imageio_ffmpeg
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; choose one of {sorted(MODES)}")
    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        raise RuntimeError(f"cannot read video {src}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    s = min(1.0, max_width / w) if max_width else 1.0
    ow, oh = max(2, int(w * s) // 2 * 2), max(2, int(h * s) // 2 * 2)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    limit = int(max_seconds * fps) if max_seconds else total or 10**9
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ow}x{oh}",
           "-r", f"{fps:.3f}", "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", str(dst)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    while n < limit:
        ok, fr = cap.read()
        if not ok:
            break
        if (ow, oh) != (w, h):
            fr = cv2.resize(fr, (ow, oh), interpolation=cv2.INTER_AREA)
        p.stdin.write(np.ascontiguousarray(MODES[mode](fr, n)).tobytes())
        n += 1
        if progress and total:
            progress(min(0.99, n / min(total, limit)))
    cap.release()
    p.stdin.close()
    if p.wait() != 0 or n == 0:
        raise RuntimeError("video encode failed")
    return dst
