"""Higgsfield Apps (higgsfield.ai/apps, Oct 2026): one-click effects grouped by category, rebuilt as OpenSfield apps.

mode "image": a photo app, Nano Banana 2.1 edit by default, Qwen-Image-Edit (open weights) as the alternative.
mode "video": a photo-to-video app, Seedance 2.5 by default, LTX-2.5 (open weights) as the alternative.
mode "tool": the app is an existing OpenSfield tool (optionally with a preset), so no new workflow is needed.
mode "pair": two-photo apps (face, character and outfit swaps) on the compose / try-on tools.
Prompts are our own wording. Skibidi is left out on purpose: it is built on someone else's IP (contest rule: no unlicensed IP).
"""

CATEGORIES = ["Professional", "Enhance & Style", "Face & Identity", "Video Editing", "Ads & Products", "Games & Characters", "Extras", "Trending Templates"]


def img(slug, name, cat, desc, prompt, tag=None, extra="Extra detail (optional)"):
    return dict(slug=slug, name=name, cat=cat, desc=desc, mode="image", prompt=prompt, tag=tag, extra=extra)


def vid(slug, name, cat, desc, prompt, tag=None, subject="Your photo"):
    return dict(slug=slug, name=name, cat=cat, desc=desc, mode="video", prompt=prompt, tag=tag, subject=subject)


def tool(slug, name, cat, desc, feature, tag=None, preset=None):
    return dict(slug=slug, name=name, cat=cat, desc=desc, mode="tool", feature=feature, tag=tag, preset=preset or {})


def pair(slug, name, cat, desc, feature, prompt="", tag=None):
    return dict(slug=slug, name=name, cat=cat, desc=desc, mode="pair", feature=feature, prompt=prompt, tag=tag)


