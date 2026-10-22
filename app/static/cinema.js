"use strict";
/* Cinema Studio: its own workspace like Higgsfield's Cinema Studio 4.0. Sidebar (Home, My elements, My favorites, Community,
   Projects) and a composer whose setting cards (References, Film setup, Camera, Color palette, Lighting) write director's
   language into the prompt, then send it to a proven tool (Seedance 2.5 by default). Uses helpers from app.js. */

const CS_FILM = {
  Genre: [["General", ""], ["Epic", "an epic, large-scale film with sweeping scope"], ["Drama", "an intimate character drama"], ["Noir", "a film noir with hard shadows and moral tension"],
    ["Comedy", "a comedy with playful timing and bright framing"], ["Horror", "a horror film with dread and negative space"], ["Action", "an action film with kinetic energy"],
    ["Sci-fi", "a science-fiction film with a designed future world"], ["Romance", "a romance with soft, warm intimacy"], ["Documentary", "a documentary with observational, naturalistic framing"]],
  Era: [["Auto", ""], ["1920s", "1920s period setting, silent-era texture"], ["1960s", "1960s period setting and production design"], ["1970s", "1970s period setting, film grain and earthy tones"],
    ["1980s", "1980s period setting and styling"], ["1990s", "1990s period setting and styling"], ["2000s", "2000s period setting and styling"], ["2020s", "present-day setting"],
    ["Near future", "a near-future setting"]],
  Tempo: [["Auto", ""], ["Calm", "calm, slow pacing with long takes"], ["Dynamic", "dynamic pacing with energetic movement"], ["Chaotic", "chaotic, frantic pacing"], ["Single shot", "one continuous shot with no cuts"]],
};
const CS_CAMERA = {
  Camera: [["Auto", ""], ["Modern digital", "shot on a modern digital cinema camera"], ["35mm film", "shot on 35mm film with natural grain"], ["16mm film", "shot on 16mm film with visible grain"],
    ["8mm film", "shot on 8mm home-movie film"], ["DV camcorder", "shot on a 2000s DV camcorder"], ["IMAX", "shot on large-format IMAX"]],
  Lens: [["Auto", ""], ["Clean sharp", "clean, sharp modern lens"], ["Anamorphic", "anamorphic lens with oval bokeh and horizontal flares"], ["Vintage anamorphic", "vintage anamorphic lens with soft edges and streak flares"],
    ["Warm vintage", "warm vintage lens with gentle halation"], ["Halation vintage", "vintage lens with strong halation around highlights"], ["Wide 24mm", "wide 24mm lens"], ["Telephoto 85mm", "85mm telephoto lens with compressed perspective"]],
  Aperture: [["Auto", ""], ["f/1.4 wide open", "f/1.4, very shallow depth of field"], ["f/2.8", "f/2.8, shallow depth of field"], ["f/4 moderate", "f/4, moderate depth of field"], ["f/11 deep focus", "f/11, deep focus with everything sharp"]],
};
const CS_MOVES = ["Static shot", "Dolly in", "Dolly out", "Pan left", "Pan right", "Tilt up", "Tilt down", "Truck left", "Truck right", "Pedestal up", "Pedestal down",
  "Crane up", "Crane down", "Arc left", "Arc right", "Tracking", "Side tracking", "Handheld", "Drone orbit", "Aerial pullback", "Helicopter shot", "Slow zoom in",
  "Slow zoom out", "Crash zoom", "Dolly zoom", "Whip pan", "Rack focus", "POV", "Snorricam", "Bullet time", "Robot arm", "Slider left", "Slider right"];
