# OpenSfield

Open-source rebuild of Higgsfield's creative apps on ComfyUI, for Comfy's
**#OpenSourceHiggsfield** challenge. Open weights by default; an optional
`partner/` pack adds Comfy Router models.

## Status (honest summary)
- **37 of 72 modules are built and have real example outputs** in [`examples/`](examples/README.md), using open-weight models
  only: 21 are separate ComfyUI workflows (motion transfer, character replacement, text/image-to-video, first/last frame,
  video edit, image edit, inpaint, outpaint, background removal, layer decomposition, upscale, music, image-to-3D, several
  text-to-image models, style reference, two-reference compose), 11 are presets that reuse those workflows (camera angles, viral effects,
  multishot, character sheet, identity, product shots, thumbnails, ads, brand assets, sprites, studio presets) and 5 are local CPU effects (`app/fx.py`: thermal palettes, retro looks, deflicker, burned captions, typewriter and word-stack text).
- **35 modules are not built.** Reasons: partner-only models, platform features that are not generation, nodes that need your
  own custom packs, or no usable open workflow found. COVERAGE.md lists each one. [COVERAGE.md](COVERAGE.md) lists every Higgsfield feature, its planned open-weight
  stand-in and its status (`planned` / `built` / `tested`).
- **The app runs in mock mode out of the box** (placeholder outputs, no ComfyUI needed). Real runs through the app's `comfy-sdk`
  path are implemented and unit-tested against a stub, and **verified end to end for one module**: `image.bg-remove` was run through the app against Comfy Cloud on 2026-10-21 (app -> `comfy-sdk` -> Cloud -> result in the UI). The other modules have not each been run through the app yet; their example renders used Comfy Cloud's template runner.

## Try the app shell (mock mode, no ComfyUI)
```bash
uv run uvicorn app.main:app --port 8765
```
Open http://127.0.0.1:8765. Every manifest becomes a studio card + generated form; Generate
creates a job and returns a placeholder image. Tests: `uv run --extra dev pytest`.
Env: `OPENSFIELD_MODE=mock|comfy`, `OPENSFIELD_PARTNER=1` (show partner-pack modules),
`COMFY_BASE_URL`, `COMFY_API_KEY` (comfy mode only; `uv sync --extra comfy`).

## Layout
- `registry/features.py` — every Higgsfield feature, its tier, and the base graphs it is built from
- `features/<id>/manifest.json` — generated per-feature manifests (inputs/slots/models filled in as each is built)
- `schema/manifest.schema.json` — manifest contract
- `scripts/build_registry.py` — regenerates manifests + `COVERAGE.md`
- `app/` — FastAPI + static web UI (`registry.py` reads manifests, `runner.py` has MockRunner + comfy-sdk ComfyRunner, `main.py` is the API)
- `registry/wiring.py` — which node/field each form input drives, per built module
- `examples/` — real example renders

## Workflows: rendered on Comfy Cloud
Twelve modules have real workflows wired from official Comfy templates, and each has a real render in
[`examples/`](examples/README.md) (open-weight models only; seconds to about a minute of GPU each). They were run through Comfy Cloud's
template runner using the node ids in `registry/wiring.py`; **the app's own `comfy-sdk` submission path has been run live for `image.bg-remove` only**.
Wiring is also checked statically by `tests/test_wiring.py`.

| Module | Template | Model family |
|---|---|---|
| `genjutsu.motion-control` | `video_wan_animate2_distilled` | Wan Animate 2 (int8) |
| `cinema.camera-rig` | `video_ltx2_5_i2v` | LTX-2.5 |
| `cinema.first-last-frame` | `video_ltx2_5_flf2v` | LTX-2.5 |
| `soul.t2i` | `image_z_image_turbo` | Z-Image Turbo |
| `image.edit-open` | `image_qwen_image_edit_2511_int8` | Qwen-Image-Edit 2511 |
| `image.bg-remove` | `utility_birefnet_remove_background` | BiRefNet |
| `image.upscale` / `video.upscale` | `utility_seedvr2_3b_int8_upscale_image` / `_video` | SeedVR2 3B |
| `audio.music` | `audio_ace_step1_5_xl_turbo` | ACE-Step 1.5 XL Turbo |
| `video.t2v-i2v-open` | `video_ltx2_5_t2v` | LTX-2.5 |
| `genjutsu.replace-object` | `video_wan21_scail2_character_replacement_int8` | SCAIL-2 (Wan 2.1) int8 |
| `scene3d.image-to-3d` | `3d_hunyuan3d_image_to_model` | Hunyuan3D 2.0 |

Each `features/<id>/` holds `workflow_ui.json` (open in ComfyUI), `workflow_api.json` (what `comfy-sdk` submits) and the
manifest, whose `workflow.inputs` says which node/field each form input drives. `registry/wiring.py` is the source of that map.
`comfy-sdk` only accepts API format, and the templates use subgraphs, so the API files were converted against a node catalog:
re-export against whichever server will run them (read-only, it only GETs `/object_info`):

```bash
uv run --with comfy-cli scripts/export_api.py --base http://127.0.0.1:8188
uv run scripts/build_registry.py && uv run --extra dev --extra comfy pytest
```
Template example assets (their sample character/driving clip) are not used; supply your own inputs.

## Demo video
`demo/make_demo.py` builds the demo (captions + real renders + app screenshots + the ACE-Step track made by the music module)
with no voice-over. Instructions are at the top of the script. The rendered mp4 is not committed.

## Regenerate coverage
```bash
uv run scripts/build_registry.py
```

## Real runs (verified for image.bg-remove)
```bash
uv sync --extra comfy
export OPENSFIELD_MODE=comfy
export COMFY_API_KEY=...                      # Comfy Cloud, or
export COMFY_BASE_URL=http://127.0.0.1:8189   # a self-hosted ComfyUI behind comfy-api-proxy (no key needed)
uv run uvicorn app.main:app --port 8765
```
The four built modules need their models on the target server (names are in each manifest's `workflow.models`; Comfy Cloud
already has them). You can also open any `features/<id>/workflow_ui.json` directly in ComfyUI.

License: MIT.
