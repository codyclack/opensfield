"""Seed registry of every Higgsfield feature -> OpenSfield implementation plan.

Source: Higgsfield MCP catalog (models_explore, get_presets, apps_search,
get_workflow_instructions) + Comfy's 'Open Source Higgsfield' brief, Oct 2026.

Tier  A = hand-built + smoke-tested through comfy-sdk
      B = generated from a base workflow + preset/parameter data
      C = mapped only / out of scope (reason in `note`)
Track open = open-weights only, partner = needs Comfy Router/partner nodes.
Everything starts as status 'planned'; build/smoke scripts promote it.
"""

# base workflow ids (the ~18 graphs everything else is generated from)
BASES = {
    "wan_animate2": "Wan Animate 2 motion transfer / replace (template video_wan_animate2[_distilled])",
    "ltx25_i2v": "LTX-2.5 image->video (template video_ltx2_5_i2v)",
    "ltx25_t2v": "LTX-2.5 text->video (template video_ltx2_5_t2v)",
    "ltx25_flf2v": "LTX-2.5 first/last frame (template video_ltx2_5_flf2v)",
    "ltx23_ic_lora": "LTX-2.3 IC-LoRA control: depth/pose/edges (template video_ltx2_3_ic_lora)",
    "ltx23_audio": "LTX-2.3 image+audio->video, ID-LoRA lip-sync/voice (templates video_ltx2_3_ia2v / _id_lora)",
    "t2i": "Z-Image / Flux text->image (local: Z-Image Turbo, Flux dev fp8)",
    "ref_edit": "Reference-image edit/compose (Flux Redux/Kontext, Qwen-Image-Edit)",
    "flux_redux_blend": "Flux Redux two-image style blend",
    "fill": "Flux Fill inpaint / outpaint",
    "upscale": "SeedVR2 / ESRGAN image+video upscale + deflicker",
    "matte": "SAM3 / RMBG matte (image + video background removal)",
    "planner_llm": "QwenVL (installed) as shot/ad/copy planner",
    "tts_audio": "TTS + voice clone + music + SFX + Whisper captions",
    "hunyuan3d": "Image -> 3D mesh",
    "postfx": "OpenCV/ffmpeg post nodes (CRT, VHS, glitch, nightvision, typography)",
    "thermal": "Thermal look (black/white-hot, rainbow), app/fx.py",
    "moondream_hud": "EXISTING Moondream-tracked HUD node set (Tracelab)",
    "stitch": "VideoHelperSuite concat/trim/audio mux",
}


def f(id, studio, name, tier, base, hf, track="open", note="", count=1, partner=None):
    return dict(id=id, studio=studio, name=name, tier=tier, base=base, higgsfield=hf,
                track=track, note=note, count=count, partner=partner or [], status="planned")