const CS_PALETTES = [
  ["Auto", [], ""], ["Teal night", ["#0b1e2d", "#12405a", "#1f7a8c", "#e0a458", "#f2d0a4", "#2d1e2f"], "teal shadows with amber highlights, night grade"],
  ["Warm tungsten", ["#2b1608", "#6b3410", "#b8692a", "#e8a85f", "#f6d7a7", "#fff3df"], "warm tungsten orange grade"],
  ["Bleach bypass", ["#1c1d1f", "#3b3e42", "#6c7176", "#a3a7aa", "#cfd1d1", "#efefec"], "desaturated bleach-bypass grade with crushed blacks"],
  ["Pastel morning", ["#f6e2e6", "#e9c9d6", "#c7d8e8", "#bfe0d6", "#f3e7c3", "#fffaf1"], "soft pastel morning palette"],
  ["Neon noir", ["#0a0612", "#2b0b45", "#7a1fa2", "#ff2e88", "#00e0ff", "#f6f0ff"], "neon magenta and cyan against deep black"],
  ["Desert gold", ["#3a2412", "#7b4a1e", "#c48a3a", "#e8c07a", "#f5e0b0", "#9db4c0"], "sun-bleached desert gold with pale sky"],
  ["Forest mist", ["#0f1c14", "#22382a", "#3f5e47", "#7d9b7f", "#c2d1bf", "#eef2ea"], "misty green forest tones"],
  ["Cold steel", ["#0d141c", "#1e2a38", "#3b4c61", "#6d8099", "#a9b8c8", "#e6edf3"], "cold steel-blue grade"],
  ["Technicolor pop", ["#d7263d", "#f46036", "#f9c80e", "#2e86ab", "#1b998b", "#fdfffc"], "saturated three-strip Technicolor primaries"],
  ["Sepia memory", ["#2e1f14", "#5a3e28", "#8c6a48", "#b8987a", "#dccab0", "#f4ead8"], "faded sepia memory tones"],
  ["Crimson stage", ["#14070a", "#3d0d15", "#7d1424", "#c2243a", "#e8a0a8", "#f7e4e6"], "deep crimson stage reds"],
  ["Mono contrast", ["#000000", "#2a2a2a", "#555555", "#9a9a9a", "#d4d4d4", "#ffffff"], "high-contrast black and white"],
];
const CS_LIGHTS = [["Auto", "", "linear-gradient(135deg,#3a3a40,#1a1a1e)"], ["Natural window", "soft natural window light from one side", "linear-gradient(110deg,#f4efe6 0 30%,#5b5a57 60%,#1e1d1c)"],
  ["Golden hour", "low golden-hour sunlight with long shadows", "linear-gradient(160deg,#ffcf7a,#e0773a 55%,#3a1d10)"], ["Practicals", "lit by practical lamps visible in frame", "radial-gradient(circle at 70% 30%,#ffd28a,#6b3a1a 35%,#120b08 70%)"],
  ["Silhouette", "strong backlight with subjects in silhouette", "radial-gradient(circle at 50% 60%,#ffb04a,#7a3a10 40%,#080606 70%)"], ["Hard noir", "hard noir key light with venetian-blind shadows", "repeating-linear-gradient(170deg,#e6e6e6 0 8px,#141414 8px 20px)"],
  ["Soft key", "soft diffused key light, gentle falloff", "radial-gradient(circle at 35% 35%,#f1ece6,#8d8780 45%,#2a2826)"], ["Overhead fall", "single overhead light falling onto the subject", "radial-gradient(ellipse at 50% 0%,#fff3d6,#5a5248 45%,#0f0e0d 75%)"],
  ["Contre-jour", "contre-jour backlighting with glowing rim light", "radial-gradient(circle at 50% 40%,#fff,#9fc6ff 25%,#1b2433 60%)"], ["Neon spill", "colored neon light spilling across faces", "linear-gradient(120deg,#ff2e88,#3a0d3d 45%,#00d0ff)"],
  ["Candlelight", "warm flickering candlelight", "radial-gradient(circle at 50% 70%,#ffcf6b,#8a3b0a 30%,#0d0604 65%)"], ["Moonlight", "cool blue moonlight", "radial-gradient(circle at 70% 20%,#dbe8ff,#3a5a8c 35%,#070b14 70%)"],
  ["Stage spot", "a single theatrical spotlight in darkness", "radial-gradient(circle at 50% 45%,#fffbe8,#6b6250 22%,#050505 45%)"]];
