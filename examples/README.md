# Example outputs

**`apps/`** (2026-10-22): one example per Higgsfield app, made through the app itself (`scripts/render_app_examples.py` calls
`app/runner.py`, which drives a self-hosted ComfyUI over its HTTP API) on one Quadro RTX 6000, open weights only. Photo apps use
Qwen-Image-Edit 2511 int8 in Fast mode (4-step Lightning LoRA), about 50-90 s each; swap and try-on apps give it two photos
(`garment_puffer.png` is the garment, cut from `char_b.png` by the same model). Video apps use LTX-2.3 at 512x768, 3 s, about 7 min a
clip. The input photos are `char_a.png`, `char_b.png`, `t2i_flux3_sneakers.png`, `influencer_cafe.png`, `style_reference_alley.png` and
`sketch_input.png`; which app used which is in `scripts/render_app_examples.py`, and `registry/apps_examples.json` records each file.

Real renders from Comfy Cloud on 2026-10-21 using the workflows in `features/`, with open-weight models only
(Z-Image Turbo, LTX-2.5, Wan Animate 2). All people are AI-generated and fictional. No real likenesses and no
third-party footage or template sample assets are used. Each render was queued with overrides addressed by the node ids in
`registry/wiring.py`, which is how the wiring map was confirmed.

| File | Module | Inputs | GPU time |
|---|---|---|---|
| `char_a.png` | `soul.t2i` | seed 11, 768x1152. "full-body photo of a fictional young woman ... black hoodie, cargo trousers, white sneakers, short dark bob" | 5 s |
| `char_b.png` | `soul.t2i` | seed 12, 768x1152. "fictional young man ... orange puffer jacket, grey joggers, red high-tops, curly hair" | 11 s |
| `cinema_camera_rig_dance.mp4` | `cinema.camera-rig` | start frame `char_a.png`, seed 7, 5 s. Prompt: relaxed street dance with a slow eye-level push-in, 35mm | 18 s |
| `driving_dance.mp4` | `cinema.camera-rig` | start frame `char_a.png`, seed 9, 5 s. Prompt: locked-off static wide shot, full-body dance | 36 s |
| `first_last_frame_morph.mp4` | `cinema.first-last-frame` | first `char_a.png`, last `char_b.png`, 704x1024, seed 7. Prompt: spin, flash of light, she becomes him | 20 s |
| `motion_transfer.mp4` | `genjutsu.motion-control` | character `char_b.png`, driving `driving_dance.mp4`, seed 7 | 74 s |
| `motion_transfer_compare.mp4` | `genjutsu.motion-control` | same job, driving clip beside the result | (same job) |

Second batch (same day, same conditions; inputs reuse `char_a.png`, `char_b.png` and the clips above):

| File | Module | Inputs |
|---|---|---|
| `image_edit_yellow_hoodie.png` | `image.edit-open` (Qwen-Image-Edit 2511) | `char_a.png`, seed 7. "Change the black hoodie to a bright yellow hoodie. Keep the person, face, pose, trousers, shoes and background exactly the same." |
| `bg_remove_cutout.png`, `bg_remove_mask.png` | `image.bg-remove` (BiRefNet) | `char_b.png`. The cutout is RGBA (about 75% of pixels transparent); some viewers show it flattened |
| `upscale_2x.png` | `image.upscale` (SeedVR2 3B int8) | `char_a.png`, 2x, 768x1152 to 1536x2304 |
| `video_upscale.mp4` | `video.upscale` (SeedVR2 3B int8) | `motion_transfer.mp4`, 480x848 to 960x1696 |
| `music_lofi.mp3` | `audio.music` (ACE-Step 1.5 XL Turbo) | 30 s, 80 BPM, "lo-fi hip hop, warm vinyl crackle, mellow electric piano, soft drums, instrumental", seed 5 |
| `text_to_video_alley.mp4` | `video.t2v-i2v-open` (LTX-2.5 text-to-video) | seed 5, 5 s, 16:9. A neon-lit rainy alley with a cyclist in a yellow raincoat |
| `replace_character_a.mp4`, `replace_character_b.mp4` | `genjutsu.replace-object` (SCAIL-2 int8) | source `driving_dance.mp4`, replacement `char_b.png`, replace "woman", seed 7. The template has two parallel branches and both outputs are kept |
| `image_to_3d.glb` | `scene3d.image-to-3d` (Hunyuan3D 2.0) | `char_b.png`. Valid glTF binary (3.4 MB); the mesh was not inspected visually |

Third batch (same day). Preset modules were rendered with the app's own prompt assembly (`scripts/overrides.py`), so the prompts below are what the app sends.

