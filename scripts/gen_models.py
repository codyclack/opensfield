"""Generate one runnable tool per Higgsfield partner model from Comfy's official API-node templates.

For each template in MODELS: download its UI workflow from Comfy-Org/workflow_templates, convert it to API format with
Comfy Cloud's node catalog, auto-wire the prompt / media loaders / option widgets from the node specs, and write
features/<id>/workflow_{ui,api}.json plus registry/models_gen.json (read by registry/features.py and registry/wiring.py).

    uv run --with comfy-cli scripts/gen_models.py            # needs COMFY_API_KEY (reads Cloud's /api/object_info)
    ... --only api_seedance2_5_i2v_1080p,api_bfl_flux3_t2i   # a subset
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

from comfy_cli.workflow_to_api import WorkflowConversionError, convert_ui_to_api

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from export_api import fetch_object_info  # noqa: E402

RAW = "https://raw.githubusercontent.com/Comfy-Org/workflow_templates/main/templates/{}.json"
UA = {"User-Agent": "opensfield/0.1"}

# (template, studio, group). Group = what the model switcher on the create page lists together.
MODELS = [
    # image generation
    ("api_nano_banana_2_1_t2i", "Image models", "Text to image"), ("api_google_nano_banana2_text_to_image", "Image models", "Text to image"),
    ("api_nano_banana_2_lite_t2i", "Image models", "Text to image"), ("api_openai_gpt_image_2_t2i", "Image models", "Text to image"),
    ("api_openai_gpt_image_25_flare_t2i", "Image models", "Text to image"), ("api_openai_gpt_image_25_sunburst_t2i", "Image models", "Text to image"),
    ("api_bytedance_seedream_5_0_pro_t2i", "Image models", "Text to image"), ("api_bytedance_seedream_5_0_flash_t2i", "Image models", "Text to image"),
    ("api_bfl_flux3_t2i", "Image models", "Text to image"), ("api_grok_imagine_image_2_t2i", "Image models", "Text to image"),
    ("api_ideogram_v4_5_t2i", "Image models", "Text to image"), ("api_recraft_v4_1_t2i", "Image models", "Text to image"),
    ("api_kling_v3_t2i", "Image models", "Text to image"), ("api_kling_o3_image", "Image models", "Text to image"),
    ("api_krea3_t2i", "Image models", "Text to image"), ("api_qwen3_t2i", "Image models", "Text to image"),
    # image edit / reference
    ("api_nano_banana_2_1_image_edit", "Image models", "Image edit"), ("api_openai_gpt_image_2_image_edit", "Image models", "Image edit"),
    ("api_bytedance_seedream_5_0_flash_image_edit", "Image models", "Image edit"), ("api_bfl_flux3_image_edit", "Image models", "Image edit"),
    ("api_grok_imagine_image_2_image_edit", "Image models", "Image edit"), ("api_ideogram_v4_5_image_edit", "Image models", "Image edit"),
    ("api_qwen3_image_edit", "Image models", "Image edit"),
    # video: text to video
    ("api_seedance2_0_t2v", "Video models", "Text to video"), ("api_seedance2_0_mini_t2v", "Video models", "Text to video"),
    ("api_seedance2_5_t2v_1080p", "Video models", "Text to video"), ("api_kling_o3_t2v", "Video models", "Text to video"),
    ("api_minimax_h3_max_t2v", "Video models", "Text to video"), ("api_wan3_0_t2v", "Video models", "Text to video"),
    ("api_grok_imagine_video_1_5_lite_t2v", "Video models", "Text to video"), ("api_happyhorse1_1_t2v", "Video models", "Text to video"),
    ("api_bfl_flux3_t2v", "Video models", "Text to video"), ("api_google_gemini_omni_flash_1_1_t2v", "Video models", "Text to video"),
    ("api_luma_ray3_3_t2v", "Video models", "Text to video"), ("api_pixverse6_t2v", "Video models", "Text to video"),
    # video: image to video / reference
    ("api_seedance2_5_i2v_1080p", "Video models", "Image to video"), ("api_bytedance_seedance1_5_image_to_video", "Video models", "Image to video"),
    ("api_kling_v3_video", "Video models", "Image to video"), ("api_kling_o3_i2v", "Video models", "Image to video"),
    ("api_kling2_6_i2v", "Video models", "Image to video"), ("api_minimax_h3_max_i2v", "Video models", "Image to video"),
    ("api_minimax_h3_max_turbo_i2v", "Video models", "Image to video"), ("api_wan3_0_i2v", "Video models", "Image to video"),
    ("api_wan2_6_i2v", "Video models", "Image to video"), ("api_grok_imagine_video_1_5", "Video models", "Image to video"),
    ("api_happyhorse1_1_i2v", "Video models", "Image to video"), ("api_bfl_flux3_i2v", "Video models", "Image to video"),
    ("api_google_gemini_omni_flash_1_1_i2v", "Video models", "Image to video"), ("api_luma_ray3_3_i2v", "Video models", "Image to video"),
    ("api_pixverse6_i2v", "Video models", "Image to video"), ("api_vidu_q4_preview_i2v", "Video models", "Image to video"),
    ("api_seedance2_0_r2v", "Video models", "Reference to video"), ("api_seedance2_5_r2v", "Video models", "Reference to video"),
    ("api_minimax_h3_r2v", "Video models", "Reference to video"), ("api_wan3_0_r2v", "Video models", "Reference to video"),
    ("api_kling_v3_flf2v", "Video models", "First / last frame"), ("api_kling_o3_flf2v", "Video models", "First / last frame"),
    ("api_kling_motion_control3", "Genjutsu", "Motion control"), ("api_kling_o3_video_edit", "Video tools", "Video edit"),
    ("api_bria_remove_video_background_transparent", "Video tools", "Video background remover"),
    # tools
    ("api_topaz_image_enhance_wonder3_5", "Image tools", "Image upscale"), ("api_kling_vto", "Marketing", "Virtual try-on"),
    ("api_meshy7_1_image_to_model", "Image models", "Image to 3D"), ("api_tripo_p2_image_to_model", "Image models", "Image to 3D"),
    # audio
    ("api_elevenlabs_v4_text_to_speech", "Audio", "Text to speech"), ("api_fishaudio_text_to_speech", "Audio", "Text to speech"),
    ("api_heygen_text_to_speech", "Audio", "Text to speech"), ("api_fishaudio_voice_clone_tts", "Audio", "Voice clone"),
    ("api_sync_so_talking_image", "Video tools", "Lip sync"),
    # Higgsfield modules that map 1:1 onto a template: wired straight into the existing feature id (4th field)
    ("api_elevenlabs_text_to_sound_effects", "Audio", "Sound effects", "audio.sfx"),
    ("api_elevenlabs_speech_to_speech", "Audio", "Voice change", "audio.voice-change"),
    ("api_heygen_video_translate", "Audio", "Dubbing", "audio.dubbing"),
    ("api_sync_so_lip_sync_video", "Video tools", "Lip sync", "video.lipsync"),
    ("api_seedance2_5_video_extend", "Cinema Studio", "Extend video", "cinema.extend"),
    ("template_seedance_2_0_plus_llm_prompt_helper", "Cinema Studio", "AI Director", "cinema.director"),
    ("template_seedance2_0_viral_videos_character_swap", "Marketing", "Katana remix", "marketing.katana"),
]

LOADERS = {"LoadImage": ("image", "image"), "LoadVideo": ("video", "file"), "LoadAudio": ("audio", "audio")}
def saver_kind(cls: str):
    if cls == "PreviewImage" or cls.startswith("Save"):
        low = cls.lower()
        for key, kind in (("video", "video"), ("webm", "video"), ("audio", "audio"), ("glb", "3d"), ("3d", "3d"), ("model", "3d"), ("image", "image"), ("svg", "image"), ("webp", "image")):
            if key in low:
                return kind
    return None
SKIP_KEYS = {"control_after_generate", "unique_id"}
HIDE = {"output_format", "bit_depth", "color_space", "codec", "spacing_color", "spacing_width", "video_processing", "response_modalities",
        "thinking_level", "n", "custom_width", "custom_height", "background", "watermark", "top_p", "temperature", "volume", "direction",
        "apply_text_normalization", "speaker_frame", "speaker_x", "speaker_y", "model_name", "task_type", "safety_tolerance"}
ASPECT_RE = re.compile(r"^\d+:\d+")


def pretty(key: str) -> str:
    return re.sub(r"[_.]+", " ", key).strip().capitalize()


def slug(template: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"^api_", "", template).lower()).strip("-")


def spec_of(info: dict, cls: str, key: str):
    node = info.get(cls, {})
    for sect in ("required", "optional"):
        if key in node.get("input", {}).get(sect, {}):
            return node["input"][sect][key]
    return None


def dyn_spec(info: dict, cls: str, node_inputs: dict, key: str):
    """Spec of a dotted input like 'model.resolution' (a dynamic-combo child): look it up under the selected option."""
    parent, sub = key.split(".", 1)
    pspec = spec_of(info, cls, parent)
    if not pspec or len(pspec) < 2 or not isinstance(pspec[1], dict):
        return None
    for opt in pspec[1].get("options", []):
        if isinstance(opt, dict) and opt.get("key") == node_inputs.get(parent):
            inner = opt.get("inputs", {})
            for sect in ("required", "optional"):
                if sub in inner.get(sect, {}):
                    return inner[sect][sub]
    return None


def wire(api: dict, info: dict) -> dict:
    inputs, used, outputs, kind = [], set(), [], None
    for nid, n in api.items():
        k = saver_kind(n["class_type"])
        if k:
            outputs.append(nid)
            kind = kind or k
    # media loaders become upload inputs, labelled by what consumes them
    consumers = {}
    for nid, n in api.items():
        for key, v in n["inputs"].items():
            if isinstance(v, list) and len(v) == 2 and v[0] in api and api[v[0]]["class_type"] in LOADERS:
                consumers.setdefault(v[0], (nid, key))
    for nid, n in api.items():
        if n["class_type"] not in LOADERS:
            continue
        mk, field = LOADERS[n["class_type"]]
        name = f"{mk}_{len([i for i in inputs if i['kind'] == mk]) + 1}"
        label = pretty(consumers[nid][1].split(".")[-1]) if nid in consumers else pretty(mk)
        inputs.append(dict(name=name, label=label, kind=mk, node=nid, field=field, required=True))
        used.add(nid)
    # widgets of the partner (API) nodes
    for nid, n in api.items():
        meta = info.get(n["class_type"], {})
        feeds_save = any(isinstance(v, list) and v[0] == nid and saver_kind(api[o]["class_type"]) for o in api for v in api[o]["inputs"].values())
        if not (meta.get("api_node") or feeds_save) or n["class_type"] in LOADERS or saver_kind(n["class_type"]):
            continue
        for key, val in n["inputs"].items():
            if key in SKIP_KEYS or isinstance(val, list) or key.count(".") > 1:
                continue
            spec = dyn_spec(info, n["class_type"], n["inputs"], key) if "." in key else spec_of(info, n["class_type"], key)
            if not spec:
                continue
            short = key.split(".")[-1]
            typ, cfg = spec[0], (spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {})
            if short == "seed":
                inputs.append(dict(name="seed", label="Seed (0 = random)", kind="seed", node=nid, field=key, default=0))
            elif typ == "STRING" and (cfg.get("multiline") or "prompt" in short):
                if "negative" in short or "expansion" in short:
                    continue
                inputs.append(dict(name=short if short not in {i["name"] for i in inputs} else f"{short}_{nid}", label=pretty(short), kind="text", node=nid,
                                   field=key, required=short == "prompt"))
            elif (isinstance(typ, list) and typ) or (typ == "COMBO" and cfg.get("options")):
                raw = typ if isinstance(typ, list) else cfg["options"]
                opts = [str(o) for o in raw]
                if val not in raw or isinstance(val, bool):
                    continue
                kindopts = dict(options=opts, default=str(val) if not isinstance(val, bool) else str(val).lower())
                inputs.append(dict(name=short, label=pretty(short), kind="choice", node=nid, field=key, **kindopts))
            elif typ in ("INT", "FLOAT") and isinstance(val, (int, float)) and not isinstance(val, bool):
                lo, hi = cfg.get("min", 0), cfg.get("max", max(val * 4, 1))
                step = cfg.get("step", 1 if typ == "INT" else 0.1)
                inputs.append(dict(name=short, label=pretty(short), kind="number", node=nid, field=key, default=val, min=lo, max=hi, step=step))
    # a prompt that lives in a primitive string node (switch-based templates) is still the prompt
    if not any(i["kind"] == "text" for i in inputs):
        for nid, n in api.items():
            v = n["inputs"].get("value")
            if n["class_type"] in ("PrimitiveStringMultiline", "PrimitiveString") and isinstance(v, str) and len(v) > 30:
                inputs.append(dict(name="prompt", label="Prompt", kind="text", node=nid, field="value", required=True))
                break
    # multi-shot storyboards: shot 1's text is THE prompt and the other shots receive the same text, so no demo text leaks in
    shots = [i for i in inputs if i["kind"] == "text" and ("storyboard" in i["name"] or "shot" in i["name"])]
    if shots:
        main = shots[0]
        main.update(name="prompt", label="Prompt", required=True)
        main["also"] = [dict(node=t["node"], field=t["field"]) for t in shots[1:]]
        inputs = [i for i in inputs if i not in shots[1:]]
    # Higgsfield-style forms: hide plumbing (system prompts, codecs, counts) and keep the template's value for those
    inputs = [i for i in inputs if not (i["name"] in HIDE or "system" in i["name"])]
    seen_kinds, keep = set(), []
    for i in inputs:  # one prompt box and one seed per tool; later duplicates keep the template's value
        if i["kind"] == "seed" or (i["kind"] == "text" and i["name"].startswith("prompt")):
            key = i["kind"]
            if key in seen_kinds:
                continue
            seen_kinds.add(key)
        keep.append(i)
    inputs = keep
    has_media = any(i["kind"] in ("image", "video", "audio") for i in inputs)
    for i in inputs:
        if i["kind"] == "text":
            if i["name"] in ("prompt", "text") or not has_media:
                i["required"] = True
            else:
                i["clear_blank"] = True
    # the same option on several nodes (switch branches): one control, applied to all of them
    uniq, by_name = [], {}
    for i in inputs:
        first = by_name.get(i["name"])
        if first and i["kind"] in ("choice", "number") and first["kind"] == i["kind"]:
            first.setdefault("also", []).append(dict(node=i["node"], field=i["field"]))
            continue
        if first:
            i["name"] = f"{i['name']}_{i['node'].replace(':', '_')}"
        by_name[i["name"]] = i
        uniq.append(i)
    order = {"image": 0, "video": 0, "audio": 0, "text": 1, "choice": 2, "number": 3, "seed": 4}
    uniq.sort(key=lambda i: order[i["kind"]])
    return dict(inputs=uniq[:14], outputs=outputs, output_kind=kind or "image")


def titles() -> dict:
    req = urllib.request.Request(RAW.format("index"), headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return {t["name"]: t["title"] for cat in json.load(r) for t in cat.get("templates", [])}


def download(template: str) -> dict:
    req = urllib.request.Request(RAW.format(template), headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    cache = ROOT / "outputs" / "object_info_cloud.json"
    if cache.exists():
        info = json.loads(cache.read_text(encoding="utf-8"))
    else:
        info = fetch_object_info("https://cloud.comfy.org", os.environ.get("COMFY_API_KEY"))
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(json.dumps(info), encoding="utf-8")
    only = {s for s in args.only.split(",") if s}
    gen_path = ROOT / "registry" / "models_gen.json"
    gen = json.loads(gen_path.read_text(encoding="utf-8")) if gen_path.exists() else {"features": {}, "wiring": {}}
    ex_path = ROOT / "registry" / "models_examples.json"
    examples = json.loads(ex_path.read_text(encoding="utf-8")) if ex_path.exists() else {}
    names = titles()
    gen.setdefault("patch", {})
    for template, studio, group, *target in MODELS:
        if only and template not in only:
            continue
        fid = target[0] if target else f"model.{slug(template)}"
        try:
            ui = download(template)
            api = convert_ui_to_api(ui, info)
        except (WorkflowConversionError, Exception) as e:  # noqa: BLE001 - report and continue
            print(f"SKIP {template}: {type(e).__name__}: {str(e)[:160]}")
            continue
        w = wire(api, info)
        if not w["outputs"] or not any(i["kind"] in ("text", "image", "video", "audio") for i in w["inputs"]):
            print(f"SKIP {template}: nothing to wire ({len(api)} nodes)")
            continue
        d = ROOT / "features" / fid
        d.mkdir(parents=True, exist_ok=True)
        (d / "workflow_ui.json").write_text(json.dumps(ui), encoding="utf-8")
        (d / "workflow_api.json").write_text(json.dumps(api, indent=1), encoding="utf-8")
        title = names.get(template, slug(template)).replace(": ", " · ").replace(" (API)", "")
        if target:  # an existing Higgsfield module: keep its name and studio, mark it partner and group it
            gen["patch"][fid] = dict(track="partner", group=group, partner=[template], note=f"Runs {title} through Comfy Cloud API nodes (uses Comfy credits).")
        else:
            gen["features"][fid] = dict(id=fid, studio=studio, name=title, tier="B", base=[], higgsfield=group, track="partner",
                                   note="Partner model run through Comfy Cloud API nodes (uses Comfy credits).", count=1, partner=[template], status="planned", group=group)
        wiring = dict(template=template, output_kind=w["output_kind"], inputs=w["inputs"], outputs=w["outputs"], models=[template])
        if fid in examples:
            wiring.update(verified_via="App path: runner.run_comfy -> comfy-sdk -> Comfy Cloud, 2026-10-21", examples=examples[fid])
        gen["wiring"][fid] = wiring
        print(f"OK   {fid:<52} {w['output_kind']:<6} {len(w['inputs'])} inputs")
    gen_path.write_text(json.dumps(gen, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
