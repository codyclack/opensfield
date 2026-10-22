"""Write the two graphs the app-example renders use on a local ComfyUI (both open weights, both checked on a Quadro RTX 6000):

- features/_graphs/qwen_edit_2511_two_image/  Qwen-Image-Edit 2511 with a second reference photo (face swap, try-on, character swap)
- features/_graphs/ltx23_i2v_local/            LTX-2.3 image-to-video, one distilled stage at up to 768 px, 3 s at 24 fps, no audio

Both are API-format graphs; workflow_ui.json is the same graph (ComfyUI opens API-format files too).

    uv run python scripts/make_local_graphs.py
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "features" / "_graphs"


def write(name, graph):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    for f in ("workflow_api.json", "workflow_ui.json"):
        (d / f).write_text(json.dumps(graph, indent=1) + "\n", encoding="utf-8")
    print("wrote", d.relative_to(ROOT))


def qwen_two_image():
    g = copy.deepcopy(json.loads((ROOT / "features" / "image.edit-open" / "workflow_api.json").read_text(encoding="utf-8")))
    g["42"] = {"class_type": "LoadImage", "inputs": {"image": "char_b.png"}, "_meta": {"title": "Second photo"}}
    g["170:171"] = {"class_type": "FluxKontextImageScale", "inputs": {"image": ["42", 0]}}
    for n in ("170:149", "170:151"):  # both the positive and the empty negative see the two references, as in the template
        g[n]["inputs"]["image2"] = ["170:171", 0]
    return g


def ltx23_i2v(frames=73, size=768):
    # Settings follow the official LTX-2.3 template's first stage (distilled LoRA 0.5, its 8 manual sigmas, euler, cfg 1),
    # with the split transformer / Gemma / VAE files and without the 2x spatial upscale stage.
    vid_vae, aud_vae = ["5", 0], ["6", 0]
    return {
        "1": {"class_type": "DiffusionModelLoaderKJ", "inputs": {"model_name": "ltx-2.3-22b-dev_transformer_only_fp8_scaled.safetensors", "weight_dtype": "default",
                                                              "compute_dtype": "fp16", "patch_cublaslinear": False, "sage_attention": "disabled", "enable_fp16_accumulation": False}},
        "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"lora_name": "ltx-2.3-22b-distilled-1.1_lora-dynamic_fro09_avg_rank_111_bf16.safetensors", "strength_model": 0.5, "model": ["1", 0]}},
        "33": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "gemma_3_12B_it_fp8_scaled.safetensors", "clip_name2": "ltx-2.3_text_projection_bf16.safetensors", "type": "ltxv", "device": "default"}},
        "5": {"class_type": "VAELoaderKJ", "inputs": {"vae_name": "LTX23_video_vae_bf16.safetensors", "device": "main_device", "weight_dtype": "fp32"}},
        "6": {"class_type": "VAELoaderKJ", "inputs": {"vae_name": "LTX23_audio_vae_bf16.safetensors", "device": "main_device", "weight_dtype": "fp16"}},
        "8": {"class_type": "CLIPTextEncode", "inputs": {"text": "The person slowly turns toward the camera and smiles.", "clip": ["33", 0]}},
        "9": {"class_type": "CLIPTextEncode", "inputs": {"text": "pc game, console game, video game, cartoon, childish, ugly", "clip": ["33", 0]}},
        "10": {"class_type": "LTXVConditioning", "inputs": {"frame_rate": 24, "positive": ["8", 0], "negative": ["9", 0]}},
        "40": {"class_type": "LoadImage", "inputs": {"image": "char_a.png"}, "_meta": {"title": "Start frame"}},
        "41": {"class_type": "ImageResizeKJv2", "inputs": {"width": size, "height": size, "upscale_method": "lanczos", "keep_proportion": "resize", "pad_color": "0, 0, 0",
                                                         "crop_position": "center", "divisible_by": 32, "device": "cpu", "image": ["40", 0]}},
        "42": {"class_type": "LTXVPreprocess", "inputs": {"img_compression": 18, "image": ["41", 0]}},
        "74": {"class_type": "GetImageSizeAndCount", "inputs": {"image": ["41", 0]}},
        "14": {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": ["74", 1], "height": ["74", 2], "length": frames, "batch_size": 1}},
        "43": {"class_type": "LTXVImgToVideoInplace", "inputs": {"strength": 1.0, "bypass": False, "vae": vid_vae, "image": ["42", 0], "latent": ["14", 0]}},
        "44": {"class_type": "LTXVEmptyLatentAudio", "inputs": {"frames_number": frames, "frame_rate": 24, "batch_size": 1, "audio_vae": aud_vae}},
        "15": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["43", 0], "audio_latent": ["44", 0]}},
        "18": {"class_type": "RandomNoise", "inputs": {"noise_seed": 42}},
        "19": {"class_type": "CFGGuider", "inputs": {"cfg": 1, "model": ["4", 0], "positive": ["10", 0], "negative": ["10", 1]}},
        "20": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "21": {"class_type": "ManualSigmas", "inputs": {"sigmas": "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"}},
        "17": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["18", 0], "guider": ["19", 0], "sampler": ["20", 0], "sigmas": ["21", 0], "latent_image": ["15", 0]}},
        "23": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["17", 0]}},
        # tiled like the official template's decoder: the fp32 VAE (fp16 decodes to black on Turing) is too big to decode 73 frames at once
        "24": {"class_type": "VAEDecodeTiled", "inputs": {"tile_size": 768, "overlap": 64, "temporal_size": 4096, "temporal_overlap": 4, "samples": ["23", 0], "vae": vid_vae}},
        "25": {"class_type": "CreateVideo", "inputs": {"fps": 24, "images": ["24", 0]}},
        "26": {"class_type": "SaveVideo", "inputs": {"filename_prefix": "video/OpenSfield_LTX23", "format": "auto", "format.codec": "auto", "video": ["25", 0]}},
    }


if __name__ == "__main__":
    write("qwen_edit_2511_two_image", qwen_two_image())
    write("ltx23_i2v_local", ltx23_i2v())

