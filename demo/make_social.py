"""Profile picture and banner for an OpenSfield social account (demo/social/).

    uv run --no-project --with pillow python demo/make_social.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "demo" / "social"
LIME, INK, BG, WHITE, MUTED = (209, 254, 23), (19, 21, 23), (19, 21, 23), (247, 247, 248), (167, 167, 175)
BOLD, REG = "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeui.ttf"


def mark(size, s=4):
    """The app's logo mark (app/static/index.html): two dots joined by an S curve on a lime square, drawn at s x then reduced."""
    n = size * s
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = n / 32
    d.rounded_rectangle((0, 0, n - 1, n - 1), radius=9 * k, fill=LIME)
    pts = []
    for i in range(101):  # cubic bezier M10 11 C18 11 14 21 22 21
        t = i / 100
        x = (1 - t) ** 3 * 10 + 3 * (1 - t) ** 2 * t * 18 + 3 * (1 - t) * t ** 2 * 14 + t ** 3 * 22
        y = (1 - t) ** 3 * 11 + 3 * (1 - t) ** 2 * t * 11 + 3 * (1 - t) * t ** 2 * 21 + t ** 3 * 21
        pts.append((x * k, y * k))
    r = k  # stroke the curve with a round brush: a wide PIL polyline frays at the joints
    for i in range(len(pts) - 1):
        for j in range(8):
            x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * j / 8
            y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * j / 8
            d.ellipse((x - r, y - r, x + r, y + r), fill=INK)
    for cx, cy in ((10, 11), (22, 21)):
        r = 3.2 * k
        d.ellipse((cx * k - r, cy * k - r, cx * k + r, cy * k + r), fill=INK)
    return im.resize((size, size), Image.LANCZOS)


def avatar():
    im = Image.new("RGB", (400, 400), LIME)
    m = mark(400)
    im.paste(m, (0, 0), m)
    im.save(OUT / "avatar_400.png")


def banner():
    W, H = 1500, 500
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for y in range(16, H, 32):  # the app's dot grid
        for x in range(16, W, 32):
            d.point((x, y), fill=(52, 54, 60))
    thumbs = ["game-dump", "3d-figure", "comic-book", "renaissance"]
    tw, th, x0 = 150, 225, W - 4 * 158 - 40
    for i, s in enumerate(thumbs):  # a strip of real app examples on the right, clear of the text
        p = ROOT / "examples" / "apps" / f"{s}.png"
        if p.exists():
            t = Image.open(p).convert("RGB")
            t = t.resize((tw, round(t.height * tw / t.width)), Image.LANCZOS).crop((0, 0, tw, th))
            y = 140 + (i % 2) * 40
            im.paste(t, (x0 + i * 158, y))
            d.rectangle((x0 + i * 158, y, x0 + i * 158 + tw - 1, y + th - 1), outline=LIME, width=2)
    m = mark(88)
    im.paste(m, (70, 150), m)
    d.text((176, 150), "OPENSFIELD", font=ImageFont.truetype(BOLD, 72), fill=WHITE)
    d.text((72, 270), "Open-source Higgsfield, rebuilt on ComfyUI", font=ImageFont.truetype(BOLD, 30), fill=LIME)
    d.text((72, 316), "146 tools · 83 apps · open weights + partner models · MIT", font=ImageFont.truetype(REG, 24), fill=MUTED)
    im.save(OUT / "banner_1500x500.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    avatar()
    banner()
    print("wrote", OUT)
