"""Reads features/*/manifest.json and derives the input form for each feature.

A built feature lists its real slots in manifest["workflow"]["inputs"]. Until then
the form is derived from the feature's base graphs so the whole catalog is usable
(in mock mode) from day one.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEATURES_DIR = ROOT / "features"

STUDIO_ORDER = [
    "Genjutsu", "Cinema Studio", "Reshoot", "Viral Hub", "Soul", "Image models", "Image tools",
    "Video tools", "Video models", "Audio", "Marketing", "Match Cut + Tracelab", "Platform",
]

MEDIA = {"image", "video", "audio"}

INPUT_SPECS = {
    "prompt": dict(label="Prompt", kind="text"),
    "brief": dict(label="Brief", kind="text"),
    "aspect": dict(label="Aspect", kind="choice", options=["16:9", "9:16", "1:1", "4:3", "3:4"], default="16:9"),
    "duration": dict(label="Duration", kind="choice", options=["3s", "5s", "8s", "10s"], default="5s"),
    "seed": dict(label="Seed", kind="seed", default=0),
    "image": dict(label="Image", kind="image", required=True),
    "reference": dict(label="Reference image", kind="image", required=True),
    "character": dict(label="Character image", kind="image", required=True),
    "start_image": dict(label="Start frame", kind="image", required=True),
    "end_image": dict(label="End frame", kind="image", required=True),
    "image_b": dict(label="Image B", kind="image", required=True),
    "mask": dict(label="Mask", kind="image", required=False),
    "driving_video": dict(label="Driving video", kind="video", required=True),
    "control_video": dict(label="Control video", kind="video", required=True),
    "video": dict(label="Video", kind="video", required=True),
    "audio": dict(label="Audio", kind="audio", required=True),
    "voice": dict(label="Voice", kind="choice", options=["narrator", "young-f", "young-m", "deep-m", "clone-from-audio"], default="narrator"),
    "scale": dict(label="Scale", kind="choice", options=["2x", "4x"], default="2x"),
    "blend": dict(label="Blend A to B", kind="number", default=0.5, min=0, max=1, step=0.05),
    "fx_mode": dict(label="Effect", kind="choice", options=["crt", "crt-glitch", "vhs", "glitch", "nokia", "retropop", "night-vision"], default="crt"),
    "palette": dict(label="Palette", kind="choice", options=["black-hot", "white-hot", "rainbow", "iron"], default="black-hot"),
    "target": dict(label="Track target", kind="text", default="face"),
}

# input names contributed by each base graph, in display order
BASE_INPUTS = {
    "t2i": ["prompt", "aspect", "seed"],
    "ref_edit": ["reference", "prompt"],
    "flux_redux_blend": ["image", "image_b", "blend"],
    "wan_animate2": ["character", "driving_video", "prompt"],
    "ltx25_i2v": ["start_image", "prompt", "duration"],
    "ltx25_t2v": ["prompt", "aspect", "duration"],
    "ltx25_flf2v": ["start_image", "end_image", "prompt", "duration"],
    "ltx23_ic_lora": ["control_video", "prompt"],
    "ltx23_audio": ["start_image", "audio", "prompt"],
    "fill": ["image", "mask", "prompt"],
    "upscale": ["image", "scale"],
    "matte": ["image"],
    "planner_llm": ["brief"],
    "tts_audio": ["prompt", "voice"],
    "hunyuan3d": ["image"],
    "postfx": ["video", "fx_mode"],
    "thermal": ["video", "palette"],
    "moondream_hud": ["video", "target"],
    "stitch": [],
}

VIDEO_BASES = {"wan_animate2", "ltx25_i2v", "ltx25_t2v", "ltx25_flf2v", "ltx23_ic_lora", "ltx23_audio",
               "postfx", "thermal", "moondream_hud", "stitch"}


def derive_inputs(base: list[str]) -> list[dict]:
    names: list[str] = []
    for b in base:
        for n in BASE_INPUTS.get(b, []):
            if n not in names:
                names.append(n)
    if "video" in names and "driving_video" in names:
        names.remove("video")  # driving_video already supplies the clip
    return [{"name": n, **INPUT_SPECS[n]} for n in names]


def output_kind(base: list[str]) -> str:
    if any(b in VIDEO_BASES for b in base):
        return "video"
    if base == ["tts_audio"]:
        return "audio"
    if "hunyuan3d" in base:
        return "3d"
    return "image"


ENGINES = [("seedance2_5", "Seedance 2.5"), ("seedance2_0_mini", "Seedance 2.0 Mini"), ("seedance2_0", "Seedance 2.0"), ("seedance1_5", "Seedance 1.5"),
           ("kling_o3", "Kling O3"), ("kling_v3", "Kling 3.0"), ("kling2_6", "Kling 2.6"), ("kling", "Kling"), ("minimax", "MiniMax H3"), ("grok", "Grok Imagine"),
           ("nano_banana", "Nano Banana"), ("gpt_image", "GPT Image"), ("flux3", "FLUX 3"), ("ideogram", "Ideogram"), ("recraft", "Recraft"),
           ("seedream", "Seedream"), ("krea3", "Krea 3"), ("qwen3", "Qwen Image 3"), ("wan3", "Wan 3.0"), ("wan2_6", "Wan 2.6"), ("happyhorse", "HappyHorse"),
           ("luma", "Luma Ray"), ("pixverse", "PixVerse"), ("vidu", "Vidu"), ("gemini", "Gemini"), ("elevenlabs", "ElevenLabs"), ("fishaudio", "Fish Audio"),
           ("heygen", "HeyGen"), ("topaz", "Topaz"), ("meshy", "Meshy"), ("tripo", "Tripo"), ("bria", "Bria"),
           ("ltx-2.5", "LTX-2.5"), ("ltx-2.3", "LTX-2.3"), ("ltx", "LTX"), ("wan_animate", "Wan Animate 2"), ("scail", "SCAIL-2"), ("wan", "Wan 2.x"),
           ("z_image", "Z-Image Turbo"), ("flux", "FLUX"), ("krea", "Krea"), ("qwen_image_edit", "Qwen Image Edit"), ("qwen_image", "Qwen Image"),
           ("seedvr", "SeedVR2"), ("birefnet", "BiRefNet"), ("ace_step", "ACE-Step"), ("chatterbox", "Chatterbox"), ("hunyuan3d", "Hunyuan3D")]


def engine(wf: dict, local) -> str:
    """Short human name of the open model behind a module, from its template / model file names."""
    if local:
        return "Local CPU (OpenCV + ffmpeg)"
    hay = " ".join([wf.get("template", "")] + wf.get("models", [])).lower().replace("-", "_")
    for key, name in ENGINES:
        if key.replace("-", "_") in hay:
            return name
    return ""


def _enrich(m: dict) -> dict:
    wf = m.get("workflow") or {}
    api = wf.get("api")
    m["inputs"] = wf.get("inputs") or derive_inputs(m["base"])
    m["output_kind"] = wf.get("output_kind") or output_kind(m["base"])
    m["examples"] = wf.get("examples", [])  # real renders, served under /examples
    m["local"] = wf.get("local")  # e.g. {"mode_input": "palette"} for CPU effects run by app/fx.py
    m["engine"] = engine(wf, m["local"])
    m["runnable"] = bool(api and (ROOT / api).exists()) or bool(m["local"])
    return m


def load_features() -> list[dict]:
    feats = [_enrich(json.loads(p.read_text(encoding="utf-8"))) for p in sorted(FEATURES_DIR.glob("*/manifest.json"))]
    rank = {s: i for i, s in enumerate(STUDIO_ORDER)}
    feats.sort(key=lambda f: (rank.get(f["studio"], 99), f["id"]))
    return feats
