"""Builds demo/OpenSfield_demo.mp4 (1080p, ~110 s, captions + music, no voice-over) from the real renders in examples/
and screenshots of the app in demo/frames/.

    uv run --no-project --with pillow --with numpy --with opencv-python-headless --with imageio-ffmpeg python demo/make_demo.py

Screenshots: start the app (uv run uvicorn app.main:app --port 8765) and capture with headless Edge, e.g.
    msedge --headless=new --window-size=1920,1080 --virtual-time-budget=6000 --screenshot=demo/frames/home_genjutsu.png "http://127.0.0.1:8765/#s=Genjutsu"
"""
import subprocess
import sys
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
EX, SH = ROOT / "examples", ROOT / "demo" / "frames"
OUT = ROOT / "demo" / "OpenSfield_demo.mp4"
W, H, FPS, FADE = 1920, 1080, 30, 0.35
BG, LIME, YEL, WHITE, MUTED, INK = (23, 18, 32), (209, 254, 23), (242, 255, 89), (247, 247, 248), (167, 157, 179), (33, 25, 39)
BOLD, REG = "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeui.ttf"
font = lambda p, s: ImageFont.truetype(p, s)  # noqa: E731


def make_bg():
    a = np.empty((H, W, 3), np.uint8)
    a[:] = BG[::-1]
    for dy in (0, 1):
        for dx in (0, 1):
            a[16 + dy::32, 16 + dx::32] = (66, 50, 62)
    return a


BGIMG = make_bg()


class Layer:
    """A pre-rendered RGBA overlay, blended only inside its bounding box."""

    def __init__(self, draw_fn):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_fn(ImageDraw.Draw(img))
        a = np.array(img)
        ys, xs = np.where(a[..., 3] > 0)
        self.y0, self.y1, self.x0, self.x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        self.rgb = a[self.y0:self.y1, self.x0:self.x1, [2, 1, 0]].astype(np.float32)
        self.al = a[self.y0:self.y1, self.x0:self.x1, 3:4].astype(np.float32) / 255

    def on(self, frame, op=1.0):
        if op <= 0:
            return
        reg = frame[self.y0:self.y1, self.x0:self.x1].astype(np.float32)
        al = self.al * op
        frame[self.y0:self.y1, self.x0:self.x1] = (reg * (1 - al) + self.rgb * al).astype(np.uint8)


def marker(d, xy, text, size, pad=14):
    f = font(BOLD, size)
    x0, y0, x1, y1 = d.textbbox(xy, text, font=f)
    d.rounded_rectangle((x0 - pad, y0 - pad // 2, x1 + pad, y1 + pad // 2), 10, fill=YEL)
    d.text(xy, text, font=f, fill=INK)


def caption(text, sub=None):
    def draw(d):
        d.rounded_rectangle((120, 900, 1800, 1010), 18, fill=(23, 18, 32, 225), outline=(255, 255, 255, 40))
        d.rounded_rectangle((120, 900, 130, 1010), 5, fill=LIME)
        d.text((160, 918 if sub else 935), text, font=font(BOLD, 40), fill=WHITE)
        if sub:
            d.text((160, 966), sub, font=font(REG, 28), fill=MUTED)
    return Layer(draw)


def title(text, y=70, size=64, x=120):
    return Layer(lambda d: marker(d, (x, y), text, size))


def label(text, x, y, size=30, color=LIME, anchor="la"):
    return Layer(lambda d: d.text((x, y), text, font=font(BOLD, size), fill=color, anchor=anchor))


class Clip:
    def __init__(self, path, w=None, h=None):
        cap = cv2.VideoCapture(str(path))
        self.fps, self.f = cap.get(cv2.CAP_PROP_FPS) or 24, []
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            if w or h:
                sw, sh = fr.shape[1], fr.shape[0]
                s = (w / sw) if w else (h / sh)
                fr = cv2.resize(fr, (round(sw * s), round(sh * s)), interpolation=cv2.INTER_AREA)
            self.f.append(fr)
        self.h, self.w = self.f[0].shape[:2]

    def at(self, t):
        return self.f[int(t * self.fps) % len(self.f)]


def still(path, w=None, h=None):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if w or h:
        s = (w / im.shape[1]) if w else (h / im.shape[0])
        im = cv2.resize(im, (round(im.shape[1] * s), round(im.shape[0] * s)), interpolation=cv2.INTER_AREA)
    return im


def cover(img, w, h):
    """Scale to fill w x h and center-crop (no distortion)."""
    s = max(w / img.shape[1], h / img.shape[0])
    im = cv2.resize(img[..., :3], (round(img.shape[1] * s), round(img.shape[0] * s)), interpolation=cv2.INTER_AREA)
    y, x = (im.shape[0] - h) // 2, (im.shape[1] - w) // 2
    return np.ascontiguousarray(im[y:y + h, x:x + w])


def paste(frame, img, x, y, border=True):
    h, w = img.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, W), min(y + h, H)
    if x1 > x0 and y1 > y0:
        frame[y0:y1, x0:x1] = img[y0 - y:y1 - y, x0 - x:x1 - x, :3]
        if border:
            cv2.rectangle(frame, (x0, y0), (x1 - 1, y1 - 1), LIME[::-1], 2)


def kenburns(img, t, dur, z0=1.0, z1=1.08):
    z = z0 + (z1 - z0) * t / dur
    cw, ch = W / z, H / z
    x0, y0 = (img.shape[1] - cw) / 2, (img.shape[0] - ch) / 2
    M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR)


