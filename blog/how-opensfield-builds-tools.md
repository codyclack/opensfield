---
title: Inside OpenSfield: how a Comfy template becomes a tool
category: Inside OpenSfield
date: 2026-10-21
cover: examples/models/kling-v3-video.mp4
excerpt: 146 tools, one pattern: a manifest plus a workflow. How the generator reads Comfy's official templates and builds each form automatically.
---
## A tool is a manifest plus a workflow

Each tool lives in `features/<id>/`: the ComfyUI workflow (`workflow_ui.json`), the API graph comfy-sdk submits (`workflow_api.json`), and a manifest that maps form inputs to node ids.

## Partner models are generated

`scripts/gen_models.py` downloads each official template from Comfy-Org/workflow_templates, converts it to API format with Comfy Cloud's node catalog, then reads the node specs to build the form: image loaders become upload tiles, the prompt widget becomes the prompt box, combos become option chips, and plumbing (codecs, system prompts) stays hidden.

## Verified means rendered

A tool is **Ready** only after it rendered through the app's own path (runner → comfy-sdk → Comfy Cloud) and the output is in `examples/`. Everything else is marked untested. `COVERAGE.md` lists every Higgsfield feature and its status.

## Presets reuse workflows

Viral effects, UGC, click-to-ad and Cinema Studio's pickers don't need new graphs: they write better prompts into a proven workflow.