const CS_ENGINES = {
  video: [["Seedance 2.5", "model.seedance2-5-i2v-1080p", "model.seedance2-5-t2v-1080p"], ["Kling 3.0", "model.kling-v3-video", "model.kling-o3-t2v"],
    ["LTX-2.5 (open)", "cinema.camera-rig", "video.t2v-i2v-open"]],
  image: [["Nano Banana 2.1", "model.nano-banana-2-1-image-edit", "model.nano-banana-2-1-t2i"], ["GPT Image 2", "model.openai-gpt-image-2-image-edit", "model.openai-gpt-image-2-t2i"],
    ["Open weights", "image.edit-open", "soul.t2i"]],
};
const CS_DEFAULT = { mode: "video", engine: 0, Genre: "General", Era: "Auto", Tempo: "Auto", Camera: "Auto", Lens: "Auto", Aperture: "Auto", palette: "Auto", lighting: "Auto",
  prompt: "", chips: {} };
const cs = { ...CS_DEFAULT, refs: [], projects: [] };

function csSave() { store.set("osf.cinema", { ...cs, refs: [], projects: [] }); }
function csLoad() { Object.assign(cs, CS_DEFAULT, store.get("osf.cinema", {}), { refs: cs.refs, projects: cs.projects }); }
const csFeature = () => { const e = CS_ENGINES[cs.mode][cs.engine] || CS_ENGINES[cs.mode][0]; return state.byId[cs.refs.length ? e[1] : e[2]] || state.byId[e[2]]; };
const csSpec = (f, names) => f && f.inputs.find((s) => names.includes(s.name));

/* ---------------- shell ---------------- */
async function renderCinema(page, arg) {
  csLoad();
  try { cs.projects = await api("/api/projects"); } catch { cs.projects = []; }
  const main = $("#main");
  const content = h("div", { class: "cscontent" });
  main.replaceChildren(h("div", { class: "csapp" }, csSidebar(page, arg), content));
  document.title = "Cinema Studio · OpenSfield";
  if (page === "elements") renderAssets(content);
  else if (page === "favorites") csFavorites(content);
  else if (page === "community") renderCommunity(content);
  else csHome(content, page === "p" ? arg : null);
}