def box(d, x, y, w, h, head, body, accent):
    d.rounded_rectangle((x, y, x + w, y + h), 16, fill=(42, 34, 51, 255), outline=accent, width=3)
    d.text((x + 20, y + 18), head, font=font(BOLD, 28), fill=accent)
    for i, line in enumerate(body):
        d.text((x + 20, y + 66 + i * 34), line, font=font(REG, 26), fill=WHITE)


scenes = []  # (duration, render(t) -> frame)


def scene(dur):
    def deco(fn):
        scenes.append((dur, fn))
        return fn
    return deco


# 1. title
L1a = Layer(lambda d: marker(d, (120, 300), "OPENSFIELD", 190, 28))
L1b = label("Open-source Higgsfield, rebuilt on ComfyUI", 124, 590, 60, WHITE)
L1c = label("Open weights + partner models  ·  MIT  ·  #OpenSourceHiggsfield", 124, 690, 40, LIME)


@scene(6)
def s1(t):
    f = BGIMG.copy()
    L1a.on(f, min(1, t / 0.6)); L1b.on(f, min(1, max(0, t - 0.5) / 0.6)); L1c.on(f, min(1, max(0, t - 1.0) / 0.6))
    return f


# 2. how it is built
steps = [("1  Feature map", ["72 Higgsfield modules", "tiers, open stand-ins"], (255, 169, 49)),
         ("2  Manifest", ["inputs → node + field", "models, outputs"], (179, 157, 219)),
         ("3  Comfy template", ["official workflow", "converted to API format"], (100, 181, 246)),
         ("4  comfy-sdk", ["runs it on Comfy Cloud", "or a local ComfyUI"], (129, 199, 132)),
         ("5  OpenSfield app", ["node-graph UI", "real example renders"], (209, 254, 23))]
L2t = title("EVERY FEATURE = A MANIFEST + A WORKFLOW")
L2boxes = [Layer(lambda d, i=i, s=s: box(d, 80 + i * 360, 330, 320, 190, s[0], s[1], s[2])) for i, s in enumerate(steps)]
L2arrows = [Layer(lambda d, i=i: d.text((410 + i * 360 - 8, 395), "→", font=font(BOLD, 56), fill=MUTED)) for i in range(4)]
L2c = caption("Higgsfield has about 100 models, 87 viral effects and 10+ studios.", "We mapped all of it. 76 tools are verified end to end: open-weight workflows plus partner models.")


@scene(12)
def s2(t):
    f = BGIMG.copy()
    L2t.on(f)
    for i, b in enumerate(L2boxes):
        b.on(f, min(1, max(0, t - 0.8 - i * 1.4) / 0.5))
        if i < 4:
            L2arrows[i].on(f, min(1, max(0, t - 1.6 - i * 1.4) / 0.4))
    L2c.on(f, min(1, max(0, t - 1) / 0.6))
    return f


# 3. app tour (Higgsfield layout)
TOUR = [("ui_explore", "The Higgsfield layout: Explore, Image, Video, Audio and every studio in the top menu", "Feature banners and tiles, then rows of tools that play on hover"),
        ("ui_video", "Video: Seedance 2.5 by default, every video model in one picker", "Create Video, Text to Video, References, First & Last, Motion Control, Edit Video"),
        ("ui_viral", "Viral effects, UGC, click-to-ad, AI influencer: presets on Seedance 2.5", "The open LTX-2.5 version is one click away in the same model list"),
        ("ui_image", "Image: describe it in the bottom bar, pick GPT Image, Nano Banana, FLUX 3...", "Every result lands in History: download, save to Assets, reuse the settings"),
        ("ui_assets", "Assets and @Elements: characters, props and locations you reuse", "“From assets” on every input, ★ on every result")]
TOUR_IMG = [still(SH / f"{n}.png") for n, _, _ in TOUR]
for _im in TOUR_IMG:  # screenshots come from the preview server: hide its "Mock mode" chip
    _im[10:46, 1544:1642, :3] = (14, 12, 12)
TOUR_CAP = [caption(a, b) for _, a, b in TOUR]
SEG = 4.0