FEATURES = [
    # ---------------- Genjutsu (named in the contest brief) ----------------
    f("genjutsu.motion-control", "Genjutsu", "Motion transfer (image + driving video)", "A", ["wan_animate2"],
      "hf_mult_motion_control, hf_mult_motion_control_flash", note="Contest-named target. Template is Int8; prove on Turing first."),
    f("genjutsu.replace-object", "Genjutsu", "Replace character/object in a video", "A", ["wan_animate2", "matte"],
      "hf_mult_replace_object, hf_mult_replace_object_flash", note="'Openjutsu' in the Comfy brief."),
    f("genjutsu.styles", "Genjutsu", "Restyle a video, keep its motion", "B", ["ltx23_ic_lora", "ref_edit"],
      "genjutsu-styles (e.g. Knitted Yarn World, Rounded Toy CGI)", note="Style presets = prompt+LoRA data."),
    f("genjutsu.motion-gallery", "Genjutsu", "Trending/new motion preset gallery", "B", ["wan_animate2"],
      "genjutsu / genjutsu-trending / genjutsu-new", count=12, note="Driving-video library; 12 trending seen (Athlete Dance Swap, Skyway Chase...). Must use own/licensed driving clips."),
    # ---------------- Cinema Studio (named in the brief) ----------------
    f("cinema.director", "Cinema Studio", "AI Director: concept -> shot list", "A", ["planner_llm"],
      "cinematic_studio_2_5 / 3_0 / video_4_0 director", note="QwenVL planner outputs per-shot JSON."),
    f("cinema.camera-rig", "Cinema Studio", "Camera body / lens / focal / move controls", "A", ["ltx25_i2v"],
      "cinematic_studio_video(_v2)", note="Camera language -> prompt grammar + optional camera LoRAs."),
    f("cinema.multishot", "Cinema Studio", "Multi-shot sequence + stitch", "A", ["ltx25_i2v", "ltx25_flf2v", "stitch"],
      "cinematic_studio_3_0 / 4_0, nano_banana_2_shots"),
    f("cinema.first-last-frame", "Cinema Studio", "First/last-frame transitions", "A", ["ltx25_flf2v"], "kling_o3_flf, FLF"),
    f("cinema.draw-to-video", "Cinema Studio", "Sketch/annotation -> video", "B", ["ltx23_ic_lora"], "draw_to_video"),
    f("cinema.extend", "Cinema Studio", "Extend / continue a clip", "B", ["ltx25_i2v", "stitch"], "video extend"),
    # ---------------- Reshoot / 3D ----------------
    f("reshoot.novel-view", "Reshoot", "Re-shoot a video/shot from any angle", "A", ["ref_edit", "ltx23_ic_lora"],
      "3d_jutsu_angles, Scene Builder angles", note="Contest-named 'Re-shoot'."),
    f("scene3d.angles", "Reshoot", "New camera views of a location/product", "B", ["ref_edit"], "3d_jutsu_angles, soul_location angles"),
    f("scene3d.image-to-3d", "Reshoot", "Image(s) -> 3D model", "B", ["hunyuan3d"], "sam_3_3d, image_to_3d, multi_image_to_3d, meshy_*"),
    f("scene3d.rigging", "Reshoot", "Auto-rig 3D character", "C", [], "3d_rigging, meshy_rigging", note="No solid open Comfy path; out of scope."),
    f("scene3d.autosprite", "Reshoot", "Sprite sheet generation", "B", ["t2i"], "autosprite"),
    # ---------------- Viral Hub ----------------
    f("viral.effects", "Viral Hub", "Viral effect chains (87 presets)", "B", ["ref_edit", "ltx25_flf2v", "ltx25_i2v"],
      "get_presets source=viral (effects/motion/product-shot)", count=87,
      note="Chain = start-frame edit -> FLF2V/I2V with effect prompt. 15 seen: Floating fall, Vanish, Eyes in, Cutout, Wild ride, Lidar transition, Smash and grab, Incline, Clones, Infinite clones, Selfception, Act natural, Monster dab, Street colossus, World morphing. Remaining 72 enumerated at build time."),
    # ---------------- Soul / Characters ----------------
    f("soul.t2i", "Soul", "Soul 2.0 photoreal text->image", "A", ["t2i"], "soul_2, soul_v2"),
    f("soul.cinematic", "Soul", "Soul Cinematic / Cinema stills", "A", ["t2i"], "soul_cinematic, soul_cinema_studio"),
    f("soul.cast", "Soul", "Soul Cast: character from reference", "B", ["ref_edit"], "soul_cast"),
    f("soul.location", "Soul", "Soul Location: place from reference", "B", ["ref_edit"], "soul_location"),
    f("soul.id", "Soul", "Soul ID: reusable character identity", "B", ["ref_edit", "flux_redux_blend"], "Soul ID",
      note="Reference-based identity (no training) in v1; LoRA trainer is stretch."),
    f("soul.styles", "Soul", "Soul style presets", "B", ["t2i", "flux_redux_blend"], "get_presets source=soul", count=1, note="Style = prompt/LoRA/Redux data."),
    f("soul.character-sheet", "Soul", "Character sheets / turnarounds", "B", ["t2i", "ref_edit"], "workflow character-sheet"),
    # ---------------- Image models (roster) ----------------
    f("image.t2i-open", "Image models", "Open text->image (Flux 3/2, Z-Image, Qwen-Image)", "A", ["t2i"], "flux_2, flux_3_image, z_image, flux_kontext"),
    f("image.edit-open", "Image models", "Open reference edit/compose (Nano Banana-style)", "A", ["ref_edit"],
      "nano_banana, nano_banana_pro, nano_banana_2*, kling_omni_image", partner=["comfy-router: nano-banana"]),
    f("image.partner-roster", "Image models", "Partner image models via Router", "C", [], "gpt_image_2/2_5, seedream_v4_5/v5*, grok_image*, ideogram_4_5, recraft_v4*, openai_hazel",
      track="partner", note="Only in optional partner/ pack. Not in the open-weights entry.", partner=["comfy-router"]),
    # ---------------- Image tools ----------------
    f("image.bg-remove", "Image tools", "Background remover", "A", ["matte"], "image_background_remover"),
    f("image.outpaint", "Image tools", "Outpaint / generative expand", "B", ["fill"], "outpaint, flux_2_pro_outpaint"),
    f("image.upscale", "Image tools", "Upscale (Topaz-style)", "B", ["upscale"], "topaz_image(_generative), bytedance_image_upscale"),
    f("image.decompose", "Image tools", "Decompose image into layers", "B", ["ref_edit"], "image_decompose", note="Qwen-Image-Layered if available."),
    f("image.reframe", "Image tools", "Reframe / aspect-ratio change", "B", ["fill"], "reframe"),
    f("image.inpaint-brush", "Image tools", "Brush inpaint / edit region", "B", ["fill"], "Marketing Studio brush inpainting"),
    # ---------------- Video tools ----------------
    f("video.upscale", "Video tools", "Video upscale", "B", ["upscale"], "topaz_video, topaz_hyperion_2_5, video_upscale, bytedance_video_upscale"),
    f("video.deflicker", "Video tools", "Deflicker", "B", ["upscale"], "video_deflicker"),
    f("video.bg-remove", "Video tools", "Video background remover", "B", ["matte"], "video_background_remover"),
    f("video.reframe", "Video tools", "Reframe video (9:16 etc.)", "B", ["matte", "stitch"], "reframe"),
    f("video.clipify", "Video tools", "Long video -> viral clips", "B", ["tts_audio", "planner_llm", "stitch"], "clipify"),
    f("video.lipsync", "Video tools", "Lip-sync", "A", ["ltx23_audio"], "sync_so"),
    f("video.edit", "Video tools", "Prompt-based video edit", "B", ["ltx23_ic_lora", "wan_animate2"], "kling_video_edit, flux_3_video_edit"),
    f("video.t2v-i2v-open", "Video models", "Open text/image->video (LTX 2.5, Wan)", "A", ["ltx25_t2v", "ltx25_i2v"],
      "seedance*, kling2_6/3_0*, wan2_6, minimax_hailuo, grok_video*, happy_horse_video", note="Open stand-ins for the whole video-model roster. Contest LTX VFX bonus lives here."),
    f("video.partner-roster", "Video models", "Partner video models via Router", "C", [], "seedance_2_0/2_5, kling3_0, minimax_h3(_max), grok_video_v15, veo, sora",
      track="partner", note="Optional partner/ pack only.", partner=["comfy-router: seedance, minimax-h3"]),
    # ---------------- Audio ----------------
    f("audio.tts", "Audio", "Text to speech", "B", ["tts_audio"], "text2speech_v2, qwen_audio_tts, seed_audio, inworld_text_to_speech, elevenlabs_v4(_turbo)"),
    f("audio.voice-clone", "Audio", "Voice clone / create voice", "B", ["tts_audio"], "create_voice, create_voice_from_confirmed_audio"),
    f("audio.voice-change", "Audio", "Voice change", "B", ["tts_audio"], "voice_change"),
    f("audio.dubbing", "Audio", "AI dubbing / translation", "B", ["tts_audio", "planner_llm", "ltx23_audio"], "dubbing"),
    f("audio.music", "Audio", "Music generation", "B", ["tts_audio"], "sonilo_music"),
    f("audio.sfx", "Audio", "Sound effects", "B", ["tts_audio"], "mirelo_text_to_audio"),
    f("audio.narration", "Audio", "Narration fitted to timing", "B", ["tts_audio", "stitch"], "workflow narration"),
    f("audio.captions", "Audio", "Burned captions", "B", ["tts_audio", "postfx"], "video-montage captions"),
    # ---------------- Marketing ----------------
    f("marketing.click-to-ad", "Marketing", "Product URL -> video ad", "B", ["planner_llm", "ref_edit", "ltx25_i2v", "tts_audio", "stitch"], "Click-to-Ad"),
    f("marketing.ugc-video", "Marketing", "UGC video (review, unboxing, try-on, tutorial, site tour)", "B", ["ref_edit", "ltx23_audio", "tts_audio"], "workflow ugc-video", count=6),
    f("marketing.ads-studio", "Marketing", "Static ad creatives with copy", "B", ["planner_llm", "ref_edit"], "ads_studio_*"),
    f("marketing.product-photoshoot", "Marketing", "Product photoshoot / packshot / try-on", "B", ["ref_edit", "matte"], "workflow product-photoshoot"),
    f("marketing.thumbnails", "Marketing", "YouTube/IG thumbnails", "B", ["t2i", "ref_edit", "postfx"], "workflow thumbnail-generation (16 frameworks)", count=16),
    f("marketing.brand-assets", "Marketing", "Logos, brand kits, mockups", "B", ["t2i", "ref_edit"], "workflow brand-asset-creation"),
    f("marketing.ad-multiplier", "Marketing", "Multiply one ad into variants (edit / recreate)", "B", ["wan_animate2", "ref_edit", "matte"], "ad_multiplier, ad_multiplier_v2"),
    f("marketing.katana", "Marketing", "Reference-edit remix (Katana)", "C", ["planner_llm", "wan_animate2"], "workflow katana", note="Stretch; depends on Ad Multiplier + Genjutsu."),
    f("marketing.faceless-video", "Marketing", "Faceless narrated channel video", "B", ["planner_llm", "t2i", "ltx25_i2v", "tts_audio", "stitch"], "workflow faceless-video", count=5),
    f("marketing.shorts-studio", "Marketing", "Shorts studio sessions/presets", "B", ["planner_llm", "ltx25_i2v", "tts_audio", "stitch"], "shorts_studio_*"),
    f("marketing.ai-influencer", "Marketing", "AI influencer (character + presets)", "B", ["ref_edit", "ltx23_audio"], "ai_influencer_*"),
    f("marketing.studio-presets", "Marketing", "Marketing Studio product-shot / motion presets", "B", ["ref_edit", "ltx25_i2v"], "get_presets source=marketing_studio", count=1),
    f("marketing.video-edit-montage", "Marketing", "Montage / Higgsedit-style edits", "C", ["stitch", "postfx"], "video-editing, video-montage", note="ffmpeg-level; shipped as a thin helper."),
    # ---------------- Match Cut + Tracelab (28 actions in the Higgsfield app) ----------------
    f("matchcut.tracelab", "Match Cut + Tracelab", "Tracelab: track objects/faces + HUD overlays", "A", ["moondream_hud"], "create_tracelab", note="Existing CC HUD node set."),
    f("matchcut.thermal", "Match Cut + Tracelab", "Thermal / black-hot / white-hot / rainbow", "A", ["thermal"], "create_thermal, create_black_hot, create_white_hot, create_rainbow_thermal", count=4, note="Thermal look, rendered locally by app/fx.py."),
    f("matchcut.retro-fx", "Match Cut + Tracelab", "CRT / CRT-glitch / VHS / glitch / Nokia / retropop / night-vision", "B", ["postfx"],
      "create_crt, create_crtglitch, create_vhs, create_glitch, create_nokia, create_retropop, create_nightvision", count=7),
    f("matchcut.subject-cuts", "Match Cut + Tracelab", "Face/search/logo/product/sticker/sphere/lens cuts", "B", ["matte", "postfx"],
      "create_facecut, searchcut, logocut, productcut, stickercut, spherecut, lenscut", count=7),
    f("matchcut.text-motion", "Match Cut + Tracelab", "Notebook / notereel / scrapboard / wordstack / typewriter / commentcut", "B", ["postfx"],
      "create_notebook, notereel, scrapboard, wordstack, typewriter, commentcut", count=6),
    f("matchcut.render", "Match Cut + Tracelab", "Match-cut reel renderer", "B", ["stitch", "postfx"], "create_render, list_render_modes"),
    # ---------------- Platform (not Comfy-shaped) ----------------
    f("platform.website-builder", "Platform", "Website / app / game builder", "C", [], "website-builder-flow", note="Not a generation workflow; out of scope."),
    f("platform.publish", "Platform", "TikTok publishing", "C", [], "tiktok_*", note="Out of scope."),
    f("platform.virality", "Platform", "Virality predictor", "C", ["planner_llm"], "virality_predictor", note="Possible QwenVL scoring toy; low priority."),
    f("platform.billing-community", "Platform", "Credits, plans, community presets, contests", "C", [], "balance, transactions, publish_project", note="N/A for an open-source local app."),
]

