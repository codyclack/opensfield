---
title: One prompt, eight image models: which one to pick
category: Listicles
date: 2026-10-21
cover: examples/models/bfl-flux3-t2i.png
excerpt: We ran the same sneaker prompt through eight image models in OpenSfield. Here is what each one is good at, what it costs, and when to switch.
---
All eight runs used the prompt *"a pair of white sneakers on a wet city street at dusk, soft light"*, default settings, through the app's own comfy-sdk path. Credits are what Comfy Cloud's billing feed showed per run on 2026-10-21.

1. **GPT Image 2** (about 2 credits). Clean product look, very cheap. The default on the Image page.
2. **Nano Banana 2.1** (about 12). Strong photorealism, excellent at edits that keep the subject.
3. **FLUX 3** (about 14). Rich lighting and texture; expands short prompts well.
4. **Recraft 4.1**. Stylised, poster-friendly compositions.
5. **Kling 3.0** (about 6). Cinematic framing, good starting frames for video.
6. **Ideogram 4.5** (about 18). The one to pick when the image needs readable text.
7. **Krea 3**. Fashion and product staging with a soft editorial feel.
8. **Qwen Image 3** (about 12). Dense layouts: posters, menus, storyboards.

## How to switch

On the Image page, click the model chip in the prompt bar and pick another. Your prompt stays, so A/B tests take one click.

## Open-weight alternatives

FLUX 3 Klein, Z-Image Turbo, Krea 2 and Qwen-Image run on your own ComfyUI with no credits. They are under **Image models** in Apps.