@scene(20)
def s3(t):
    i = min(len(TOUR) - 1, int(t // SEG))
    f = kenburns(TOUR_IMG[i][..., :3], t - i * SEG, SEG, 1.0, 1.04)
    TOUR_CAP[i].on(f, min(1, (t - i * SEG) / 0.4))
    return f


# 4. same prompt, eight models
MODELS8 = [("FLUX 3", "bfl-flux3-t2i"), ("NANO BANANA 2.1", "nano-banana-2-1-t2i"), ("GPT IMAGE 2", "openai-gpt-image-2-t2i"), ("RECRAFT 4.1", "recraft-v4-1-t2i"),
           ("KLING 3.0", "kling-v3-t2i"), ("IDEOGRAM 4.5", "ideogram-v4-5-t2i"), ("KREA 3", "krea3-t2i"), ("QWEN IMAGE 3", "qwen3-t2i")]
M8 = [cover(still(EX / "models" / f"{f}.png"), 420, 250) for _, f in MODELS8]
L4t = title("ONE PROMPT, EIGHT MODELS", 60, 56)
L4l = [label(n, 60 + (i % 4) * 450 + 210, 195 + (i // 4) * 330, 24, LIME, "ma") for i, (n, _) in enumerate(MODELS8)]
L4c = caption("Same prompt, switch the model: FLUX 3, Nano Banana, GPT Image, Recraft and more", "Prompt: “a pair of white sneakers on a wet city street at dusk” · each run through the app")


@scene(12)
def s4(t):
    f = BGIMG.copy(); L4t.on(f)
    for i, m in enumerate(M8):
        k = min(1, max(0, t - 0.3 - i * 0.35) / 0.4)
        if k > 0:
            paste(f, m, 60 + (i % 4) * 450, 230 + (i // 4) * 330)
            L4l[i].on(f, k)
    L4c.on(f, min(1, t / 0.5))
    return f


# 4b. partner video wall
VIDS = [("GROK IMAGINE 1.5 LITE", "grok-imagine-video-1-5-lite-t2v"), ("KLING O3", "kling-o3-t2v"), ("SEEDANCE 2.5", "seedance2-5-t2v-1080p"), ("KLING 3.0", "kling-v3-video")]
CV = [Clip(EX / "models" / f"{f}.mp4", w=800) for _, f in VIDS]
L4bt = title("PARTNER VIDEO MODELS", 60, 56)
L4bl = [label(n, 60 + (i % 2) * 920 + 400, 168 + (i // 2) * 360, 24, LIME, "ma") for i, (n, _) in enumerate(VIDS)]
L4bc = caption("Grok, Kling, MiniMax, Seedance, Wan, Luma and more through Comfy API nodes", "Each tool is generated from Comfy's official template, so the form always matches the model")


@scene(12)
def s4b(t):
    f = BGIMG.copy(); L4bt.on(f)
    for i, c in enumerate(CV):
        fr = c.at(t)
        fr = cover(fr, 640, 330)
        paste(f, fr, 140 + (i % 2) * 920 - 0, 200 + (i // 2) * 360)
        L4bl[i].on(f)
    L4bc.on(f, min(1, t / 0.5))
    return f


# 5. motion transfer
C5 = Clip(EX / "motion_transfer_compare.mp4", w=1600)
L5t = title("GENJUTSU: MOTION TRANSFER", 60, 56)
L5l = label("RESULT: NEW CHARACTER", 160 + 190 * 1.0 - 10, 150, 26, LIME, "ma")
L5r = label("DRIVING CLIP (AI-GENERATED)", 160 + 1150, 150, 26, LIME, "ma")
L5c = caption("Wan Animate 2 · character image + driving video → same moves", "Rendered on Comfy Cloud with open weights · all people are fictional")


@scene(10)
def s5(t):
    f = BGIMG.copy(); L5t.on(f); L5l.on(f); L5r.on(f)
    paste(f, C5.at(t), 160, 190); L5c.on(f)
    return f


# 6. first/last frame
C6 = Clip(EX / "first_last_frame_morph.mp4", h=720)
L6t = title("VIRAL-STYLE TRANSITION", 60, 56)
L6a = Layer(lambda d: [d.text((1020, 280), "LTX-2.5 first / last frame", font=font(BOLD, 44), fill=WHITE),
                       d.text((1020, 350), "Two stills in, one morph out.", font=font(REG, 36), fill=MUTED),
                       d.text((1020, 410), "Viral Hub effects: 6 of 87 presets", font=font(REG, 36), fill=MUTED),
                       d.text((1020, 460), "are built (on LTX-2.5 image-to-video).", font=font(REG, 36), fill=MUTED)])
L6c = caption("Spin, flash of light, new outfit and person", "First frame and last frame are both generated stills")


@scene(8)
def s6(t):
    f = BGIMG.copy(); L6t.on(f); paste(f, C6.at(t), 300, 150); L6a.on(f, min(1, t / 0.6)); L6c.on(f)
    return f


# 7. character replacement
C7a, C7b = Clip(EX / "driving_dance.mp4", w=880), Clip(EX / "replace_character_a.mp4", w=880)
L7t = title("CHARACTER REPLACEMENT", 60, 56)
L7l, L7r = label("SOURCE VIDEO", 60 + 440, 170, 26, LIME, "ma"), label("SAME SHOT, NEW CHARACTER", 980 + 440, 170, 26, LIME, "ma")
L7c = caption("SCAIL-2 · swap who is in the footage, keep the motion", "Source: an AI-generated clip · replacement: a generated character image")


@scene(9)
def s7(t):
    f = BGIMG.copy(); L7t.on(f); L7l.on(f); L7r.on(f)
    paste(f, C7a.at(t), 60, 220); paste(f, C7b.at(t), 980, 220 + (C7a.h - C7b.h) // 2); L7c.on(f)
    return f


# 8. tools
A, B = still(EX / "char_a.png", h=380), still(EX / "image_edit_yellow_hoodie.png", h=380)
CUT = still(EX / "bg_remove_cutout.png", h=380)
yy, xx = np.indices((CUT.shape[0], CUT.shape[1]))
checker = (yy // 24 + xx // 24) % 2
chk = np.where(checker[..., None] == 0, 200, 150).astype(np.uint8).repeat(3, 2)
al = CUT[..., 3:4].astype(np.float32) / 255
CUTC = (CUT[..., :3] * al + chk * (1 - al)).astype(np.uint8)
C8 = Clip(EX / "text_to_video_alley.mp4", w=560)
L8t = title("MORE MODULES, ALL REAL RENDERS", 60, 56)
L8l = [label("IMAGE EDIT (QWEN)", 40 + 536 // 2 + 40, 600, 26, LIME, "ma"), label("BACKGROUND REMOVAL", 40 + 536 + 100 + 253 // 2 + 120, 600, 26, LIME, "ma"),
       label("TEXT-TO-VIDEO (LTX-2.5)", 1580, 600, 26, LIME, "ma")]
L8c = caption("Edit · cut-out · text-to-video, plus inpaint, video edit, effects, music and 3D", "Prompt: \"change the black hoodie to yellow\" · every output is in examples/")


@scene(9)
def s8(t):
    f = BGIMG.copy(); L8t.on(f)
    paste(f, A, 80, 190); paste(f, B, 80 + A.shape[1] + 30, 190)
    paste(f, CUTC, 720 + 60, 190)
    paste(f, C8.at(t), 1300, 190 + (380 - C8.h) // 2)
    for l in L8l:
        l.on(f)
    L8c.on(f)
    return f


# 9. end
L9 = Layer(lambda d: [marker(d, (120, 170), "76 TOOLS RUN FOR REAL", 78),
                      d.text((124, 330), "146 in the catalog: 59 more wired from Comfy templates, 11 not built", font=font(BOLD, 44), fill=WHITE),
                      d.text((124, 410), "Open weights + partner models  ·  MIT  ·  built on comfy-sdk", font=font(REG, 40), fill=MUTED),
                      d.text((124, 560), "github.com/codyclack/opensfield", font=font(BOLD, 72), fill=LIME),
                      d.text((124, 680), "#OpenSourceHiggsfield", font=font(BOLD, 56), fill=WHITE),
                      d.text((124, 820), "Examples were rendered through the app on Comfy Cloud. Partner models use Comfy credits.", font=font(REG, 30), fill=MUTED)])


@scene(8)
def s9(t):
    f = BGIMG.copy(); L9.on(f, min(1, t / 0.7))
    return f


def main():
    total = sum(d for d, _ in scenes)
    print(f"{len(scenes)} scenes, {total} s", flush=True)
    music = EX / "music_lofi.mp3"
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-stream_loop", "-1", "-i", str(music), "-t", str(total), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "medium",
           "-c:a", "aac", "-b:a", "160k", "-af", f"volume=0.85,afade=t=in:d=1,afade=t=out:st={total - 3}:d=3", str(OUT)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i, (dur, fn) in enumerate(scenes):
        for n in range(int(dur * FPS)):
            t = n / FPS
            fr = fn(t)
            k = min(1.0, t / FADE, (dur - t) / FADE)
            if k < 1:
                fr = (fr.astype(np.float32) * k + BGIMG * (1 - k)).astype(np.uint8)
            p.stdin.write(np.ascontiguousarray(fr).tobytes())
        print(f"scene {i + 1} done", flush=True)
    p.stdin.close()
    p.wait()
    print("wrote", OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
