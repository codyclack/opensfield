---
title: Viral effects in three clicks
category: Guides
date: 2026-10-21
cover: examples/effect_clones.mp4
excerpt: Clones, Vanish, Giant, Eyes in. Upload a photo, pick an effect, generate. How the presets work and how to make your own.
---
1. Top bar → **Viral** → **Viral effect chains**.
2. Add a photo of a person. Full body works best for Clones, Vanish and Giant; a face close-up for Eyes in.
3. Pick an effect card and press **Generate**.

The tool runs on **Seedance 2.5** by default. Open the Model list to switch to the open **LTX-2.5** version.

## What a preset really is

Hover an effect to read its prompt. A preset is a carefully written shot description added in front of your own text. Add a line of your own in **Subject detail** ("she is wearing a yellow raincoat") to steer it.

## Make your own

Presets live in `registry/wiring.py` (`EFFECTS`). Add a name and a prompt, run `uv run scripts/build_registry.py`, refresh the app.
