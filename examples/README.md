# Example outputs

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

Known quirks: the first frame of `driving_dance.mp4` is a torso crop (the model's opening frame), and the push-in shot
crops to the torso and shifts the hair colour. These are model behaviour, not post-processed.
