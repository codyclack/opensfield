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

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = ImageDraw = ImageFont = None

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


def _font(size, bold=True, mono=False):
    import os
    names = (["consolab.ttf", "consola.ttf", "DejaVuSansMono-Bold.ttf"] if mono else
             ["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"] if bold else ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"])
    for d in (os.environ.get("WINDIR", "C:/Windows") + "/Fonts", "/usr/share/fonts/truetype/dejavu", "/Library/Fonts"):
        for n in names:
            if os.path.exists(os.path.join(d, n)):
                return ImageFont.truetype(os.path.join(d, n), size)
    return ImageFont.load_default(size=size)  # Pillow >= 10.1 bitmap fallback


def _draw_text(frame, items):
    """items: [(text, (x, y), size, rgb, kw)] drawn with a dark outline. Returns a new BGR frame."""
    if Image is None:
        raise RuntimeError("text looks need Pillow: uv sync --extra fx")
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(img, "RGBA")
    for text, xy, size, rgb, kw in items:
        d.text(xy, text, font=_font(size, mono=kw.get("mono", False)), fill=rgb + (255,), anchor=kw.get("anchor", "la"),
               stroke_width=max(1, size // 14), stroke_fill=(0, 0, 0, 255))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def _lines(text):
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def captions(frame, idx, ctx):
    """Burn the given lines as subtitles, spread evenly across the clip (no speech recognition)."""
    lines = _lines(ctx["text"])
    h, w = frame.shape[:2]
    cur = lines[min(len(lines) - 1, int(idx / max(1, ctx["n"]) * len(lines)))]
    size = max(14, h // 16)
    out = frame.copy()
    cv2.rectangle(out, (0, int(h * 0.78)), (w, int(h * 0.94)), (0, 0, 0), -1)
    out = cv2.addWeighted(out, 0.45, frame, 0.55, 0)
    return _draw_text(out, [(cur, (w // 2, int(h * 0.86)), size, (255, 255, 255), {"anchor": "mm"})])


def typewriter(frame, idx, ctx):
    """Type the text onto a dark panel, character by character, with a blinking cursor."""
    text = " ".join(_lines(ctx["text"]))
    h, w = frame.shape[:2]
    shown = int(len(text) * min(1.0, idx / max(1, ctx["n"] * 0.7)))
    cursor = "_" if (idx // max(1, int(ctx["fps"] / 2))) % 2 == 0 or shown < len(text) else " "
    size = max(14, h // 18)
    per_line = max(8, int(w * 0.84 / (size * 0.6)))
    rows = [text[:shown][i:i + per_line] for i in range(0, max(1, shown), per_line)] or [""]
    rows[-1] += cursor
    panel = frame.copy()
    cv2.rectangle(panel, (int(w * 0.06), int(h * 0.08)), (int(w * 0.94), int(h * 0.08) + int(size * 1.5 * (len(rows) + 1))), (0, 0, 0), -1)
    out = cv2.addWeighted(panel, 0.6, frame, 0.4, 0)
    return _draw_text(out, [(r, (int(w * 0.09), int(h * 0.08) + int(size * 0.8) + int(i * size * 1.5)), size, (120, 255, 140), {"mono": True})
                            for i, r in enumerate(rows)])


def wordstack(frame, idx, ctx):
    """Stack the words one by one as big outlined type, alternating white and lime."""
    words = " ".join(_lines(ctx["text"])).split()
    h, w = frame.shape[:2]
    show = max(1, min(len(words), int(np.ceil(len(words) * min(1.0, (idx + 1) / max(1, ctx["n"] * 0.8))))))
    size = max(18, min(h // 6, int(h * 0.8 / max(1, show) * 0.75)))
    y0 = h // 2 - int(size * 0.55 * show)
    items = [(words[i].upper(), (int(w * 0.07), y0 + int(i * size * 1.1)), size, (255, 255, 255) if i % 2 == 0 else (209, 254, 23), {})
             for i in range(show)]
    return _draw_text(cv2.addWeighted(frame, 0.7, np.zeros_like(frame), 0.3, 0), items)


def deflicker(frame, idx, ctx):
    """Scale each frame so its mean brightness follows a rolling median (computed in a first pass)."""
    return _u8(frame.astype(np.float32) * ctx["gains"][min(idx, len(ctx["gains"]) - 1)])


def _gains_from_means(means, window=9):
    m = np.asarray(means, dtype=np.float64) + 1e-3
    pad = window // 2
    ref = np.array([np.median(m[max(0, i - pad):i + pad + 1]) for i in range(len(m))])
    return np.clip(ref / m, 0.6, 1.6)


def _deflicker_gains(path, limit, window=9):
    cap = cv2.VideoCapture(str(path))
    means = []
    while len(means) < limit:
        ok, fr = cap.read()
        if not ok:
            break
        means.append(float(fr.mean()))
    cap.release()
    return _gains_from_means(means, window)


CTX_MODES: dict[str, Callable] = {"captions": captions, "typewriter": typewriter, "wordstack": wordstack, "deflicker": deflicker}
TEXT_MODES = {"captions", "typewriter", "wordstack"}


def process_video(src: Path, dst: Path, mode: str, max_seconds: float | None = None, max_width: int | None = 960,
                  progress: Callable[[float], None] | None = None, text: str = "") -> Path:
    """Apply one effect to every frame of `src` and write an H.264 mp4 to `dst`."""
    _need()
    import imageio_ffmpeg
    if mode not in MODES and mode not in CTX_MODES:
        raise ValueError(f"unknown mode {mode!r}; choose one of {sorted({*MODES, *CTX_MODES})}")
    if mode in TEXT_MODES and not _lines(text):
        raise ValueError(f"the {mode!r} look needs some text")
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
    ctx = {"text": text, "fps": fps, "n": min(total, limit) if total else limit}
    if mode == "deflicker":
        ctx["gains"] = _deflicker_gains(src, limit)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    while n < limit:
        ok, fr = cap.read()
        if not ok:
            break
        if (ow, oh) != (w, h):
            fr = cv2.resize(fr, (ow, oh), interpolation=cv2.INTER_AREA)
        out = CTX_MODES[mode](fr, n, ctx) if mode in CTX_MODES else MODES[mode](fr, n)
        p.stdin.write(np.ascontiguousarray(out).tobytes())
        n += 1
        if progress and total:
            progress(min(0.99, n / min(total, limit)))
    cap.release()
    p.stdin.close()
    if p.wait() != 0 or n == 0:
        raise RuntimeError("video encode failed")
    return dst