function csSidebar(page, arg) {
  const item = (href, ico, label, on) => h("a", { class: "csnav", href, "aria-current": on ? "page" : null }, h("span", { class: "csico" }, ico), label);
  const sw = h("div", { class: "csswitch" },
    h("button", { type: "button", class: "csapp-btn", "aria-haspopup": "true" }, h("span", { class: "csmark" }, "◆"), "Cinema Studio", h("span", { class: "chev" }, "▾")),
    h("div", { class: "csapps" }, ...[["#/", "OpenSfield home"], ["#/w/image/0", "Image"], ["#/w/video/0", "Video"], ["#/w/audio/0", "Audio"], ["#/apps", "All apps"],
      ["#/assets", "Elements"], ["#/blog", "Learn"]].map(([href, l]) => h("a", { href }, l))));
  const newName = h("input", { class: "csnewin", placeholder: "Project name", "aria-label": "New project name", hidden: true,
    onkeydown: async (e) => {
      if (e.key === "Escape") { newName.hidden = true; return; }
      if (e.key !== "Enter" || !newName.value.trim()) return;
      const p = await api("/api/projects", json("POST", { name: newName.value.trim() })).catch(() => null);
      if (p) location.hash = `#/cinema/p/${p.id}`;
    } });
  return h("aside", { class: "cside" }, sw,
    item("#/cinema", "⌂", "Home", !page),
    item("#/cinema/elements", "@", "My elements", page === "elements"),
    item("#/cinema/favorites", "♥", "My favorites", page === "favorites"),
    item("#/cinema/community", "◎", "Community", page === "community"),
    h("div", { class: "cslabel" }, "Projects"),
    ...cs.projects.map((p) => h("a", { class: "csnav proj", href: `#/cinema/p/${p.id}`, "aria-current": page === "p" && arg === p.id ? "page" : null },
      h("span", { class: "csico" }, "▣"), h("span", { class: "grow" }, p.name),
      h("button", { type: "button", class: "csdel", title: "Delete project (its generations stay in History)", "aria-label": `Delete project ${p.name}`,
        onclick: async (e) => { e.preventDefault(); e.stopPropagation(); if (!confirm(`Delete the project "${p.name}"? Its generations stay in History.`)) return;
          await api(`/api/projects/${p.id}`, { method: "DELETE" }).catch(() => {}); location.hash = "#/cinema"; route(); } }, "✕"))),
    h("button", { type: "button", class: "csnav csnew", onclick: () => { newName.hidden = false; newName.focus(); } }, h("span", { class: "csico" }, "+"), "New project"), newName,
    h("span", { class: "grow" }),
    h("a", { class: "cslearn", href: "#/blog/cinema-studio-direct-a-shot" }, h("small", {}, "Learn to make movies"), h("b", {}, "Direct a shot: film setup, camera, palette, light"),
      exampleEl("examples/cinema_camera_rig_dance.mp4", "bg", { autoplay: true }), h("span", { class: "mini" }, "Read the guide")),
    h("a", { class: "csnav", href: "#/generations" }, h("span", { class: "csico" }, "◷"), "All generations"));
}

/* ---------------- home: posters, composer, this project's generations ---------------- */
function csHome(el, projectId) {
  const project = cs.projects.find((p) => p.id === projectId);
  const posters = ["examples/models/seedance2-5-t2v-1080p.mp4", "examples/multishot.mp4", "examples/models/kling-v3-video.mp4"].map((u, i) =>
    h("div", { class: `poster p${i}` }, exampleEl(u, "bg", { autoplay: true })));
  el.replaceChildren(
    h("div", { class: "cshero" }, h("div", { class: "posters" }, ...posters),
      h("h1", { class: "cstitle" }, project ? project.name.toUpperCase() : "BRING YOUR STORIES TO LIFE"),
      project && h("p", { class: "sub center" }, "Everything you generate here is filed under this project.")),
    csComposer(projectId),
    h("div", { class: "csgal" }, galleryHead(project ? project.name : "Your Cinema Studio shots"), h("div", { id: "gallery" })));
  state.gallery = { filter: (j) => j.inputs && j.inputs._studio === "cinema" && (!projectId || j.project === projectId), examples: [],
    empty: "Your shots appear here. Set the cards above, describe the scene and press Generate." };
  renderGallery();
}

function csCard(label, value, onClick, swatch) {
  return h("button", { type: "button", class: "cscard", onclick: onClick },
    h("span", { class: "cssw", style: swatch || "" }), h("span", { class: "cstext" }, h("small", {}, label), h("b", {}, value)));
}