# Higgsfield model id -> (family, open stand-in). Partner-only families have no open stand-in.
MODEL_ROSTER = {
    "Soul / character": (["soul_2", "soul_v2", "soul_cinematic", "soul_cinema_studio", "soul_cast", "soul_location"], "Z-Image Turbo / Flux + reference edit"),
    "Cinema Studio": (["cinematic_studio_2_5", "cinematic_studio_3_0", "cinematic_studio_video", "cinematic_studio_video_v2", "cinematic_studio_video_4_0", "nano_banana_2_shots"], "LTX-2.5 + QwenVL planner"),
    "Marketing Studio": (["marketing_studio_image", "ms_image", "marketing_studio_video", "higgsfield_preset", "image_auto"], "preset engine over base graphs"),
    "Nano Banana": (["nano_banana", "nano_banana_pro", "nano_banana_2", "nano_banana_2_1", "nano_banana_2_lite"], "Qwen-Image-Edit / Flux Kontext (open) | Router nano-banana (partner)"),
    "GPT Image / Hazel": (["gpt_image_2", "gpt_image_2_5", "openai_hazel"], "Flux 3 / Qwen-Image (open) | Router gpt-image (partner)"),
    "Seedream": (["seedream_v4_5", "seedream_v5_lite", "seedream_5_0_flash", "seedream_v5_pro"], "partner-only; open: Flux 3 / Z-Image"),
    "Flux": (["flux_2", "flux_2_pro_outpaint", "flux_3_image", "flux_3_video", "flux_3_video_edit", "flux_kontext"], "Open weights where released; FLUX bonus track candidate"),
    "Other image": (["z_image", "kling_omni_image", "grok_image", "grok_image_2_0", "ideogram_4_5", "recraft_v4_1", "recraft_v4_styles"], "Z-Image (open); rest partner-only"),
    "3D": (["sam_3_3d", "image_to_3d", "multi_image_to_3d", "3d_rigging", "meshy_image_to_3d", "meshy_multi_image_to_3d", "meshy_rigging", "3d_jutsu_angles", "autosprite"], "Hunyuan3D; rigging out of scope"),
    "Audio": (["seed_audio", "qwen_audio_tts", "elevenlabs_v4", "elevenlabs_v4_turbo", "sonilo_music", "mirelo_text_to_audio", "inworld_text_to_speech", "text2speech_v2", "voice_change", "dubbing", "sync_so"], "Kokoro/Chatterbox, ACE-Step, MMAudio, LTX-2.3 audio"),
    "Image tools": (["image_background_remover", "outpaint", "reframe", "topaz_image", "topaz_image_generative", "image_decompose", "bytedance_image_upscale"], "SAM3/RMBG, Flux Fill, SeedVR2"),
    "Video tools": (["video_background_remover", "topaz_hyperion_2_5", "topaz_video", "bytedance_video_upscale", "video_upscale", "video_deflicker", "clipify", "draw_to_video"], "SeedVR2, SAM3, LTX"),
    "Video models": (["minimax_hailuo", "minimax_h3", "minimax_h3_max", "wan2_6", "seedance1_5", "seedance_2_0", "seedance_2_0_mini", "seedance_2_5", "kling2_6", "kling3_0", "kling3_0_turbo", "kling_o3_image_reference", "kling_o3_flf", "kling_video_edit", "happy_horse_video", "grok_video_v15", "grok_video_v15_lite"], "LTX-2.5 / Wan 2.x (open) | Router (partner)"),
    "Genjutsu": (["hf_mult_motion_control", "hf_mult_replace_object", "hf_mult_motion_control_flash", "hf_mult_replace_object_flash", "ad_multiplier", "ad_multiplier_v2"], "Wan Animate 2"),
}
