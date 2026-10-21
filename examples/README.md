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

Known quirks: the first frame of `driving_dance.mp4` is a torso crop (the model's opening frame), and the push-in shot
crops to the torso and shifts the hair colour. These are model behaviour, not post-processed.