function csComposer(projectId) {
  const err = h("span", { class: "err", role: "alert" });
  const ta = h("textarea", { id: "cs-prompt", rows: 2, placeholder: "Describe your scene - use @ to add characters & locations, # for camera moves",
    oninput: (e) => { cs.prompt = e.target.value; csSave(); } }, cs.prompt);
  attachMentions(ta, (elem) => csAddElement(elem));
  const pal = CS_PALETTES.find((p) => p[0] === cs.palette) || CS_PALETTES[0];
  const light = CS_LIGHTS.find((l) => l[0] === cs.lighting) || CS_LIGHTS[0];
  const filmVal = [cs.Genre !== "General" && cs.Genre, cs.Era !== "Auto" && cs.Era, cs.Tempo !== "Auto" && cs.Tempo].filter(Boolean).join(" · ") || "Auto";
  const camVal = [cs.Camera, cs.Lens, cs.Aperture].filter((v) => v !== "Auto").join(" · ") || "Auto";
  const cards = h("div", { class: "cscards" },
    csCard("References", `${cs.refs.length}/8`, () => csRefsModal(), cs.refs[0] ? `background-image:url(${cs.refs[0].url});background-size:cover` : ""),
    csCard("Film setup", filmVal, () => csFilmModal(), "background:linear-gradient(135deg,#d6c48a,#5a4a22)"),
    csCard("Camera", camVal, () => csCameraModal(ta), "background:radial-gradient(circle,#4f7cff 30%,#14203f 70%)"),
    csCard("Color palette", cs.palette, () => csPaletteModal(), pal[1].length ? `background:linear-gradient(90deg,${pal[1].join(",")})` : "background:linear-gradient(135deg,#c5a535,#5d4d0e)"),
    csCard("Lighting", cs.lighting, () => csLightModal(), `background:${light[2]}`));
  const f = csFeature();
  const chips = csChips(f);
  const engines = CS_ENGINES[cs.mode];
  const engineSel = h("span", { class: "chipctl", title: "Model" }, h("span", { class: "cico" }, "◆"), h("span", { class: "cval" }, `Cinema Studio · ${engines[cs.engine]?.[0] || engines[0][0]}`),
    h("select", { "aria-label": "Model", onchange: (e) => { cs.engine = Number(e.target.value); cs.chips = {}; csSave(); route(); } },
      engines.map(([l], i) => h("option", { value: i, selected: i === cs.engine }, l))));
  const plus = h("input", { type: "file", accept: "image/*", class: "sr", id: "cs-up", onchange: async (e) => {
    const fd = new FormData(); fd.append("file", e.target.files[0]);
    const up = await api("/api/uploads", { method: "POST", body: fd }).catch((x) => { err.textContent = x.message; return null; });
    if (up) { cs.refs.push({ id: up.id, url: URL.createObjectURL(e.target.files[0]), name: e.target.files[0].name }); route(); }
  } });
  const go = h("button", { type: "button", class: "go csgo" }, "Generate", f?.cost ? h("span", { class: "cost" }, `✦ ${f.cost}`) : null);
  const run = async () => {
    err.textContent = "";
    if (!f) { err.textContent = "This model is not available."; return; }
    const text = csBuildPrompt(ta.value);
    if (!ta.value.trim()) { err.textContent = "Describe your scene first."; ta.focus(); return; }
    const inputs = { _studio: "cinema" };
    const pspec = f.inputs.find((s) => s.kind === "text" && s.required) || f.inputs.find((s) => s.kind === "text");
    if (pspec) inputs[pspec.name] = text;
    const ispec = f.inputs.find((s) => s.kind === "image");
    if (ispec && cs.refs[0]) inputs[ispec.name] = cs.refs[0].id;
    for (const [name, v] of Object.entries(cs.chips)) if (f.inputs.some((s) => s.name === name)) inputs[name] = v;
    go.disabled = true;
    try { await api("/api/jobs", json("POST", { feature_id: f.id, inputs, project: projectId || null })); poll(); }
    catch (e) { err.textContent = e.message; }
    go.disabled = false;
  };
  go.addEventListener("click", run);
  state.run = run;
  return h("section", { class: "cscomposer" },
    h("div", { class: "csmode", role: "radiogroup", "aria-label": "Output" }, ...[["image", "▣", "Image"], ["video", "▶", "Video"]].map(([m, ico, l]) =>
      h("button", { type: "button", role: "radio", "aria-checked": String(cs.mode === m), onclick: () => { cs.mode = m; cs.engine = 0; cs.chips = {}; csSave(); route(); } }, h("span", {}, ico), l))),
    h("div", { class: "csbox" }, cards,
      h("div", { class: "csinput" }, ta,
        h("div", { class: "csrow" },
          h("label", { class: "chipctl icon", for: "cs-up", title: "Add a reference image" }, "+"), plus,
          h("button", { type: "button", class: "chipctl icon", title: "Add an element (@)", onclick: () => { ta.value += (ta.value.endsWith(" ") || !ta.value ? "@" : " @"); ta.focus(); ta.dispatchEvent(new Event("input")); } }, "@"),
          h("button", { type: "button", class: "chipctl icon", title: "Add a camera move (#)", onclick: () => csCameraModal(ta, "Movement") }, "#"),
          engineSel, ...chips, h("span", { class: "grow" }), err, go)),
      h("div", { class: "csfine" }, f ? `${f.name} · ${cs.refs.length ? "first reference is the start frame" : "no reference: text only"}${f.track === "partner" ? " · uses Comfy credits" : " · open weights"}` : "")));
}

