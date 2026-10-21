"""Maps form inputs to nodes in each feature's workflow_api.json.

Node ids come from scripts/export_api.py run against a ComfyUI node catalog; every id and field
here is checked against the file by tests/test_wiring.py. Workflows start as official Comfy
templates (see `template`). Nothing here has been run end to end: manifests stay status "built"
until a real render promotes them to "tested".
"""

ASPECTS = ["1:1 (Square)", "2:3 (Portrait Photo)", "3:2 (Photo)", "3:4 (Portrait Standard)", "4:3 (Standard)",
           "9:16 (Portrait Widescreen)", "16:9 (Widescreen)", "21:9 (Ultrawide)"]


def inp(name, label, kind, node, field, **kw):
    return dict(name=name, label=label, kind=kind, node=node, field=field, **kw)


SEED = dict(label="Seed (0 = random)", kind="seed", default=0)

# What "verified" means here: the template was rendered on Comfy Cloud (2026-10-21) with overrides addressed by exactly the
# node ids/fields in these maps. The app's own comfy-sdk submission path has not been exercised yet.
VIA = "Comfy Cloud run_template using the node ids in this map, 2026-10-21 (not yet via comfy-sdk)"

WIRING = {
    # Wan Animate 2 (distilled, int8): motion transfer from a driving video onto a still character.
    "genjutsu.motion-control": dict(
        template="video_wan_animate2_distilled", output_kind="video",
        verified_via=VIA, examples=["examples/motion_transfer.mp4", "examples/motion_transfer_compare.mp4"],
        inputs=[
            inp("character", "Character image", "image", "189", "image", required=True),
            inp("driving_video", "Driving video", "video", "240", "file", required=True),
            inp("character_prompt", "Character description", "text", "605", "value", required=True),
            inp("motion_prompt", "Motion description", "text", "604", "value", required=True),
            inp("seed", SEED["label"], "seed", "261:19", "noise_seed", default=0),
        ],
        outputs=["246", "292"],  # 246 = generated video, 292 = driving | result side by side
        models=["wan_animate_2_distill_int8_convrot.safetensors",
                "lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors",
                "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "clip_vision_h.safetensors", "Wan2_1_VAE_bf16.safetensors"],
    ),
    # LTX-2.5 image-to-video: Cinema Studio style single shot; camera language goes in the prompt.
    "cinema.camera-rig": dict(
        template="video_ltx2_5_i2v", output_kind="video",
        verified_via=VIA, examples=["examples/cinema_camera_rig_dance.mp4", "examples/driving_dance.mp4"],
        inputs=[
            inp("start_image", "Start frame", "image", "395", "image", required=True),
            inp("prompt", "Shot prompt (subject, camera move, lens, light)", "text", "398:376", "value", required=True),
            inp("aspect", "Aspect", "choice", "403", "aspect_ratio", options=ASPECTS, default="16:9 (Widescreen)"),
            inp("duration", "Duration (s)", "number", "398:362", "value", default=5, min=1, max=10, step=1),
            inp("seed", SEED["label"], "seed", "398:338", "noise_seed", default=0, also=[dict(node="398:339", field="noise_seed")]),
        ],
        outputs=["75"],
        models=["ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors", "gemma4_e2b_it_int8_convrot.safetensors",
                "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors", "ltx-2.5-video-vae-bf16.safetensors",
                "ltx-2.5-audio-vae-bf16.safetensors", "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors",
                "ltx-av-step-1751000_vocoder_24K.safetensors"],
    ),
    # LTX-2.5 first/last frame: the transition engine behind Viral Hub style effects.
    "cinema.first-last-frame": dict(
        template="video_ltx2_5_flf2v", output_kind="video",
        verified_via=VIA, examples=["examples/first_last_frame_morph.mp4"],
        inputs=[
            inp("start_image", "First frame", "image", "31", "image", required=True),
            inp("end_image", "Last frame", "image", "39", "image", required=True),
            inp("prompt", "Transition prompt", "text", "251:252", "value", required=True),
            inp("width", "Width", "number", "251:215", "value", default=1280, min=256, max=1920, step=32),
            inp("height", "Height", "number", "251:216", "value", default=720, min=256, max=1920, step=32),
            inp("duration", "Duration (s)", "number", "251:198", "value", default=5, min=1, max=10, step=1),
            inp("seed", SEED["label"], "seed", "251:196", "noise_seed", default=0),
        ],
        outputs=["68"],
        models=["ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors", "gemma4_e2b_it_int8_convrot.safetensors",
                "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors", "ltx-2.5-video-vae-bf16.safetensors",
                "ltx-2.5-audio-vae-bf16.safetensors"],
    ),
    # Z-Image Turbo text-to-image stands in for Soul 2.0.
    "soul.t2i": dict(
        template="image_z_image_turbo",
        verified_via=VIA, examples=["examples/char_a.png", "examples/char_b.png"],
        inputs=[
            inp("prompt", "Prompt", "text", "57:27", "text", required=True),
            inp("width", "Width", "number", "57:13", "width", default=1024, min=512, max=2048, step=64),
            inp("height", "Height", "number", "57:13", "height", default=1024, min=512, max=2048, step=64),
            inp("seed", SEED["label"], "seed", "57:3", "seed", default=0),
        ],
        outputs=["9"],
        models=["z_image_turbo_bf16.safetensors", "qwen_3_4b.safetensors", "ae.safetensors"],
    ),
}


def preset(name, label, presets, apply_to="prompt"):
    """A choice with no node of its own: the chosen text is prepended to the `apply_to` text input (see runner.resolve_values)."""
    return dict(name=name, label=label, kind="choice", options=list(presets), default=next(iter(presets)), presets=presets, apply_to=apply_to)


def _seed(node, field="seed", **kw):
    return inp("seed", SEED["label"], "seed", node, field, default=0, **kw)


# Second batch. `models` is filled from each workflow_ui.json by scripts/build_registry.py.
WIRING.update({
    # Qwen-Image-Edit 2511 (int8): instruction-based image edit, stands in for Nano Banana style edits.
    "image.edit-open": dict(
        template="image_qwen_image_edit_2511_int8", output_kind="image",
        verified_via=VIA, examples=["examples/image_edit_yellow_hoodie.png"],
        inputs=[inp("image", "Image", "image", "41", "image", required=True),
                inp("prompt", "Edit instruction", "text", "170:151", "prompt", required=True), _seed("170:169")],
        outputs=["195"]),
    # BiRefNet background removal: cutout with alpha plus the mask.
    "image.bg-remove": dict(
        template="utility_birefnet_remove_background", output_kind="image",
        verified_via=VIA, examples=["examples/bg_remove_cutout.png", "examples/bg_remove_mask.png"],
        inputs=[inp("image", "Image", "image", "17", "image", required=True)], outputs=["18", "20"]),
    # SeedVR2 3B (int8) one-step upscaler.
    "image.upscale": dict(
        template="utility_seedvr2_3b_int8_upscale_image", output_kind="image",
        verified_via=VIA, examples=["examples/upscale_2x.png"],
        inputs=[inp("image", "Image", "image", "1", "image", required=True),
                inp("scale", "Scale (x)", "number", "66:57", "resize_type.multiplier", default=4, min=1, max=4, step=1), _seed("66:54")],
        outputs=["9"]),
    "video.upscale": dict(
        template="utility_seedvr2_3b_int8_upscale_video", output_kind="video",
        verified_via=VIA, examples=["examples/video_upscale.mp4"],
        inputs=[inp("video", "Video", "video", "73", "file", required=True), _seed("66:54")], outputs=["76"]),
    # ACE-Step 1.5 XL Turbo text-to-music.
    "audio.music": dict(
        template="audio_ace_step1_5_xl_turbo", output_kind="audio",
        verified_via=VIA, examples=["examples/music_lofi.mp3"],
        inputs=[inp("tags", "Style tags", "text", "94", "tags", required=True),
                inp("lyrics", "Lyrics ([Instrumental] for none)", "text", "94", "lyrics", required=True),
                inp("bpm", "BPM", "number", "94", "bpm", default=95, min=40, max=220, step=1),
                inp("duration", "Duration (s)", "number", "94", "duration", default=30, min=5, max=240, step=1,
                    also=[dict(node="98", field="seconds")]),
                _seed("109", "value")],
        outputs=["111"]),
    # LTX-2.5 text-to-video: stands in for the open side of the video-model roster.
    "video.t2v-i2v-open": dict(
        template="video_ltx2_5_t2v", output_kind="video",
        verified_via=VIA, examples=["examples/text_to_video_alley.mp4"],
        inputs=[inp("prompt", "Prompt", "text", "405:376", "value", required=True),
                inp("aspect", "Aspect", "choice", "409", "aspect_ratio", options=ASPECTS, default="16:9 (Widescreen)"),
                inp("duration", "Duration (s)", "number", "405:362", "value", default=5, min=1, max=10, step=1),
                _seed("405:338", "noise_seed", also=[dict(node="405:339", field="noise_seed")])],
        outputs=["75"]),
    # SCAIL-2 (Wan 2.1, int8) character replacement; the template has two parallel branches, both are wired.
    "genjutsu.replace-object": dict(
        template="video_wan21_scail2_character_replacement_int8", output_kind="video",
        verified_via=VIA, examples=["examples/replace_character_a.mp4", "examples/replace_character_b.mp4"],
        inputs=[inp("video", "Source video", "video", "155", "file", required=True),
                inp("image", "Replacement character image", "image", "30", "image", required=True),
                inp("prompt", "Character description", "text", "213:3", "text", required=True, also=[dict(node="262:258", field="text")]),
                inp("target", "Who to replace in the video", "text", "213:191", "text", required=True, also=[dict(node="262:242", field="text")]),
                _seed("213:19", "noise_seed", also=[dict(node="262:227", field="noise_seed")])],
        outputs=["202", "271"]),
    # Hunyuan3D 2.0 image to untextured mesh (.glb).
    "scene3d.image-to-3d": dict(
        template="3d_hunyuan3d_image_to_model", output_kind="3d",
        verified_via=VIA, examples=["examples/image_to_3d.glb"],
        inputs=[inp("image", "Image", "image", "56", "image", required=True), _seed("91:3")], outputs=["82"]),
})


# Third batch. New templates (own workflow files) first, then preset modules that reuse another module's files via files_from.
WIRING.update({
    "image.t2i-open": dict(
        template="image_flux3_klein_t2i", output_kind="image",
        inputs=[inp("prompt", "Prompt", "text", "18:17", "value", required=True),
                inp("aspect", "Aspect", "choice", "19", "aspect_ratio", options=ASPECTS, default="1:1 (Square)"), _seed("18:7")],
        outputs=["9"]),
    "soul.cinematic": dict(
        template="image_krea2_turbo_t2i", output_kind="image",
        inputs=[inp("prompt", "Scene", "text", "30:19", "value", required=True,
                    prefix="Cinematic film still, anamorphic lens, shallow depth of field, natural film grain. "),
                inp("aspect", "Aspect", "choice", "49", "aspect_ratio", options=ASPECTS, default="16:9 (Widescreen)"), _seed("30:3")],
        outputs=["29"]),
    "soul.cast": dict(
        template="image_qwen_image_2_1_image_edit", output_kind="image",
        inputs=[inp("image", "Character image", "image", "470", "image", required=True),
                inp("image_b", "Second reference image", "image", "475", "image", required=True),
                inp("prompt", "Instruction (use 'first image' / 'second image')", "text", "459:500", "prompt", required=True),
                _seed("459:458")],
        outputs=["461"]),
    "soul.styles": dict(
        template="image_krea2_turbo_int8_image_style_reference", output_kind="image",
        inputs=[inp("style", "Style reference image", "image", "69", "image", required=True),
                inp("prompt", "Subject", "text", "30:19", "value", required=True),
                inp("aspect", "Aspect", "choice", "71", "aspect_ratio", options=ASPECTS, default="1:1 (Square)"), _seed("30:63", "noise_seed")],
        outputs=["29"]),
    "image.inpaint-brush": dict(
        template="flux_fill_inpaint_example", output_kind="image",
        inputs=[inp("image", "Image (transparent area = repaint here)", "image", "17", "image", required=True),
                inp("prompt", "What to paint there", "text", "47:23", "text", required=True), _seed("47:3")],
        outputs=["9"]),
    "image.outpaint": dict(
        template="flux_fill_outpaint_example", output_kind="image",
        inputs=[inp("image", "Image", "image", "17", "image", required=True),
                inp("prompt", "What the new area should contain", "text", "23", "text", required=True),
                inp("left", "Extend left (px)", "number", "44", "left", default=256, min=0, max=1024, step=64),
                inp("right", "Extend right (px)", "number", "44", "right", default=256, min=0, max=1024, step=64),
                inp("top", "Extend top (px)", "number", "44", "top", default=0, min=0, max=1024, step=64),
                inp("bottom", "Extend bottom (px)", "number", "44", "bottom", default=0, min=0, max=1024, step=64), _seed("3")],
        outputs=["9"]),
    "image.decompose": dict(
        template="image_qwen_image_layered", output_kind="image",
        inputs=[inp("image", "Image", "image", "74", "image", required=True),
                inp("prompt", "Describe the image", "text", "116", "value", required=True),
                inp("layers", "Layers", "number", "83:118", "layers", default=3, min=2, max=8, step=1), _seed("83:3")],
        outputs=["60"]),
    "video.edit": dict(
        template="video_bernini_r_video_editing", output_kind="video",
        inputs=[inp("video", "Video", "video", "47", "file", required=True),
                inp("image", "Reference image (new background / look)", "image", "104", "image", required=True),
                inp("prompt", "Edit instruction", "text", "298:297", "value", required=True), _seed("298:275", "noise_seed")],
        outputs=["46"]),
})

CAM = WIRING["cinema.camera-rig"]["inputs"]  # start_image, prompt, aspect, duration, seed


def _with(inputs, **changes):
    """Copy a module's inputs, applying per-input overrides: _with(CAM, prompt=dict(required=False, prefix="..."))."""
    out = []
    for s in inputs:
        s = dict(s)
        s.update(changes.get(s["name"], {}))
        out.append(s)
    return out


def _reuse(src, template_of, inputs, outputs=None, **kw):
    return dict(template=WIRING[template_of]["template"], files_from=src, output_kind=WIRING[template_of].get("output_kind", "image"),
                inputs=inputs, outputs=outputs or WIRING[template_of]["outputs"], **kw)


EFFECTS = {
    "Clones": "Identical clones of the person appear around the scene one after another, each mirroring the person's movements, while the original steps toward the camera. Locked-off camera.",
    "Vanish": "The person's body suddenly disappears, leaving their empty clothes to collapse and fall flat onto the ground. Locked-off camera.",
    "Floating fall": "The person falls backward in slow motion while their belongings float in midair around them, the camera drifting through crisp close-ups.",
    "Act natural": "Time freezes for the person and the objects near them mid-action while everything else in the world keeps moving normally.",
    "Giant": "The person grows into a towering giant standing in a city street, buildings small beside them, the camera tilting up their body.",
    "Eyes in": "The camera pushes in on the person's face and dives into their eye, passing through the dark pupil.",
}
WIRING.update({
    # soul.location is deliberately NOT wired: the two-image Qwen 2.1 template returned corrupted images for a portrait + a
    # landscape location photo in three attempts (it worked for two portraits). Revisit with an inpaint-based approach.
    # single-image tasks use the single-image edit workflow (Qwen-Image-Edit 2511), which follows these instructions better
    "soul.id": _reuse("image.edit-open", "image.edit-open", [
        dict(WIRING["image.edit-open"]["inputs"][0], label="Person (identity to keep)"),
        dict(WIRING["image.edit-open"]["inputs"][1], label="New scene", prefix="Keep this person's face, hair, build and clothes exactly the same, and change the scene around them so that they are "),
        WIRING["image.edit-open"]["inputs"][2]]),
    "soul.character-sheet": _reuse("image.edit-open", "image.edit-open", [
        dict(WIRING["image.edit-open"]["inputs"][0], label="Character image"),
        dict(WIRING["image.edit-open"]["inputs"][1], required=False, label="Extra detail (optional)",
             prefix="Turn this into a character reference sheet: the same person shown three times side by side as a front view, a side view and a back view, same outfit, plain light background. "),
        WIRING["image.edit-open"]["inputs"][2]]),
    "viral.effects": _reuse("cinema.camera-rig", "cinema.camera-rig", [
        CAM[0], preset("effect", "Effect", EFFECTS),
        dict(CAM[1], required=False, label="Subject detail (optional)", prefix="Use the provided start image as the first frame. "), *CAM[2:]]),
    "cinema.multishot": _reuse("cinema.camera-rig", "cinema.camera-rig", _with(CAM,
        prompt=dict(label="Shots: 'Shot 1: ... Shot 2: ...'", prefix="Use the provided start image as the first frame. A multi-shot sequence with hard cuts between shots, consistent character and lighting. "),
        duration=dict(default=8))),
    "marketing.studio-presets": _reuse("cinema.camera-rig", "cinema.camera-rig", [
        dict(CAM[0], label="Product image"),
        preset("motion", "Product motion", {
            "Orbit": "A smooth 180 degree orbit around the product at eye level on a clean studio surface, soft reflections.",
            "Slow push-in": "A slow macro push-in on the product, shallow depth of field, soft light sweeping across its surface.",
            "Rise and reveal": "The product rises into frame from below on a seamless backdrop as a light sweep reveals its details."}),
        dict(CAM[1], required=False, label="Extra detail (optional)", prefix="Use the provided start image as the first frame. "), *CAM[2:]]),
    "marketing.product-photoshoot": _reuse("image.edit-open", "image.edit-open", [
        dict(WIRING["image.edit-open"]["inputs"][0], label="Product photo"),
        preset("scene", "Shot style", {
            "Studio packshot": "Place this product on a seamless pure white studio background with a soft natural shadow, e-commerce packshot, evenly lit.",
            "Lifestyle table": "Place this product on a sunlit wooden table in a bright minimal room, shallow depth of field, lifestyle photo.",
            "City street": "Place this product on a wet city sidewalk at dusk with neon reflections, shallow depth of field."}),
        dict(WIRING["image.edit-open"]["inputs"][1], required=False, label="Extra detail (optional)"), WIRING["image.edit-open"]["inputs"][2]]),
    "marketing.thumbnails": _reuse("soul.cinematic", "soul.cinematic", [
        preset("framework", "Thumbnail framework", {
            "Face close-up": "YouTube thumbnail: extreme close-up of an expressive face with wide eyes, high contrast, saturated colors, clear empty space on the left for text.",
            "Hero object": "YouTube thumbnail: one bold hero object in sharp focus on a vivid gradient background, strong rim light, empty space at the top for text.",
            "Mystery silhouette": "YouTube thumbnail: dramatic silhouette against a glowing backdrop, moody colors, strong contrast, empty space on the right for text."}),
        dict(WIRING["soul.cinematic"]["inputs"][0], label="Topic / subject", prefix=""), *WIRING["soul.cinematic"]["inputs"][1:]]),
    "marketing.ads-studio": _reuse("image.t2i-open", "image.t2i-open", [
        preset("format", "Ad format", {
            "Social product ad": "A polished social media product ad photo, product centered, clean colorful background, generous empty space for a headline.",
            "Poster": "A bold advertising poster layout with a strong focal image and large empty areas reserved for headline and body copy."}),
        dict(WIRING["image.t2i-open"]["inputs"][0], label="Product / brand and idea"), *WIRING["image.t2i-open"]["inputs"][1:]]),
    "marketing.brand-assets": _reuse("image.t2i-open", "image.t2i-open", [
        preset("asset", "Asset type", {
            "Logo mark": "A clean minimal vector-style logo mark on a plain white background, flat colors, centered, no text.",
            "Merch mockup": "A product mockup of a plain t-shirt on a hanger against a neutral wall with the brand mark printed on the chest, studio lighting.",
            "Packaging mockup": "A product packaging mockup: a box and a pouch on a light surface, brand colors, soft studio shadows."}),
        dict(WIRING["image.t2i-open"]["inputs"][0], label="Brand name and style"), *WIRING["image.t2i-open"]["inputs"][1:]]),
    "scene3d.autosprite": _reuse("soul.t2i", "soul.t2i", [
        dict(WIRING["soul.t2i"]["inputs"][0], label="Character", prefix="Game sprite sheet, a 4 by 4 grid of the same character in a walk cycle, flat solid green background, consistent proportions: "),
        *WIRING["soul.t2i"]["inputs"][1:]]),
})


# Local CPU effects (app/fx.py): no workflow files, no ComfyUI. "verified_via" is added once they have rendered.
LOCAL_VIA = "Rendered locally by app/fx.py on CPU, 2026-10-21 (no ComfyUI involved)"
WIRING.update({
    "matchcut.thermal": dict(
        local=dict(mode_input="palette"), template="app/fx.py", output_kind="video", outputs=[],
        inputs=[dict(name="video", label="Video", kind="video", required=True),
                dict(name="palette", label="Palette", kind="choice", options=["black-hot", "white-hot", "rainbow", "iron"], default="black-hot")],
        verified_via=LOCAL_VIA, examples=["examples/fx_thermal_blackhot.mp4", "examples/fx_thermal_rainbow.mp4"]),
    "matchcut.retro-fx": dict(
        local=dict(mode_input="mode"), template="app/fx.py", output_kind="video", outputs=[],
        inputs=[dict(name="video", label="Video", kind="video", required=True),
                dict(name="mode", label="Look", kind="choice", default="crt",
                     options=["crt", "crt-glitch", "vhs", "glitch", "nokia", "retropop", "night-vision"])],
        verified_via=LOCAL_VIA, examples=["examples/fx_crt.mp4", "examples/fx_vhs.mp4", "examples/fx_nokia.mp4"]),
})


# Real renders on Comfy Cloud, 2026-10-21 (see examples/README.md). Preset modules were rendered with the app's own prompt assembly.
_RENDERED = {
    "image.t2i-open": ["examples/t2i_flux3_sneakers.png"],
    "soul.cinematic": ["examples/cinematic_krea.png"],
    "soul.cast": ["examples/soul_cast.png"],
    "soul.styles": ["examples/style_reference_out.png"],
    "image.inpaint-brush": ["examples/inpaint_out.png"],
    "image.outpaint": ["examples/outpaint_out.png"],
    "image.decompose": ["examples/layers_0.png", "examples/layers_1.png", "examples/layers_2.png"],
    "video.edit": ["examples/video_edit_street.mp4"],
    "soul.id": ["examples/soul_id.png"],
    "soul.character-sheet": ["examples/character_sheet.png"],
    "viral.effects": ["examples/effect_clones.mp4", "examples/effect_vanish.mp4"],
    "cinema.multishot": ["examples/multishot.mp4"],
    "marketing.studio-presets": ["examples/product_orbit.mp4"],
    "marketing.product-photoshoot": ["examples/product_photoshoot.png"],
    "marketing.thumbnails": ["examples/thumbnail_hero.png"],
    "marketing.ads-studio": ["examples/ad_social.png"],
    "marketing.brand-assets": ["examples/brand_logo.png"],
    "scene3d.autosprite": ["examples/sprite_sheet.png"],
}
for _fid, _ex in _RENDERED.items():
    WIRING[_fid].update(verified_via=VIA, examples=_ex)


WIRING["scene3d.angles"] = _reuse("image.edit-open", "image.edit-open", [
    dict(WIRING["image.edit-open"]["inputs"][0], label="Subject image"),
    preset("angle", "Camera angle", {
        "Side view": "Show the exact same subject from a camera rotated 90 degrees to the left so we see their left side, same outfit, same lighting, plain background.",
        "Back view": "Show the exact same subject from directly behind, same outfit, same lighting, plain background.",
        "Low angle": "Show the exact same subject from a low camera angle looking up at them, dramatic perspective, same outfit and lighting.",
        "Top-down": "Show the exact same subject from a high camera angle looking down at them, same outfit and lighting."}),
    dict(WIRING["image.edit-open"]["inputs"][1], required=False, label="Extra detail (optional)"),
    WIRING["image.edit-open"]["inputs"][2]])

WIRING["scene3d.angles"].update(verified_via=VIA, examples=["examples/angle_low.png"])  # rendered with the "Low angle" preset


WIRING.update({
    "video.deflicker": dict(
        local=dict(mode="deflicker"), template="app/fx.py", output_kind="video", outputs=[],
        inputs=[dict(name="video", label="Flickering video", kind="video", required=True)],
        verified_via=LOCAL_VIA, examples=["examples/flicker_input.mp4", "examples/fx_deflicker.mp4"]),
    "audio.captions": dict(
        local=dict(mode="captions", text_input="text"), template="app/fx.py", output_kind="video", outputs=[],
        inputs=[dict(name="video", label="Video", kind="video", required=True),
                dict(name="text", label="Caption lines (one per line, spread evenly; no speech recognition)", kind="text", required=True)],
        verified_via=LOCAL_VIA, examples=["examples/fx_captions.mp4"]),
    "matchcut.text-motion": dict(
        local=dict(mode_input="mode", text_input="text"), template="app/fx.py", output_kind="video", outputs=[],
        inputs=[dict(name="video", label="Video", kind="video", required=True),
                dict(name="mode", label="Animation", kind="choice", options=["typewriter", "wordstack"], default="typewriter"),
                dict(name="text", label="Text", kind="text", required=True)],
        verified_via=LOCAL_VIA, examples=["examples/fx_typewriter.mp4", "examples/fx_wordstack.mp4"]),
})


# LTX-2.3 IC-LoRA union control: the control video supplies structure/motion, the image supplies the new look of the first frame.
WIRING["genjutsu.styles"] = dict(
    template="video_ltx2_3_ic_lora", output_kind="video",
    inputs=[inp("video", "Control video (motion + structure)", "video", "199", "file", required=True),
            inp("image", "Restyled first frame (the look you want)", "image", "200", "image", required=True),
            inp("prompt", "Describe the restyled scene", "text", "129:209", "prompt", required=True)],
    outputs=["68"], verified_via=VIA, examples=["examples/style_yarn.mp4", "examples/style_yarn_frame.png"])
# Tried and not shipped: video.lipsync (LTX-2.3 image+audio): kept the face for one frame then invented a different scene.


# LTX-2.3 outpainting IC-LoRA: extends a video to a new aspect ratio (the Higgsfield Reframe / Outpaint video tool).
# Node ids come from scripts/export_api.py run against Comfy Cloud's catalog. 5151:5097/5098 are the target aspect (width, height).
WIRING["video.reframe"] = dict(
    template="video_ltx2_3_lora_video_outpainting", output_kind="video",
    inputs=[inp("video", "Video to reframe", "video", "5060", "video", required=True),
            inp("aspect_w", "Target aspect: width part", "number", "5151:5097", "value", default=9, min=1, max=32, step=1),
            inp("aspect_h", "Target aspect: height part", "number", "5151:5098", "value", default=16, min=1, max=32, step=1),
            inp("prompt", "What to fill in at the edges (optional)", "text", "5151:5138", "text"),
            inp("seed", SEED["label"], "seed", "5151:5117", "noise_seed", default=0)],
    outputs=["5152"])

# Chatterbox TTS: speaks the text in the voice of a short audio sample (this is also the voice-clone path).
WIRING["audio.tts"] = dict(
    template="audio-chatterbox_tts", output_kind="audio",
    inputs=[inp("text", "What to say", "text", "4", "text", required=True),
            inp("voice", "Voice sample (a few seconds of speech)", "audio", "6", "audio", required=True),
            inp("exaggeration", "Expressiveness", "number", "4", "exaggeration", default=0.5, min=0.25, max=2.0, step=0.05),
            _seed("4")],
    outputs=["8"])
WIRING["audio.voice-clone"] = _reuse("audio.tts", "audio.tts", [
    dict(WIRING["audio.tts"]["inputs"][1], label="Voice to clone (5-15 s of clean speech)"),
    dict(WIRING["audio.tts"]["inputs"][0], label="Line to speak in that voice"), *WIRING["audio.tts"]["inputs"][2:]])

# Rendered through the app's own path (runner.run_comfy -> comfy-sdk -> Comfy Cloud), 2026-10-21.
APP_VIA = "App path: runner.run_comfy -> comfy-sdk -> Comfy Cloud, 2026-10-21"
for _fid, _ex in {"video.reframe": ["examples/video_reframe_916.mp4", "examples/driving_dance.mp4"],
                  "audio.tts": ["examples/tts_chatterbox.flac"], "audio.voice-clone": ["examples/voice_clone.flac"]}.items():
    WIRING[_fid].update(verified_via=APP_VIA, examples=_ex)


# Third wave: preset modules over workflows already proven above (same node maps, new prompt assembly).
_OUT = WIRING["image.outpaint"]["inputs"]
_EDIT = WIRING["image.edit-open"]["inputs"]
_T2V = WIRING["video.t2v-i2v-open"]["inputs"]
WIRING.update({
    "image.reframe": _reuse("image.outpaint", "image.outpaint", [
        _OUT[0], dict(_OUT[1], required=False, label="What should fill the new area (optional)", prefix="Seamlessly continue the existing scene into the new area, same lighting and style. "), *_OUT[2:]]),
    "audio.narration": _reuse("audio.tts", "audio.tts", [
        dict(WIRING["audio.tts"]["inputs"][0], label="Narration script"), *WIRING["audio.tts"]["inputs"][1:]]),
    "reshoot.novel-view": _reuse("image.edit-open", "image.edit-open", [
        dict(_EDIT[0], label="Frame to re-shoot"),
        preset("angle", "New camera position", {
            "Over the shoulder": "Re-shoot this exact scene from an over-the-shoulder camera position behind the main subject, same people, same place, same lighting.",
            "High wide": "Re-shoot this exact scene from a high wide camera position looking down, same people, same place, same lighting.",
            "Close-up": "Re-shoot this exact scene as a tight close-up on the main subject's face, same person, same place, same lighting.",
            "Low hero": "Re-shoot this exact scene from a low hero camera angle looking up at the main subject, same people, same place, same lighting."}),
        dict(_EDIT[1], required=False, label="Extra detail (optional)"), _EDIT[2]]),
    "marketing.ai-influencer": _reuse("image.edit-open", "image.edit-open", [
        dict(_EDIT[0], label="Your influencer (face reference)"),
        preset("scene", "Content scene", {
            "Coffee shop selfie": "Keep this person's face, hair, build and clothes exactly the same, and change the scene around them so that they are in a bright coffee shop holding a latte, casual phone-camera look.",
            "Gym mirror": "Keep this person's face, hair, build and clothes exactly the same, and change the scene around them so that they are in a gym with mirrors and soft overhead light.",
            "Travel golden hour": "Keep this person's face, hair, build and clothes exactly the same, and change the scene around them so that they are on a rooftop at golden hour with a city skyline behind them.",
            "Get ready with me": "Keep this person's face, hair, build and clothes exactly the same, and change the scene around them so that they are sitting at a vanity mirror with warm bulbs."}),
        dict(_EDIT[1], required=False, label="Extra detail (optional)"), _EDIT[2]]),
    "marketing.ad-multiplier": _reuse("image.edit-open", "image.edit-open", [
        dict(_EDIT[0], label="Winning ad image"),
        preset("variant", "Variant", {
            "New background": "Keep the product and any text exactly the same and replace only the background with a fresh, different setting that suits the product.",
            "Seasonal": "Keep the product exactly the same and restyle the scene for a festive holiday campaign with seasonal props and warm lights.",
            "Different color": "Keep the layout and product shape the same and change the main brand color scheme to a bold contrasting palette.",
            "Dark mode": "Keep the product and layout exactly the same and restyle the scene as a dark, moody premium version with rim lighting."}),
        dict(_EDIT[1], required=False, label="Extra detail (optional)"), _EDIT[2]]),
    "marketing.ugc-video": _reuse("cinema.camera-rig", "cinema.camera-rig", [
        dict(CAM[0], label="Product or person image"),
        preset("format", "UGC format", {
            "Product review": "Handheld phone-camera video of a person holding the product up to the camera and reacting with a genuine smile, casual home setting, slight camera shake.",
            "Unboxing": "Handheld phone-camera video of hands opening a package and revealing the product on a table, excited energy, natural window light.",
            "Try-on": "Handheld mirror-selfie style video of a person trying on the item and turning to show it from different sides, natural light.",
            "Tutorial": "Locked-off phone video of hands demonstrating how to use the product step by step on a clean table, soft daylight."}),
        dict(CAM[1], required=False, label="Extra detail (optional)", prefix="Use the provided start image as the first frame. "), *CAM[2:]]),
    "marketing.click-to-ad": _reuse("cinema.camera-rig", "cinema.camera-rig", [
        dict(CAM[0], label="Product image (from your listing)"),
        preset("style", "Ad style", {
            "Punchy 6s spot": "A fast, punchy product ad: dynamic push-in, quick light sweeps, product hero shot on a bold colored backdrop, premium commercial look.",
            "Lifestyle spot": "A warm lifestyle product ad: the product in use in a sunlit home, gentle camera drift, soft focus pulls, commercial look.",
            "Luxury reveal": "A slow luxury product reveal on a dark reflective surface with a sweeping rim light and shallow depth of field."}),
        dict(CAM[1], required=False, label="Extra detail (optional)", prefix="Use the provided start image as the first frame. "), *CAM[2:]]),
    "marketing.shorts-studio": _reuse("video.t2v-i2v-open", "video.t2v-i2v-open", [
        preset("style", "Short style", {
            "Cinematic story beat": "Vertical short film moment, cinematic lighting, expressive character acting, shallow depth of field.",
            "Explainer visual": "Vertical explainer visual, clean bright scene, one clear subject, smooth camera move, social video look.",
            "Hype montage": "Vertical hype montage shot, rapid camera movement, bold colors, energetic lighting."}),
        dict(_T2V[0], label="Scene idea"), dict(_T2V[1], default="9:16 (Portrait Widescreen)"), *_T2V[2:]]),
})

for _fid, _ex in {"image.reframe": ["examples/image_reframe.png"], "reshoot.novel-view": ["examples/reshoot_over_shoulder.png"],
                  "marketing.ai-influencer": ["examples/influencer_cafe.png"], "marketing.ad-multiplier": ["examples/ad_variant_new_bg.png"],
                  "audio.narration": ["examples/narration.flac"], "marketing.ugc-video": ["examples/ugc_review.mp4"],
                  "marketing.click-to-ad": ["examples/click_to_ad.mp4"], "marketing.shorts-studio": ["examples/shorts_vertical.mp4"]}.items():
    WIRING[_fid].update(verified_via=APP_VIA, examples=_ex)


# Partner-model tools generated by scripts/gen_models.py (node ids come from each template's API-format graph).
import json as _json  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_GEN = _Path(__file__).with_name("models_gen.json")
if _GEN.exists():
    WIRING.update(_json.loads(_GEN.read_text(encoding="utf-8"))["wiring"])
