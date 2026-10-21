# OpenSfield

Open-source rebuild of Higgsfield's creative apps on ComfyUI, for Comfy's
**#OpenSourceHiggsfield** challenge. Open weights by default; an optional
`partner/` pack adds Comfy Router models.

Status: **scaffolding + mock-mode app shell.** No workflow has been run yet (Comfy testing is on hold).
See [COVERAGE.md](COVERAGE.md) for the full Higgsfield -> OpenSfield feature map.

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
- `generators/` — `make_*.py` workflow generators (todo)

## Workflows: rendered on Comfy Cloud
Four hero modules have real workflows wired from official Comfy templates, and each has a real render in
[`examples/`](examples/README.md) (open-weight models only; 5 to 74 s of GPU each). They were run through Comfy Cloud's
template runner using the node ids in `registry/wiring.py`; **the app's own `comfy-sdk` submission path has not been run yet**.
Wiring is also checked statically by `tests/test_wiring.py`.

| Module | Template | Model family |
|---|---|---|
| `genjutsu.motion-control` | `video_wan_animate2_distilled` | Wan Animate 2 (int8) |
| `cinema.camera-rig` | `video_ltx2_5_i2v` | LTX-2.5 |
| `cinema.first-last-frame` | `video_ltx2_5_flf2v` | LTX-2.5 |
| `soul.t2i` | `image_z_image_turbo` | Z-Image Turbo |

Each `features/<id>/` holds `workflow_ui.json` (open in ComfyUI), `workflow_api.json` (what `comfy-sdk` submits) and the
manifest, whose `workflow.inputs` says which node/field each form input drives. `registry/wiring.py` is the source of that map.
`comfy-sdk` only accepts API format, and the templates use subgraphs, so the API files were converted against a node catalog:
re-export against whichever server will run them (read-only, it only GETs `/object_info`):

```bash
uv run --with comfy-cli scripts/export_api.py --base http://127.0.0.1:8188
uv run scripts/build_registry.py && uv run --extra dev --extra comfy pytest
```
Template example assets (their sample character/driving clip) are not used; supply your own inputs.

## Regenerate coverage
```bash
uv run scripts/build_registry.py
```

## Run locally (todo, after workflows exist)
`pip install comfy-sdk` and point `COMFY_BASE_URL` at a local ComfyUI (via
`comfy-api-proxy`) or a Comfy API deployment.

License: MIT.
