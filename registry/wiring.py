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