function csChips(f) {
  if (!f) return [];
  const want = [["resolution", ["resolution"], "◇"], ["ratio", ["ratio", "aspect_ratio", "aspect"], "▭"], ["duration", ["duration"], "◷"]];
  return want.map(([, names, ico]) => {
    const spec = csSpec(f, names);
    if (!spec || (cs.mode === "image" && spec.name === "duration")) return null;
    const opts = spec.kind === "choice" ? spec.options : numberOptions(spec);
    if (!opts || opts.length < 2) return null;
    const cur = cs.chips[spec.name] ?? spec.default;
    const unit = spec.name === "duration" ? "s" : "";
    const shown = h("span", { class: "cval" }, `${String(cur).replace(/ \(.*\)$/, "")}${unit}`);
    return h("span", { class: "chipctl", title: spec.label }, h("span", { class: "cico" }, ico), shown,
      h("select", { "aria-label": spec.label, onchange: (e) => { const v = spec.kind === "number" ? Number(e.target.value) : e.target.value; cs.chips[spec.name] = v; csSave(); shown.textContent = `${String(v).replace(/ \(.*\)$/, "")}${unit}`; } },
        opts.map((o) => h("option", { value: o, selected: String(o) === String(cur) }, `${spec.label}: ${o}${unit}`))));
  }).filter(Boolean);
}

