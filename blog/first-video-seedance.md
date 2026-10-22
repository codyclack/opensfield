---
title: Your first video in five minutes (Seedance 2.5)
category: Guides
date: 2026-10-22
cover: examples/models/seedance2-5-i2v-1080p.mp4
excerpt: Pick a start frame, write one sentence, press Generate. The fastest way to see what OpenSfield can do, and what each setting changes.
---
## What you need

- OpenSfield running (`start_opensfield.bat`, or `uv run uvicorn app.main:app --port 8765`)
- A Comfy API key if you want partner models like Seedance. Open-weight tools also run on your own ComfyUI.
- One image. A product photo, a portrait or a frame from your phone all work.

## 1. Open the Video page

Click **Video** in the top bar. You land on **Create Video** with **Seedance 2.5** already selected in the Model row. Hover **Video** instead of clicking it to jump straight to Text to Video, References, First & Last, Motion Control or Edit Video.

## 2. Add a start frame

Drop your image on the **Add image** tile, or press **From assets** to reuse an element you saved before. The first frame of the clip will match this image.

## 3. Write the shot, not the story

Describe what happens in the next five seconds, in camera language:

> The woman turns toward the camera and smiles, slow push-in, warm window light, shallow depth of field.

Short and concrete beats long and poetic. One action, one camera move, one light.

## 4. Set the chips

- **720p** is the default. 1080p looks better and costs a lot more credits on Seedance.
- **Ratio**: `adaptive` keeps your image's shape. Pick `9:16` for Reels and TikTok.
- **Duration**: start with 5 s. Longer clips cost more and drift more.

## 5. Generate and iterate

Press **Generate** (or Ctrl+Enter). The clip appears in **History** on the right. Hover it to **download**, **★ save it to Elements**, **♥ favorite** it, or **↺ reuse** the exact settings for the next take. Change one thing per take.

## Prefer open weights?

Open the Model list and pick **LTX-2.5 (open)**. Same form, runs on any ComfyUI, costs only GPU time.
