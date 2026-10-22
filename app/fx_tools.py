"""Local tools that run on this computer's CPU (no ComfyUI, no credits): montage, match-cut reels, subject cuts,
Tracelab HUD tracking, a virality score card, a TikTok export and a one-page website builder.

Each tool takes the job's inputs, the uploads folder and an output folder, and returns [(filename, kind)].
Needs the `fx` extra (numpy, opencv-python-headless, imageio-ffmpeg, pillow).
"""
from __future__ import annotations

import html
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from . import fx

cv2, np = fx.cv2, fx.np
Progress = Callable[[float], None]
SIZES = {"9:16": (720, 1280), "16:9": (1280, 720), "1:1": (960, 960), "4:5": (864, 1080)}


def _writer(dst: Path, w: int, h: int, fps: float):
    import imageio_ffmpeg
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
           "-r", f"{fps:.3f}", "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", str(dst)]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def _close(p):
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("video encode failed")


def _cover(img, w, h, cx=None, cy=None, zoom=1.0):
    """Scale to fill w x h (times zoom) and crop around (cx, cy) in source pixels (default: centre)."""
    ih, iw = img.shape[:2]
    s = max(w / iw, h / ih) * zoom
    rs = cv2.resize(img, (max(w, round(iw * s)), max(h, round(ih * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    cx = (iw / 2 if cx is None else cx) * s
    cy = (ih / 2 if cy is None else cy) * s
    x0 = int(min(max(cx - w / 2, 0), rs.shape[1] - w))
    y0 = int(min(max(cy - h / 2, 0), rs.shape[0] - h))
    return np.ascontiguousarray(rs[y0:y0 + h, x0:x0 + w])


def _frames(path: Path, seconds: float, fps_out: float):
    """Read up to `seconds` of a clip, resampled to fps_out."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot read video {path.name}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    src = []
    while len(src) < int(seconds * fps) + 1:
        ok, fr = cap.read()
        if not ok:
            break
        src.append(fr)
    cap.release()
    if not src:
        raise RuntimeError(f"empty video {path.name}")
    n = max(1, int(seconds * fps_out))
    return [src[min(len(src) - 1, int(i * fps / fps_out))] for i in range(n)]


def _media(inputs: dict, uploads: Path, prefix: str, kind_ext: tuple) -> list[Path]:
    out = []
    for k in sorted(inputs, key=lambda k: (len(k), k)):
        if (k == prefix or re.fullmatch(rf"{prefix}_\d+", k)) and inputs[k]:
            p = uploads / str(inputs[k])
            if p.suffix.lower() in kind_ext and p.exists():
                out.append(p)
    return out


VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv", ".avi")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


# ---------------- montage + match-cut reel ----------------
def montage(inputs: dict, uploads: Path, out: Path, progress: Progress) -> list:
    """Join 2-6 clips into one edit: hard cuts, crossfades or flash cuts, cropped to one aspect ratio, optional look."""
    clips = _media(inputs, uploads, "video", VIDEO_EXT)
    if len(clips) < 2:
        raise ValueError("add at least two clips")
    w, h = SIZES.get(str(inputs.get("ratio") or "9:16"), SIZES["9:16"])
    fps = 24.0
    bpm = float(inputs.get("bpm") or 0)
    each = (60.0 / bpm) * 4 if bpm else float(inputs.get("seconds") or 3)
    trans = str(inputs.get("transition") or "Crossfade")
    look = fx.MODES.get(str(inputs.get("look") or "none"))
    seqs = [[_cover(f, w, h) for f in _frames(c, each, fps)] for c in clips]
    fade = int(fps * 0.4) if trans == "Crossfade" else 0
    p = _writer(out / "montage.mp4", w, h, fps)
    total = sum(len(s) for s in seqs)
    done = n = 0
    for ci, seq in enumerate(seqs):
        for fi, fr in enumerate(seq):
            if fade and ci + 1 < len(seqs) and fi >= len(seq) - fade:
                a = (fi - (len(seq) - fade)) / fade
                fr = cv2.addWeighted(fr, 1 - a, seqs[ci + 1][min(fi - (len(seq) - fade), len(seqs[ci + 1]) - 1)], a, 0)
            if trans == "Flash" and ci and fi < 3:
                fr = cv2.addWeighted(fr, 1 - (3 - fi) / 4, np.full_like(fr, 255), (3 - fi) / 4, 0)
            if look:
                fr = look(fr, n)
            p.stdin.write(fr.tobytes())
            n += 1
            done += 1
            progress(min(0.99, done / total))
    _close(p)
    return [("montage.mp4", "video")]


def reel(inputs: dict, uploads: Path, out: Path, progress: Progress) -> list:
    """Match-cut reel renderer: beat-synced cuts across clips with flash transitions and one render look."""
    inputs = {**inputs, "transition": "Flash", "bpm": inputs.get("bpm") or 120}
    montage(inputs, uploads, out, progress)
    (out / "montage.mp4").replace(out / "reel.mp4")
    return [("reel.mp4", "video")]


# ---------------- subject cuts (face / product / sphere / lens / sticker) ----------------
_face = None


def _faces(img):
    """Haar face boxes; empty when this OpenCV build has no cascade support (OpenCV 5 moved it out of the main module)."""
    global _face
    if _face is None:
        has = hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data")
        _face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml") if has else False
    if _face is False:
        return []
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return _face.detectMultiScale(g, 1.1, 5, minSize=(max(24, img.shape[1] // 20),) * 2)


def _head(img):
    """Face box if detectable, otherwise the top of the subject's outline (good for portraits and full-body shots)."""
    f = _faces(img)
    if len(f):
        return tuple(max(f, key=lambda r: r[2] * r[3]))
    x, y, w, h = _subject_box(img)
    s = max(8, int(min(w, h) * 0.32))
    return (x + w // 2 - s // 2, y, s, s)


def _subject_box(img):
    """Largest region that differs from the border colour (a cheap stand-in for saliency)."""
    h, w = img.shape[:2]
    border = np.concatenate([img[:4].reshape(-1, 3), img[-4:].reshape(-1, 3), img[:, :4].reshape(-1, 3), img[:, -4:].reshape(-1, 3)])
    diff = np.abs(img.astype(np.int16) - np.median(border, 0)).sum(2)
    mask = cv2.morphologyEx((diff > 60).astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return (w // 4, h // 4, w // 2, h // 2)
    return cv2.boundingRect(max(cnts, key=cv2.contourArea))


def subject_cuts(inputs: dict, uploads: Path, out: Path, progress: Progress) -> list:
    """Rapid cuts across 2-8 images with the subject locked to the same spot and size in every shot."""
    imgs = [cv2.imread(str(p)) for p in _media(inputs, uploads, "image", IMAGE_EXT)]
    imgs = [i for i in imgs if i is not None]
    if len(imgs) < 2:
        raise ValueError("add at least two images")
    mode = str(inputs.get("mode") or "Face")
    w, h = SIZES.get(str(inputs.get("ratio") or "9:16"), SIZES["9:16"])
    fps, bpm = 24.0, float(inputs.get("bpm") or 120)
    per = max(2, int(fps * 60 / bpm / 2))  # two cuts per beat
    loops = int(inputs.get("loops") or 3)
    shots = []
    for img in imgs:
        if mode == "Face":
            x, y, bw, bh = _head(img)
            target = 0.32
        else:
            x, y, bw, bh = _subject_box(img)
            target = 0.6
        zoom = max(1.0, (target * w) / max(1, bw) / max(w / img.shape[1], h / img.shape[0]))
        shots.append(_cover(img, w, h, x + bw / 2, y + bh / 2, zoom))
    p = _writer(out / "subject_cuts.mp4", w, h, fps)
    total = len(shots) * loops * per
    n = 0
    for _ in range(loops):
        for si, base in enumerate(shots):
            for k in range(per):
                fr = base
                if mode == "Sphere":
                    bg = np.zeros_like(fr)
                    mask = np.zeros((h, w), np.uint8)
                    cv2.circle(mask, (w // 2, h // 2), int(min(w, h) * 0.42), 255, -1)
                    fr = np.where(mask[..., None] > 0, fr, bg)
                    cv2.circle(fr, (w // 2, h // 2), int(min(w, h) * 0.42), (23, 254, 209), 4)
                elif mode == "Lens":
                    z = 1.0 + 0.25 * (1 - k / per)
                    M = cv2.getRotationMatrix2D((w / 2, h / 2), 0, z)
                    fr = cv2.warpAffine(base, M, (w, h), borderMode=cv2.BORDER_REFLECT)
                    fr = fx._u8(fr * fx._vignette(h, w, 0.6))
                elif mode == "Sticker":
                    bg = np.full_like(base, (40, 30, 20 + 30 * (si % 4)))
                    card = cv2.copyMakeBorder(cv2.resize(base, (int(w * 0.72), int(h * 0.72))), 14, 14, 14, 14, cv2.BORDER_CONSTANT, value=(255, 255, 255))
                    ang = (-6, 5, -3, 7)[si % 4]
                    M = cv2.getRotationMatrix2D((card.shape[1] / 2, card.shape[0] / 2), ang, 1)
                    card = cv2.warpAffine(card, M, (card.shape[1], card.shape[0]), borderValue=(0, 0, 0))
                    y0, x0 = (h - card.shape[0]) // 2, (w - card.shape[1]) // 2
                    roi = bg[y0:y0 + card.shape[0], x0:x0 + card.shape[1]]
                    m = card.sum(2) > 0
                    roi[m] = card[m]
                    fr = bg
                p.stdin.write(np.ascontiguousarray(fr).tobytes())
                n += 1
                progress(min(0.99, n / total))
    _close(p)
    return [("subject_cuts.mp4", "video")]


# ---------------- Tracelab: tracking boxes + HUD overlay ----------------
def tracelab(frame, idx, ctx):
    """Detect faces (or moving objects when there are none) and draw a tracking HUD."""
    h, w = frame.shape[:2]
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    boxes = []
    if idx % 3 == 0 or "boxes" not in ctx:
        boxes = [tuple(b) for b in _faces(frame)]
        prev = ctx.get("prev")
        if not boxes and prev is not None:
            mask = cv2.dilate((cv2.absdiff(g, prev) > 25).astype(np.uint8) * 255, np.ones((9, 9), np.uint8), iterations=2)
            cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            boxes = [cv2.boundingRect(c) for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:3] if cv2.contourArea(c) > w * h * 0.004]
        ctx["boxes"] = boxes
    boxes = ctx["boxes"]
    ctx["prev"] = g
    out = frame.copy()
    lime = (23, 254, 209)
    for i, (x, y, bw, bh) in enumerate(boxes):
        L = max(10, min(bw, bh) // 4)
        for (px, py, dx, dy) in ((x, y, 1, 1), (x + bw, y, -1, 1), (x, y + bh, 1, -1), (x + bw, y + bh, -1, -1)):
            cv2.line(out, (px, py), (px + dx * L, py), lime, 2)
            cv2.line(out, (px, py), (px, py + dy * L), lime, 2)
        cx, cy = x + bw // 2, y + bh // 2
        cv2.drawMarker(out, (cx, cy), lime, cv2.MARKER_CROSS, 14, 1)
        cv2.putText(out, f"OBJ-{i + 1:02d}  {cx},{cy}", (x, max(14, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, lime, 1, cv2.LINE_AA)
        trail = ctx.setdefault("trail", {}).setdefault(i, [])
        trail.append((cx, cy))
        del trail[:-20]
        for a, b in zip(trail, trail[1:]):
            cv2.line(out, a, b, (0, 200, 255), 1, cv2.LINE_AA)
    out[::3] = (out[::3] * 0.85).astype(np.uint8)  # scanlines
    cv2.putText(out, f"TRACELAB  F{idx:05d}  TARGETS {len(boxes)}", (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, lime, 1, cv2.LINE_AA)
    cv2.rectangle(out, (6, 6), (w - 7, h - 7), lime, 1)
    return out


fx.CTX_MODES["tracelab"] = tracelab


# ---------------- virality score card ----------------
def _has_audio(path: Path) -> bool:
    import imageio_ffmpeg
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    return "Audio:" in r.stderr


def virality(inputs: dict, uploads: Path, out: Path, progress: Progress) -> list:
    """Score a short video on things that predict watch-through (hook, pace, format, faces, sound) and render a report card."""
    src = uploads / str(inputs["video"])
    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    energy, bright, faces, prev, n = [], [], 0, None, 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        small = cv2.resize(fr, (96, 96 * h // max(1, w)))
        g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
        energy.append(0.0 if prev is None else float(np.abs(g - prev).mean()))
        bright.append(float(g.mean()))
        if n % int(fps) == 0 and len(_faces(fr)):
            faces += 1
        prev, n = g, n + 1
        if n % 30 == 0:
            progress(0.5 * min(1, n / max(1, cap.get(cv2.CAP_PROP_FRAME_COUNT))))
    cap.release()
    if not energy:
        raise RuntimeError("empty video")
    dur = n / fps
    e = np.asarray(energy)
    hook = float(e[: int(fps * 2)].mean()) if len(e) > 2 else 0
    cuts = int((e > max(18, e.mean() * 4)).sum())
    secs = max(1, int(dur))
    checks = [
        ("Hook (first 2 s)", min(1, hook / 8), "Open on motion or a face; the first two seconds decide the scroll."),
        ("Pace", min(1, (cuts / dur * 6 if dur else 0) + e.mean() / 12), "Add a cut or camera move every 2-3 seconds."),
        ("Vertical format", 1.0 if h > w * 1.5 else 0.6 if h >= w else 0.2, "Export 9:16 for TikTok, Reels and Shorts."),
        ("Length", 1.0 if 6 <= dur <= 35 else 0.6 if dur <= 60 else 0.25, "6 to 35 seconds watch through best."),
        ("Faces on screen", min(1, faces / secs * 1.5), "Faces early and often hold attention."),
        ("Sound", 1.0 if _has_audio(src) else 0.0, "Add music or voice; silent clips get skipped."),
        ("Exposure", 1.0 - min(1, abs(float(np.mean(bright)) - 120) / 120), "Keep the subject bright and readable."),
    ]
    if _face is False:  # no face detector in this OpenCV build: leave faces out rather than score them as zero
        checks = [c for c in checks if c[0] != "Faces on screen"]
    score = round(100 * sum(v for _, v, _ in checks) / len(checks))
    img = fx.Image.new("RGB", (1080, 1350), (14, 14, 16))
    d = fx.ImageDraw.Draw(img)
    d.text((70, 70), "VIRALITY SCORE", font=fx._font(40), fill=(209, 254, 23))
    d.text((70, 120), f"{score}", font=fx._font(220), fill=(255, 255, 255))
    d.text((70, 380), f"{dur:.1f} s · {w}x{h} · {cuts} cuts · {'sound' if checks[5][1] else 'no sound'}", font=fx._font(30, bold=False), fill=(160, 160, 170))
    y = 460
    for name, v, tip in checks:
        d.text((70, y), name, font=fx._font(32), fill=(240, 240, 240))
        d.rounded_rectangle((70, y + 46, 1010, y + 66), 10, fill=(40, 40, 46))
        d.rounded_rectangle((70, y + 46, 70 + int(940 * max(0.02, v)), y + 66), 10, fill=(209, 254, 23) if v >= 0.6 else (255, 181, 71) if v >= 0.3 else (255, 122, 122))
        if v < 0.6:
            d.text((70, y + 74), tip, font=fx._font(24, bold=False), fill=(170, 170, 180))
        y += 118
    d.text((70, 1290), "A heuristic score from the video itself (motion, cuts, format, faces, sound), not a trained model.", font=fx._font(20, bold=False), fill=(110, 110, 120))
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / "virality.png")
    progress(0.99)
    return [("virality.png", "image")]


# ---------------- TikTok export ----------------
def tiktok_export(inputs: dict, uploads: Path, out: Path, progress: Progress) -> list:
    """Reformat any video to TikTok's spec: 1080x1920, blurred fill instead of black bars, H.264 + AAC, at most 60 s."""
    import imageio_ffmpeg
    src = uploads / str(inputs["video"])
    fill = str(inputs.get("fit") or "Blur fill")
    vf = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" if fill == "Crop to fill" else
          "split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:2[bg];"
          "[b]scale=1080:1920:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2")
    out.mkdir(parents=True, exist_ok=True)
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(src), "-t", "60", "-filter_complex" if fill != "Crop to fill" else "-vf", vf,
           "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out / "tiktok.mp4")]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"export failed: {r.stderr[-300:]}")
    caption = str(inputs.get("caption") or "").strip()
    tags = " ".join(t if t.startswith("#") else f"#{t}" for t in str(inputs.get("hashtags") or "").split() if t)
    (out / "caption.txt").write_text(f"{caption}\n\n{tags}".strip() + "\n", encoding="utf-8")
    progress(0.99)
    return [("tiktok.mp4", "video"), ("caption.txt", "text")]


# ---------------- website builder ----------------
SITE_STYLES = {
    "Dark": ("#0c0c0e", "#f4f4f5", "#d1fe17", "#18181c"),
    "Light": ("#fafaf7", "#111111", "#2b59ff", "#ffffff"),
    "Bold": ("#1b0f3b", "#ffffff", "#ff3d7f", "#2a1a57"),
}


def website(inputs: dict, uploads: Path, out: Path, progress: Progress) -> list:
    """A one-page website (hero, features, gallery, call to action) as plain HTML you can host anywhere."""
    site = out / "site"
    site.mkdir(parents=True, exist_ok=True)
    bg, fg, accent, card = SITE_STYLES.get(str(inputs.get("style") or "Dark"), SITE_STYLES["Dark"])
    name = html.escape(str(inputs.get("name") or "My brand"))
    tagline = html.escape(str(inputs.get("tagline") or ""))
    about = [html.escape(x.strip()) for x in str(inputs.get("features") or "").splitlines() if x.strip()][:6]
    cta = html.escape(str(inputs.get("cta") or "Get started"))
    imgs = []
    for i, p in enumerate(_media(inputs, uploads, "image", IMAGE_EXT + VIDEO_EXT)):
        dst = f"media_{i}{p.suffix.lower()}"
        shutil.copyfile(p, site / dst)
        imgs.append(dst)
    def media(src):
        return f'<video src="{src}" autoplay muted loop playsinline></video>' if src.endswith(VIDEO_EXT) else f'<img src="{src}" alt="">'
    hero = media(imgs[0]) if imgs else ""
    gallery = "".join(f"<figure>{media(s)}</figure>" for s in imgs[1:])
    feats = "".join(f"<div class=card><b>{f.split(':')[0]}</b><p>{f.split(':', 1)[1].strip() if ':' in f else ''}</p></div>" for f in about)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name}</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:{bg};color:{fg};font:16px/1.6 system-ui,Segoe UI,Inter,sans-serif}}
header{{display:flex;justify-content:space-between;align-items:center;padding:20px 6vw}}header b{{font-size:20px;letter-spacing:.04em}}
a.btn{{display:inline-block;padding:12px 22px;border-radius:12px;background:{accent};color:{bg};text-decoration:none;font-weight:700}}
.hero{{display:grid;grid-template-columns:1.1fr 1fr;gap:5vw;align-items:center;padding:6vh 6vw}}
.hero h1{{font-size:clamp(36px,6vw,72px);line-height:1.02;margin:0 0 16px}}.hero p{{font-size:20px;opacity:.8;margin:0 0 26px}}
.hero img,.hero video,figure img,figure video{{width:100%;border-radius:20px;display:block;object-fit:cover}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;padding:4vh 6vw}}
.card{{background:{card};border-radius:18px;padding:22px}}.card b{{color:{accent};font-size:18px}}.card p{{opacity:.8;margin:6px 0 0}}
.gallery{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;padding:4vh 6vw}}figure{{margin:0}}
.end{{text-align:center;padding:10vh 6vw}}.end h2{{font-size:clamp(28px,4vw,48px);margin:0 0 20px}}footer{{padding:30px 6vw;opacity:.5;font-size:13px}}
@media(max-width:800px){{.hero{{grid-template-columns:1fr}}}}
</style></head><body>
<header><b>{name}</b><a class="btn" href="#start">{cta}</a></header>
<section class="hero"><div><h1>{name}</h1><p>{tagline}</p><a class="btn" href="#start">{cta}</a></div><div>{hero}</div></section>
{f'<section class="cards">{feats}</section>' if feats else ''}
{f'<section class="gallery">{gallery}</section>' if gallery else ''}
<section class="end" id="start"><h2>{tagline or name}</h2><a class="btn" href="#">{cta}</a></section>
<footer>{name} · built with OpenSfield</footer></body></html>"""
    (site / "index.html").write_text(page, encoding="utf-8")
    progress(0.99)
    return [("site/index.html", "html")]


TOOLS: dict[str, Callable] = {"montage": montage, "reel": reel, "subject-cuts": subject_cuts, "virality": virality,
                              "tiktok-export": tiktok_export, "website": website}


def mux(video: Path, audio: Path, dst: Path) -> Path:
    """Lay an audio track over a video, looping the video until the audio ends (narration over B-roll)."""
    import imageio_ffmpeg
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(video), "-i", str(audio),
           "-map", "0:v", "-map", "1:a", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"mux failed: {r.stderr[-300:]}")
    return dst
