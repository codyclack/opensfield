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
        template="video_wan_animate2_distilled",
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
        template="video_ltx2_5_i2v",
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
        template="video_ltx2_5_flf2v",
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
