---
title: Run OpenSfield on your own ComfyUI
category: Guides
date: 2026-10-20
cover: examples/motion_transfer.mp4
excerpt: No cloud, no key. Point OpenSfield at a local ComfyUI and run the open-weight tools on your own GPU.
---
## Install

```
git clone https://github.com/codyclack/opensfield
cd opensfield
uv sync --extra comfy --extra fx
```

## Point it at your ComfyUI

```
set OPENSFIELD_MODE=comfy
set COMFY_BASE_URL=http://127.0.0.1:8188
set OPENSFIELD_PARTNER=0
uv run uvicorn app.main:app --port 8765
```

Open http://localhost:8765. Every tool's workflow is in `features/<id>/workflow_ui.json`: open it in ComfyUI once to download its models, then run it from OpenSfield.

## No GPU?

Use Comfy Cloud: create an API key at platform.comfy.org, double-click `start_opensfield.bat` and paste it once. It is stored encrypted on your computer.

## Mock mode

Without either, the app starts in mock mode: every button works and returns placeholders, so you can explore the UI for free.