P, E, F, V, A, G, X, T = CATEGORIES
APPS = [
    # ---------------- Professional ----------------
    tool("virality-predictor", "Virality Predictor", P, "Score your video hook before you post", "platform.virality"),
    tool("expand-image", "Expand image", P, "Expand any image beyond its edges", "image.reframe"),
    tool("angles", "Angles 2.0", P, "Any angle view of any image in seconds", "scene3d.angles", tag="PRO"),
    img("shots", "Shots", P, "9 unique shots from one image",
        "Turn this image into a 3x3 contact sheet of nine different film shots of the same scene and subject: wide, medium, close-up, over-the-shoulder, low angle, high angle, profile, detail insert and a reverse shot. Same lighting and style in every panel, thin black gutters."),
    img("zooms", "Zooms", P, "9 zoom levels from one image",
        "Turn this image into a 3x3 grid showing nine zoom levels of the same scene, from an extreme wide establishing shot to an extreme close-up detail, same lighting and style, thin black gutters."),
    img("whats-next", "What's Next?", P, "8 narrative possibilities from one frame",
        "Turn this frame into a 2x4 storyboard of eight different things that could happen next to the same characters in the same place, each panel a distinct story beat, cinematic stills, thin black gutters.", tag="NEW"),
    img("behind-the-scenes", "Behind the Scenes", P, "Turn photos into behind-the-scenes shots",
        "Show this exact scene as a behind-the-scenes photo from a film set: the same subject in the middle, with crew, cameras on dollies, light stands, boom microphones and cables around them, candid documentary style."),
    tool("transitions", "Transitions", P, "Seamless transitions between any two shots", "cinema.first-last-frame", tag="TRENDING"),
    img("color-grading", "Color grading", P, "Professional color grades for any image",
        "Regrade this image with a professional cinematic color grade: rich contrast, teal shadows, warm skin tones, gentle film halation, keep the content exactly the same.", extra="Grade you want (optional, e.g. warm 70s film, cold blue night)"),
    # ---------------- Enhance & Style ----------------
    pair("ai-stylist", "AI Stylist", E, "Your AI fitting room: try anything on", "model.kling-vto", tag="NEW"),
    img("relight", "Relight", E, "Adjust lighting position, color and brightness",
        "Relight this photo with a soft warm key light from the left, a subtle cool rim light from behind and gentle falloff, keep the person and scene exactly the same.", tag="PRO", extra="Lighting you want (optional, e.g. neon pink from the right)"),
    img("skin-enhancer", "Skin Enhancer", E, "Natural, realistic skin textures",
        "Retouch this portrait with natural, realistic skin: keep pores and fine texture, even out blotches and harsh shine, no plastic smoothing, keep identity, makeup and lighting exactly the same.", tag="PRO"),
    pair("outfit-swap", "Outfit Swap", E, "Try on any outfit with one photo", "model.kling-vto"),
    img("style-snap", "Style Snap", E, "Instant style variations of your look",
        "Keep this person's face and body the same and restyle their whole look as a fresh streetwear outfit with coordinated accessories, editorial fashion photo.", extra="Style you want (optional, e.g. 90s grunge, quiet luxury)"),
    img("vending-machine", "Outfit Vending", E, "Your outfit broken down in a vending machine",
        "Show each piece of this person's outfit (top, bottoms, shoes, bag, accessories) displayed as separate products inside a glowing vending machine, each on its own shelf with a price tag, photo-real."),
    img("glitter-sticker", "Glitter Sticker", E, "A sparkling sticker version of you",
        "Turn this person into a die-cut glitter sticker with a thick white border and holographic sparkle, on a plain pastel background, full body, cute and shiny."),
    img("outfit-shot", "Outfit Shot", E, "Outfits as professional fashion shots",
        "Turn this into a professional fashion campaign photo of the same outfit: studio seamless backdrop, editorial pose, soft key light, sharp fabric detail."),
    # ---------------- Face & Identity ----------------
    tool("recast", "Recast", F, "Character swap for any video", "genjutsu.replace-object", tag="PRO"),
    pair("character-swap", "Character Swap 2.0", F, "Swap characters in your image in one click", "soul.cast",
         prompt="Replace the main person in the first image with the person from the second image, keeping the first image's pose, clothes, lighting and background."),
    pair("face-swap", "Face Swap", F, "Instant face swap for photos", "soul.cast",
         prompt="Put the face from the second image onto the person in the first image, keeping the first image's hair, body, clothes, lighting and background. Match skin tone and angle."),
    img("commercial-faces", "Commercial Faces", F, "Professional face transformations for brands",
        "Turn this portrait into a polished commercial beauty shot: clean studio light, flawless but natural skin, confident expression, neutral backdrop, same identity."),
    tool("video-face-swap", "Video Face Swap", F, "Swap faces in any video", "genjutsu.replace-object"),
    img("ai-headshot-generator", "Headshot Generator", F, "Studio-quality professional headshots",
        "Turn this photo into a professional corporate headshot of the same person: shoulders-up, navy blazer, soft studio light, light grey backdrop, friendly confident expression."),
    # ---------------- Video Editing ----------------
    vid("clipcut", "ClipCut", V, "One selfie into an outfit reel",
        "A fast fashion reel of this person: the outfit changes on every beat with quick flash cuts, the person poses and turns to the camera, bright studio, energetic social video."),
    vid("urban-cuts", "Urban Cuts", V, "Beat-synced street outfit videos",
        "A beat-synced street style video of this person walking through city locations, outfit and background switch on each beat with whip-pan cuts, golden hour, handheld energy."),
    tool("sticker-matchcut", "Sticker Match Cut", V, "Any shots into a sparkling sticker match cut", "matchcut.subject-cuts", preset={"mode": "Sticker"}),
    tool("breakdown", "Breakdown", V, "Split any image into its components", "image.decompose"),
    img("japanese-show", "Japanese Show", V, "Your photo as a retro 4-panel TV show",
        "Turn this photo into a 2x2 grid of stills from a retro Japanese variety TV show starring this person: bright studio sets, big colorful on-screen captions, 4:3 CRT look."),
    tool("video-background-remover", "Video Background Remover", V, "Strip the background from any video", "video.bg-remove"),
    # ---------------- Ads & Products ----------------
    tool("link-to-video-ad", "Click to Ad", A, "Product links into UGC and pro video ads", "marketing.click-to-ad", tag="PRO"),
    vid("asmr-add-on", "ASMR Add-On", A, "Your product inside an ASMR video",
        "A close-up ASMR video: hands gently tap, peel and handle this product on a soft surface, macro detail, quiet satisfying motions, shallow depth of field.", subject="Product photo"),
    vid("asmr-classic", "ASMR Classic", A, "A traditional ASMR video",
        "A classic ASMR video with this product: slow brushing and tapping sounds implied by gentle hand movements, warm dim light, extreme macro texture shots.", subject="Product photo"),
    img("poster", "Poster", A, "Your product as a bold poster",
        "Design a bold advertising poster around this product: big graphic shapes, strong color blocking, dramatic product placement, space for a headline at the top."),
    vid("bullet-time-scene", "Bullet Time Scene", A, "Spin around your product in a matching scene",
        "Bullet-time shot: the camera orbits 180 degrees around this product frozen in mid-air while the background changes to a scene that matches it, crisp and dramatic.", subject="Product photo"),
    vid("chameleon", "Chameleon", A, "A chameleon shifts colors to match your product",
        "A chameleon climbs onto this product and slowly shifts its skin color to match the product's colors, macro nature-documentary look.", subject="Product photo"),
    vid("asmr-host", "ASMR Host", A, "Your photo as an immersive ASMR host",
        "This person hosts an ASMR video: whispering close to a studio microphone, soft hand movements, warm dim bedroom light, intimate close framing."),
    img("packshot", "Packshot", A, "A polished closing frame for your product",
        "Create a clean end-frame packshot of this product: centered on a seamless gradient backdrop, soft reflection under it, premium studio light, empty space for a logo."),
    vid("macroshot-scene", "Macro Scene", A, "Product details in an adaptive macro scene",
        "Macro video gliding across the surface details of this product, slow motion, shallow depth of field, a backdrop that matches the product's colors.", subject="Product photo"),
    vid("magic-button", "Magic Button", A, "Your product appears in a magical reveal",
        "A finger presses a glowing magic button and this product appears with sparkles and a burst of light on a whimsical pastel stage.", subject="Product photo"),
    vid("truck-ad", "Truck Ad", A, "Your brand on a moving truck billboard",
        "This image is printed on the side of a box truck driving through a busy city street, tracking shot alongside the truck, realistic daylight.", subject="Ad or product photo"),
    vid("giant-product", "Giant Product", A, "Your product as a giant in the city",
        "This product stands as a giant landmark in a city square, people walking around its base, the camera slowly cranes up, realistic scale.", subject="Product photo"),
    vid("bullet-time-white", "Bullet Time White", A, "Spin around your product on clean white",
        "Bullet-time 360 degree orbit around this product floating on a seamless white background, soft shadows, premium e-commerce look.", subject="Product photo"),
    vid("kick-ad", "Kick Ad", A, "Your product beats the competition",
        "This product knocks plain unbranded rivals off a table in a playful slow-motion kick, then lands center frame as the winner, bright commercial look.", subject="Product photo"),
    vid("billboard", "Billboard Ad", A, "Your photo as a massive billboard takeover",
        "This image is shown on a massive building billboard over a busy city intersection at dusk, people look up, the camera pushes in.", subject="Ad or photo"),
    vid("graffiti-ad", "Graffiti Ad", A, "Your product as vibrant street art",
        "This product appears as a huge vibrant graffiti mural being finished on a brick wall, spray-paint mist, the camera pulls back to reveal the whole piece.", subject="Product photo"),
    vid("bullet-time-splash", "Bullet Time Splash", A, "Your product in a cinematic splash",
        "Bullet-time orbit around this product exploding through a frozen splash of liquid and droplets, high-speed commercial look, dramatic rim light.", subject="Product photo"),
    vid("fridge-ad", "Fridge Ad", A, "Your product inside a glowing fridge",
        "A fridge door opens to reveal this product glowing on the middle shelf, cool light spills out, the camera pushes in, playful commercial.", subject="Product photo"),
    vid("volcano-ad", "Volcano Ad", A, "Your product in front of an erupting volcano",
        "This product stands on dark rock in front of an erupting volcano, lava glow and embers drifting, epic low-angle commercial shot.", subject="Product photo"),
    img("macroshot-product", "Macroshot product", A, "Stunning macro details of your product",
        "An extreme macro photo of this product's most interesting surface detail, razor-thin depth of field, studio light that reveals texture."),
    # ---------------- Games & Characters ----------------
    img("game-dump", "Game Dump", G, "You in 12 iconic video game styles",
        "A 3x4 grid of twelve panels showing this person as a character in twelve different video game art styles: 8-bit, 16-bit pixel, cel-shaded, low-poly, voxel, fighting game, racing game, fantasy RPG, survival horror, cartoon platformer, realistic open world and anime RPG. Same face in every panel."),
    img("nano-strike", "Nano Strike", G, "You as a tactical shooter character",
        "Turn this person into a tactical shooter video game character: tactical gear, game-style render, dramatic map background, game HUD loadout screen look."),
    img("nano-theft", "Nano Theft", G, "You in a realistic open-world game style",
        "Show this person as a character in a realistic open-world crime game: loading-screen illustration style, sunny palm-lined city, bold painted look."),
    img("simlife", "Simlife", G, "You as a life-simulation character",
        "Turn this person into a stylized life-simulation game character standing in a bright cozy game house interior, soft game render, build-mode look."),
    vid("plushies", "Plushies", G, "Any photo into a plushie animation",
        "This person or pet turns into a soft plush toy and wiggles happily on a bed, felt texture, stitched seams, cute stop-motion feel."),
    img("3d-render", "3D Render", G, "Any photo as a stunning 3D render",
        "Turn this into a polished 3D animated film render: stylized proportions, subsurface skin, soft global illumination, same pose and outfit."),
    img("3d-figure", "3D Figure", G, "Your photo as a detailed 3D figure",
        "Turn this person into a detailed hand-painted collectible figurine standing on a round black display base, studio product photo on a plain grey backdrop, painted resin texture, no packaging, no text."),
    img("pixel-game", "Pixel Game", G, "Your photo as retro pixel game graphics",
        "Turn this photo into a retro 16-bit pixel art game screen with this person as the playable character, limited palette, HUD with hearts and score."),
    img("brick-cube", "Brick Cube", G, "Your photo as a brick-built cube toy",
        "Rebuild this person as a figure made of small plastic toy bricks inside a clear display cube, studio product shot."),
    img("sketch-to-real", "Sketch-to-Real", G, "Your sketch into a realistic image",
        "Turn this sketch into a realistic photograph that follows its composition and shapes exactly, natural lighting and real materials.", extra="What the sketch shows (optional)"),
    # ---------------- Extras ----------------
    img("paint-app", "Paint App", X, "Your photo as retro paint-app art",
        "Redraw this photo as if made in a 1990s desktop paint program: chunky mouse-drawn lines, flat bucket fills, a few pixel spray strokes, the paint window toolbar around it."),
    img("signboard", "Signboard", X, "See yourself on a stylish mural",
        "Paint this person as a large stylish mural on a city wall, with a few people walking past for scale, street photo."),
    img("surrounded-by-animals", "Micro-Beasts", X, "Surround yourself with cute animals",
        "Keep this person exactly the same and surround them with lots of tiny cute animals, kittens, bunnies and ducklings, playful and photo-real."),
    img("meme-generator", "AI Meme Generator", X, "Viral memes with AI characters",
        "Turn this image into a meme: exaggerated funny expression, bold white impact-font caption with black outline at the top and bottom.", extra="Caption text"),
    tool("image-background-remover", "Background Remover", X, "Clean cutouts from any photo", "image.bg-remove"),
    # ---------------- Trending Templates ----------------
    vid("yes-kiss", "Yes Kiss", T, "A surreal meme-style kiss moment",
        "A surreal meme-style moment: a cartoonish pair of lips flies in and plants a kiss on this person's cheek, they react with exaggerated surprise."),
    img("latex", "Latex", T, "You in sleek black latex style",
        "Restyle this person's outfit as sleek glossy black latex fashion, editorial studio photo, same face and pose."),
    img("j-magazine", "J-Magazine", T, "Your photo as a Japanese magazine cover",
        "Turn this photo into a Japanese fashion magazine cover with this person as the cover model, vertical Japanese headlines and colorful cover lines."),
    vid("roller-coaster", "Roller Coaster", T, "You on a thrilling roller coaster",
        "This person rides the front seat of a roller coaster, hair blown back, screaming with joy as it drops, camera mounted in front."),
    img("60s-cafe", "60s Cafe", T, "You in a vintage 60s cafe scene",
        "Place this person in a vintage 1960s diner booth with a milkshake, period outfit and hair, faded Kodachrome film look."),
    img("victory-card", "Victory Card", T, "You on a winning poker card",
        "Turn this person into the illustrated portrait on an ornate playing card held up in a winning poker hand, casino table background."),
    vid("sand-worm", "Sand Worm", T, "You in an epic desert creature scene",
        "This person stands on a desert dune as a colossal sand creature bursts from the sand behind them, epic wide shot, swirling sand."),
    img("j-poster", "J-Poster", T, "Your photo as a Japanese-style poster",
        "Turn this photo into a Japanese movie poster design with this person, bold vertical Japanese typography, halftone textures and red accents."),
    img("mascot", "Mascot", T, "You as a sports mascot",
        "Turn this person into a fluffy sports team mascot costume version of themselves cheering in a stadium, same face visible in the costume head opening."),
    vid("storm-creature", "Storm Creature", T, "An epic storm creature scene",
        "Storm clouds swirl into a giant creature above this person, lightning in its eyes, wind and rain whipping, epic low angle."),
    img("burning-sunset", "Burning Sunset", T, "An epic burning-sky sunset portrait",
        "Place this person in front of an epic fiery orange sunset sky with dramatic backlight and lens flare, cinematic portrait."),
    img("this-is-fine", "On Fire", T, "Calm in a room that is on fire",
        "Show this person sitting calmly at a table with a coffee mug, smiling, while the room around them is on fire, flat cartoon comic style, two-panel strip."),
    img("comic-book", "Comic Book", T, "Your photo as comic book art",
        "Redraw this photo as a dynamic comic book panel: bold ink lines, halftone shading, speech bubble, vivid flat colors."),
    vid("cloud-surf", "Cloud Surf", T, "Surf a dreamy pink cloud",
        "This person surfs on a fluffy pink cloud through a pastel sunset sky, hair flowing, dreamy slow motion."),
    vid("mukbang", "Mukbang", T, "Your photo as a viral eating show",
        "This person hosts a mukbang eating show, a big spread of colorful food on the table, ring light, talking to the camera between bites."),
    vid("melting-doodle", "Melting Doodle", T, "Mesmerizing melting doodle art",
        "This photo turns into a hand-drawn doodle that slowly melts and drips like colorful paint, mesmerizing loop."),
    img("giallo-horror", "Giallo Horror", T, "You in a 70s giallo horror still",
        "Turn this photo into a 1970s Italian giallo horror film still with this person: saturated red and green lighting, grainy film, dramatic shadows."),
    img("renaissance", "Renaissance", T, "You as a classical gallery painting",
        "Repaint this photo as an old-master oil painting of the same person: keep their face, hair, pose and clothes, add soft chiaroscuro light, visible brushwork and fine craquelure, and put the canvas in an ornate gold frame on a dark wall."),
    vid("rapgod", "Rap God", T, "Your photo as a rap video clip",
        "This person performs in a rap music video: fisheye lens, low angle, gold chains, friends hyping in the background, quick cuts."),
]

assert len({a["slug"] for a in APPS}) == len(APPS)