| File | Module | Notes |
|---|---|---|
| `t2i_flux3_sneakers.png` | `image.t2i-open` (FLUX 3 Klein) | seed 5, 3:2. White chunky sneakers on a wet concrete step at dawn |
| `cinematic_krea.png` | `soul.cinematic` (Krea-2 Turbo) | seed 5, 16:9. Rain-lit street, woman in a long coat |
| `soul_cast.png` | `soul.cast` (Qwen Image 2.1, two references) | `char_a.png` + `char_b.png`, "put both together side by side". An outfit-swap instruction returned a composite instead, so this module is a two-reference compose |
| `style_reference_out.png` | `soul.styles` (Krea-2 style reference) | style image `style_reference_alley.png`; subject "chunky sneakers on a wet city street" |
| `inpaint_out.png` | `image.inpaint-brush` (FLUX.1 Fill) | input `inpaint_input.png` (transparent = repaint area); "a bright red leather jacket over a white t-shirt" |
| `outpaint_out.png` | `image.outpaint` (FLUX.1 Fill) | `char_a.png`, 256 px each side, 768 to 1280 wide |
| `layers_0.png` to `layers_2.png` | `image.decompose` (Qwen-Image-Layered) | `char_b.png`, 3 layers. Layer 0 is the full composite, layer 1 is nearly empty, layer 2 is a legs fragment: the module works but the split is not clean |
| `video_edit_street.mp4` | `video.edit` (Bernini-R) | source `driving_dance.mp4` + a generated street photo as reference; the studio becomes a brick street, the dancer and her motion are kept |
| `soul_id.png` | `soul.id` (Qwen-Image-Edit 2511) | `char_b.png`, "walking along a beach at sunset in golden light" |
| `character_sheet.png` | `soul.character-sheet` (Qwen-Image-Edit 2511) | `char_b.png`; front, side and back views |
| `effect_clones.mp4`, `effect_vanish.mp4` | `viral.effects` (LTX-2.5 i2v presets) | 2 of the 6 authored effect presets rendered. Clones multiplies the person; Vanish collapses the figure onto the floor |
| `multishot.mp4` | `cinema.multishot` (LTX-2.5) | 8 s, two shots with a hard cut to a close-up (the face is a different person: no identity lock) |
| `product_orbit.mp4` | `marketing.studio-presets` (LTX-2.5) | "Orbit" preset: the camera barely moves, so treat this preset as weak |
| `product_photoshoot.png` | `marketing.product-photoshoot` | the sneaker image onto a white studio packshot |
| `thumbnail_hero.png` | `marketing.thumbnails` | "Hero object" framework, 16:9; the crop is tight |
| `ad_social.png` | `marketing.ads-studio` (FLUX 3 Klein) | "Social product ad" with an in-image headline |
| `brand_logo.png` | `marketing.brand-assets` (FLUX 3 Klein) | "Logo mark" preset; no text, as requested |
| `angle_low.png` | `scene3d.angles` (Qwen-Image-Edit 2511) | `char_b.png`, "Low angle" preset: same person from below with dramatic perspective |
| `sprite_sheet.png` | `scene3d.autosprite` (Z-Image Turbo) | 4x4 walk-cycle grid of a knight on green |
| `fx_captions.mp4`, `fx_typewriter.mp4`, `fx_wordstack.mp4` | `audio.captions`, `matchcut.text-motion` | Local CPU text looks. Captions are your own lines spread evenly over the clip: there is no speech recognition |
| `flicker_input.mp4` -> `fx_deflicker.mp4` | `video.deflicker` | Local CPU. Random brightness flicker was injected into `driving_dance.mp4`; frame-to-frame brightness jitter dropped from 36.9 to 8.7 |
| `fx_thermal_blackhot.mp4`, `fx_thermal_rainbow.mp4`, `fx_crt.mp4`, `fx_vhs.mp4`, `fx_nokia.mp4` | `matchcut.thermal`, `matchcut.retro-fx` | **Local CPU effects** (`app/fx.py`), not Comfy workflows. Source `driving_dance.mp4`, first 4 s at 640 px |

| `style_yarn.mp4` | `genjutsu.styles` (LTX-2.3 IC-LoRA) | control video `driving_dance.mp4`, restyled first frame `style_yarn_frame.png` (made with Qwen-Image-Edit from `style_source_frame.png`: "knitted wool yarn world"). The dance and framing carry over and the world is knitted, but the person is redrawn as someone else |

Tried and not shipped: `video.lipsync` (LTX-2.3 image+audio: kept the face for one frame, then invented a different scene), `soul.location` (two-image template returned corrupted images for portrait + landscape inputs in three attempts).

Known quirks: the first frame of `driving_dance.mp4` is a torso crop (the model's opening frame), and the push-in shot
crops to the torso and shifts the hair colour. These are model behaviour, not post-processed.

## Fourth batch (2026-10-21, through the app's own comfy-sdk path)
| Module | File | Notes |
|---|---|---|
| video.reframe | `video_reframe_916.mp4` | LTX-2.3 outpainting IC-LoRA, 16:9 dance clip extended to 9:16 (640x1120) |
| audio.tts | `tts_chatterbox.flac` | Chatterbox, voice from `voice_sample.wav` (a synthetic Windows voice, used only as the sample) |
| audio.voice-clone | `voice_clone.flac` | same workflow, labelled for cloning |
| audio.narration | `narration.flac` | same workflow, narration script input (no timing fit) |
| image.reframe | `image_reframe.png` | Flux Fill outpaint with a continue-the-scene prompt |
| reshoot.novel-view | `reshoot_over_shoulder.png` | Qwen Image Edit 2511, "over the shoulder" preset. A still-frame re-angle, not a video re-shoot |
| marketing.ai-influencer | `influencer_cafe.png` | Qwen Edit, coffee shop preset |
| marketing.ad-multiplier | `ad_variant_new_bg.png` | Qwen Edit, "new background" variant. Image variants only |
| marketing.ugc-video | `ugc_review.mp4` | LTX-2.5 i2v, product review preset |
| marketing.click-to-ad | `click_to_ad.mp4` | LTX-2.5 i2v from a product image. No URL scraping |
| marketing.shorts-studio | `shorts_vertical.mp4` | LTX-2.5 t2v, 9:16 |

Quirk found: the first AI-influencer run came back as noise with a "show them taking a selfie" prompt; rewording it like the working soul.id prompt ("change the scene around them so that they are ...") fixed it.
