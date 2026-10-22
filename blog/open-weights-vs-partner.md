---
title: Open weights or partner models? What runs where, and what it costs
category: Editorials
date: 2026-10-21
cover: examples/text_to_video_alley.mp4
excerpt: Every task in OpenSfield has both kinds of model in one picker. A plain guide to the trade-offs.
---
## Two kinds of tool

- **Open weights** (tagged OPEN): LTX-2.5/2.3, Wan Animate 2, SCAIL-2, Qwen Image Edit, FLUX, Z-Image, SeedVR2, ACE-Step, Chatterbox, Hunyuan3D. They run on any ComfyUI, including your own GPU, and on Comfy Cloud you pay only GPU seconds.
- **Partner models**: Seedance, Kling, MiniMax, Wan 3, Grok, Nano Banana, GPT Image, Ideogram, ElevenLabs and more, through Comfy's API nodes. They need a Comfy API key and spend Comfy credits.

## Cost, roughly

Image models cost 1 to 20 credits a run. Video models cost much more: a 5 s Seedance 2.5 clip at 1080p showed about 865 credits in Comfy Cloud's billing feed in our tests, so OpenSfield defaults Seedance to 720p. Check the number on the Generate button before you press it.

## Picking

- Drafting and iterating: open weights or cheap partner images.
- Final hero shots: Seedance 2.5, Kling 3.0.
- Text in images: Ideogram.
- Privacy or offline work: open weights on your own machine.

## Hide partner models

Set `OPENSFIELD_PARTNER=0` before starting the app and only open-weight tools are shown.