/** The director's choices become plain shot language the model understands. */
function csBuildPrompt(raw) {
  const moves = [...raw.matchAll(/#([A-Za-z][\w -]*?)(?=\s*(#|$|[.,;]))/g)].map((m) => m[1].trim()).filter((m) => CS_MOVES.some((x) => x.toLowerCase() === m.toLowerCase()));
  let text = raw.replace(/#([A-Za-z][\w -]*?)(?=\s*(#|$|[.,;]))/g, (all, name) => (CS_MOVES.some((x) => x.toLowerCase() === name.trim().toLowerCase()) ? "" : all)).replace(/\s+/g, " ").trim();
  text = text.replace(/@([\w-]+)/g, (_, n) => n.replace(/_/g, " "));
  const pick = (table, key) => (table.find(([n]) => n === cs[key]) || [, ""])[1];
  const parts = [text && !/[.!?]$/.test(text) ? `${text}.` : text];
  if (moves.length) parts.push(`Camera movement: ${moves.map((m) => m.toLowerCase()).join(", then ")}.`);
  const film = [pick(CS_FILM.Genre, "Genre"), pick(CS_FILM.Era, "Era"), pick(CS_FILM.Tempo, "Tempo")].filter(Boolean);
  if (film.length) parts.push(`Style: ${film.join("; ")}.`);
  const cam = [pick(CS_CAMERA.Camera, "Camera"), pick(CS_CAMERA.Lens, "Lens"), pick(CS_CAMERA.Aperture, "Aperture")].filter(Boolean);
  if (cam.length) parts.push(`Camera: ${cam.join(", ")}.`);
  const pal = CS_PALETTES.find((p) => p[0] === cs.palette);
  if (pal && pal[2]) parts.push(`Color grade: ${pal[2]}.`);
  const light = CS_LIGHTS.find((l) => l[0] === cs.lighting);
  if (light && light[1]) parts.push(`Lighting: ${light[1]}.`);
  return parts.join(" ");
}

async function csAddElement(elem) {
  if (elem.kind !== "image" || cs.refs.length >= 8 || cs.refs.some((r) => r.element === elem.id)) return;
  const up = await api(`/api/assets/${elem.id}/use`, { method: "POST" }).catch(() => null);
  if (up) { cs.refs.push({ id: up.id, url: elem.url, name: elem.name, element: elem.id }); const card = document.querySelector(".cscard .cstext b"); if (card) card.textContent = `${cs.refs.length}/8`; }
}

/* ---------------- setting modals ---------------- */
function csModal(title, tabs, onReset) {
  document.querySelector(".csmodal")?.remove();
  const body = h("div", { class: "csmbody" });
  const side = h("div", { class: "csmside" });
  const close = () => { wrap.remove(); document.removeEventListener("keydown", onKey); route(); };
  const onKey = (e) => { if (e.key === "Escape") close(); };
  const show = (i) => { side.querySelectorAll("button").forEach((b, j) => b.setAttribute("aria-current", String(i === j))); body.replaceChildren(tabs[i][1]()); };
  tabs.forEach(([label], i) => side.append(h("button", { type: "button", onclick: () => show(i) }, label)));
  const wrap = h("div", { class: "modal csmodal", role: "dialog", "aria-modal": "true", "aria-label": title, onclick: (e) => e.target === wrap && close() },
    h("div", { class: "csmbox" }, h("div", { class: "csmhead" }, h("b", {}, title), h("span", { class: "grow" }),
      onReset && h("button", { type: "button", class: "mini", onclick: () => { onReset(); csSave(); show(0); } }, "Reset all"),
      h("button", { type: "button", class: "adel", "aria-label": "Close", onclick: close }, "✕")),
      h("div", { class: "csmmain" }, tabs.length > 1 ? side : null, body)));
  document.body.append(wrap);
  document.addEventListener("keydown", onKey);
  show(0);
  return { close };
}
function csOptionGrid(key, list, sub, swatch) {
  const grid = h("div", { class: "csopts" });
  const draw = () => grid.replaceChildren(...list.map(([n, phrase, look]) => h("button", { type: "button", class: "csopt", "aria-pressed": String(cs[key] === n), title: phrase || "Let the model decide",
    onclick: () => { cs[key] = n; csSave(); draw(); } }, h("span", { class: "csoptart", style: swatch ? swatch(n, look) : `--h:${hash(n) % 360}` }), h("b", {}, n), phrase && h("small", {}, phrase))));
  draw();
  return h("div", {}, h("div", { class: "csmsub" }, sub), grid);
}
function csFilmModal() {
  csModal("Film setup", [["Genre", () => csOptionGrid("Genre", CS_FILM.Genre, "Story conventions the model should follow")],
    ["Era", () => csOptionGrid("Era", CS_FILM.Era, "The period the film belongs to")], ["Tempo", () => csOptionGrid("Tempo", CS_FILM.Tempo, "Pacing of the shot")]],
  () => Object.assign(cs, { Genre: "General", Era: "Auto", Tempo: "Auto" }));
}
function csCameraModal(ta, startTab) {
  const setup = () => h("div", { class: "cscols" }, ...Object.entries(CS_CAMERA).map(([key, list]) => {
    const col = h("div", { class: "cscol" }, h("div", { class: "mhead2" }, key.toUpperCase()));
    const draw = () => col.replaceChildren(col.firstChild, ...list.map(([n, phrase]) => h("button", { type: "button", class: "cswheel", "aria-pressed": String(cs[key] === n), title: phrase || "Auto",
      onclick: () => { cs[key] = n; csSave(); draw(); } }, n)));
    draw();
    return col;
  }));
  const moves = () => h("div", {}, h("div", { class: "csmsub" }, "Direct a camera move. Adds #Move to the prompt; several per shot, order matters."),
    h("div", { class: "csmoves" }, ...CS_MOVES.map((m) => h("button", { type: "button", class: "csmove", onclick: (e) => {
      if (ta) { ta.value = `${ta.value}${ta.value && !ta.value.endsWith(" ") ? " " : ""}#${m} `; cs.prompt = ta.value; csSave(); }
      e.currentTarget.classList.add("added");
    } }, h("span", { class: `mvart mv-${m.toLowerCase().replace(/[^a-z]+/g, "-")}` }, h("i")), h("b", {}, m), h("small", {}, "Put on prompt")))));
  const tabs = [["Setup", setup], ["Movement", moves]];
  csModal("Camera", startTab === "Movement" ? [tabs[1], tabs[0]] : tabs, () => Object.assign(cs, { Camera: "Auto", Lens: "Auto", Aperture: "Auto" }));
}
function csPaletteModal() {
  csModal("Color palette", [["Palette", () => csOptionGrid("palette", CS_PALETTES.map(([n, cols, phrase]) => [n, phrase, cols]), "Palette the color grade should follow",
    (n, cols) => (cols && cols.length ? `background:linear-gradient(90deg,${cols.map((c, i) => `${c} ${(i * 100) / cols.length}% ${((i + 1) * 100) / cols.length}%`).join(",")})` : "background:linear-gradient(135deg,#3a3a40,#1a1a1e)"))]],
  () => { cs.palette = "Auto"; });
}
function csLightModal() {
  csModal("Lighting", [["Lighting", () => csOptionGrid("lighting", CS_LIGHTS, "Pick a lighting scheme", (n, look) => `background:${look}`)]], () => { cs.lighting = "Auto"; });
}
async function csRefsModal() {
  const els = await loadElements();
  const body = () => {
    const box = h("div", {});
    const draw = () => box.replaceChildren(
      h("div", { class: "csmsub" }, "Characters, locations and props for this shot (up to 8). The first one is the start frame or edit source; @mention the rest in your prompt."),
      h("div", { class: "csrefs" }, ...cs.refs.map((r, i) => h("div", { class: "csref" }, h("img", { src: r.url, alt: "" }), h("small", {}, i === 0 ? `${r.name} · start` : r.name),
        h("button", { type: "button", class: "adel", "aria-label": `Remove ${r.name}`, onclick: () => { cs.refs.splice(i, 1); draw(); } }, "✕")))),
      h("div", { class: "mhead2" }, "MY ELEMENTS"),
      els.length ? h("div", { class: "csopts" }, ...els.filter((x) => x.kind === "image").map((x) => h("button", { type: "button", class: "csopt", "aria-pressed": String(cs.refs.some((r) => r.element === x.id)),
        onclick: async () => { await csAddElement(x); draw(); } }, h("span", { class: "csoptart", style: `background:url(${x.url}) center/cover` }), h("b", {}, `@${x.name}`), h("small", {}, x.type))))
        : h("p", { class: "empty" }, "No elements yet. Use + to upload a reference, or create elements in My elements."));
    draw();
    return box;
  };
  csModal("References", [["References", body]], () => { cs.refs = []; });
}

/* ---------------- favorites ---------------- */
function csFavorites(el) {
  el.replaceChildren(marker("My favorites"), h("p", { class: "sub" }, "Generations you hearted, from every tool."), galleryHead("Favorites"), h("div", { id: "gallery" }));
  state.gallery = { filter: (j) => j.fav, empty: "Press ♡ on any generation to keep it here." };
  renderGallery();
}
