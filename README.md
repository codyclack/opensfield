# OpenSfield

**Demo video (117 s):** [watch](https://codyclack.github.io/opensfield/demo/) · [download](https://github.com/codyclack/opensfield/releases/download/v1.0/OpenSfield_demo.mp4)

Open-source rebuild of Higgsfield's creative apps on ComfyUI, for Comfy's
**#OpenSourceHiggsfield** challenge. Two kinds of tools: open-weight workflows (LTX, Wan, Qwen, FLUX, ...) and one tool per Higgsfield partner model
(Seedance, Kling, GPT Image, Nano Banana, Grok, ...) generated from Comfy's official API-node templates. Partner tools use Comfy credits.

## What it looks like
A Higgsfield-style app: text top nav (Explore, Image, Video, Audio, Edit, Genjutsu, Cinema Studio, Soul, Viral, Marketing, Apps, Assets),
hover menus listing every studio, tool and model (like higgsfield.ai), a Higgsfield-style Explore page, **Image / Video / Audio workspaces** with Higgsfield's tabs (Create Video, Text to Video, References,
First & Last, Motion Control, Edit Video), a **model picker** per task (Seedance 2.5 is the default for video; open-weight models sit in the
same list), option chips (duration, ratio, resolution), a bottom prompt bar on the Image page, **@ Elements** from your asset library, a
persistent **Generations** history (download, favorite, save as element, reuse settings, remove), and an optional ComfyUI node-graph view of every tool.
**Cinema Studio** is its own workspace like Higgsfield Cinema Studio 4.0: Home, My elements, My favorites, Community and Projects in a sidebar, and a composer with References, Film setup (genre, era, tempo), Camera (body, lens, aperture, 33 moves), Color palette and Lighting pickers that write director's language into the prompt. **My elements** holds characters, locations and props with several reference images each, used by typing @ in any prompt. The **Creator Hub** (`blog/`) has how-to tutorials, a changelog and a Community showcase of every real render.
Preset video tools (viral effects, UGC, click-to-ad, product motion, multishot, shorts, AI influencer) default to Seedance 2.5 with the
open LTX-2.5 version one click away.

**Apps:** all 83 one-click apps from higgsfield.ai/apps (Skibidi left out: someone else's IP) in the same 8 categories: Professional, Enhance & Style, Face & Identity, Video Editing, Ads & Products, Games & Characters, Extras and Trending Templates. Photo apps run on Nano Banana 2.1 with a Qwen-Image-Edit open version, video apps on Seedance 2.5 with an LTX-2.5 open version, and the rest open existing tools (Angles, Expand, Transitions, Recast, Breakdown, Click to Ad...). The list and prompts live in `registry/apps.py`.

## Status (honest summary)
- **Catalog: 146 tools** (Higgsfield modules plus one tool per partner model). **83 have real example outputs** (live runs on Comfy Cloud, or local CPU tools run on this machine), **63 are wired from official Comfy templates but not yet run** (marked untested in the app), **none are left unbuilt**. Earlier summary: 48 of the original 72 modules were built in [`examples/`](examples/README.md), using open-weight models
  only: 23 are separate ComfyUI workflows (video outpainting, Chatterbox text-to-speech/voice clone, motion transfer, character replacement, text/image-to-video, first/last frame,
  video edit, image edit, inpaint, outpaint, background removal, layer decomposition, upscale, music, image-to-3D, several
  text-to-image models, style reference, two-reference compose), 20 are presets that reuse those workflows (UGC video, click-to-ad, shorts, AI influencer, ad variants, re-shoot angles, narration, image reframe, camera angles, viral effects,
  multishot, character sheet, identity, product shots, thumbnails, ads, brand assets, sprites, studio presets) and 5 are local CPU effects (`app/fx.py`: thermal palettes, retro looks, deflicker, burned captions, typewriter and word-stack text).
- **Last modules finished on 2026-10-22:** montage editing, match-cut reel renderer, subject cuts (face, product, sphere, lens, sticker), Tracelab HUD tracking, virality score card, TikTok export and website builder run locally on CPU with real examples; the faceless narrated video (ElevenLabs + Seedance, then muxed), the trending motion gallery (Wan Animate 2 with preset driving clips) and 3D auto-rig (SAM 3D Body) are wired but untested; credits and plans became a Credits & usage page. Virality is a heuristic score card, not a trained model, and TikTok publishing is an export to TikTok spec plus a caption file (you upload it in TikTok).
  own custom packs, or no usable open workflow found. COVERAGE.md lists each one. [COVERAGE.md](COVERAGE.md) lists every Higgsfield feature, its planned open-weight
  stand-in and its status (`planned` / `built` / `tested`).
- **The app runs in mock mode out of the box** (placeholder outputs, no ComfyUI needed). Real runs through the app's `comfy-sdk`
  path are implemented and unit-tested against a stub, and **verified end to end for 13 modules** (app -> `comfy-sdk` -> Cloud -> result): `image.bg-remove`, the camera-rig video module, video reframe, text-to-speech, voice clone, narration, image reframe, re-shoot angles, AI influencer, ad multiplier, UGC video, click-to-ad and shorts studio. The rest were rendered with Comfy Cloud's template runner using the same node ids and prompts.

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
template runner using the node ids in `registry/wiring.py`; **the app's own `comfy-sdk` submission path has been run live for 13 modules (see Status)**.
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
with no voice-over. Instructions are at the top of the script.

**Watch it:** [codyclack.github.io/opensfield/demo](https://codyclack.github.io/opensfield/demo/) (117 s) · [download from the v1.0 release](https://github.com/codyclack/opensfield/releases/download/v1.0/OpenSfield_demo.mp4)

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
