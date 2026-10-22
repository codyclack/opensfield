"""Render example outputs for the local CPU tools in app/fx_tools.py (no ComfyUI, no credits) into examples/.

    uv run --extra fx python scripts/make_local_examples.py
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import fx, fx_tools, runner  # noqa: E402

EX = ROOT / "examples"
UP = runner.UPLOADS
UP.mkdir(parents=True, exist_ok=True)


def up(name):
    shutil.copyfile(EX / name, UP / f"ex_{name.replace('/', '_')}")
    return f"ex_{name.replace('/', '_')}"


def run(tool, inputs, keep):
    out = ROOT / "outputs" / f"local_{tool}"
    made = fx_tools.TOOLS[tool](inputs, UP, out, lambda p: None)
    for (name, kind), dst in zip(made, keep):
        if dst:
            (EX / dst).parent.mkdir(parents=True, exist_ok=True)
            if kind == "html":
                shutil.copytree(out / Path(name).parent, EX / dst, dirs_exist_ok=True)
            else:
                shutil.copyfile(out / name, EX / dst)
            print("wrote", dst)


clips = {"video": up("models/kling-v3-video.mp4"), "video_2": up("models/seedance2-5-t2v-1080p.mp4"),
         "video_3": up("models/grok-imagine-video-1-5-lite-t2v.mp4"), "video_4": up("models/kling-o3-t2v.mp4")}
run("montage", {**clips, "ratio": "9:16", "transition": "Crossfade", "seconds": 2}, ["fx_montage.mp4"])
run("reel", {**clips, "look": "vhs", "bpm": 120, "ratio": "9:16"}, ["fx_reel_vhs.mp4"])
faces = {"image": up("char_a.png"), "image_2": up("char_b.png"), "image_3": up("influencer_cafe.png"), "image_4": up("soul_id.png")}
run("subject-cuts", {**faces, "mode": "Face", "bpm": 120, "loops": 2}, ["fx_facecut.mp4"])
products = {"image": up("t2i_flux3_sneakers.png"), "image_2": up("models/bfl-flux3-t2i.png"), "image_3": up("models/openai-gpt-image-2-t2i.png"),
            "image_4": up("models/recraft-v4-1-t2i.png")}
run("subject-cuts", {**products, "mode": "Sticker", "bpm": 110, "loops": 2}, ["fx_stickercut.mp4"])
fx.process_video(UP / up("driving_dance.mp4"), EX / "fx_tracelab.mp4", "tracelab", max_seconds=6) if "tracelab" in fx.CTX_MODES else None
print("wrote fx_tracelab.mp4")
run("virality", {"video": up("models/kling-v3-video.mp4")}, ["fx_virality.png"])
run("tiktok-export", {"video": up("models/seedance2-5-t2v-1080p.mp4"), "fit": "Blur fill", "caption": "Rainy night drop", "hashtags": "sneakers streetwear"},
    ["fx_tiktok.mp4", None])
run("website", {"name": "Puddle Runners", "tagline": "Sneakers made for wet city nights.", "cta": "Shop the drop",
                "features": "Grip: rubber that holds on wet stone\nLight: 280 g per shoe\nClean: wipes off in seconds",
                "image": up("models/bfl-flux3-t2i.png"), "image_2": up("models/kling-v3-video.mp4"), "image_3": up("models/openai-gpt-image-2-t2i.png"),
                "style": "Dark"}, ["site_example"])
