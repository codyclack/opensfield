"use strict";
/* OpenSfield UI: Higgsfield's layout (top nav, sidebar, model picker, option chips, generations feed) over Comfy workflows. */
const $ = (s) => document.querySelector(s);
const NS = "http://www.w3.org/2000/svg";
const state = { cfg: null, feats: [], byId: {}, jobs: [], query: "", filter: "all", view: "studio", timer: null, links: [], obs: null,
  pick: {}, prefill: null, carry: null, genFilter: "all", genSize: "m", gallery: null, run: null };

const STUDIO_COLOR = {
  "Genjutsu": "#ff7a59", "Cinema Studio": "#b39ddb", "Reshoot": "#64b5f6", "Viral Hub": "#ff9cf9", "Soul": "#ffa931",
  "Image models": "#81c784", "Image tools": "#4dd0e1", "Video tools": "#7986cb", "Video models": "#aed581",
  "Audio": "#f06292", "Marketing": "#ffd54f", "Match Cut + Tracelab": "#80cbc4", "Platform": "#9e9e9e",
};
const STUDIO_ICON = { "Genjutsu": "GJ", "Cinema Studio": "CS", "Reshoot": "RS", "Viral Hub": "VH", "Soul": "SO", "Image models": "IM", "Image tools": "IT",
  "Video tools": "VT", "Video models": "VM", "Audio": "AU", "Marketing": "MK", "Match Cut + Tracelab": "MC", "Platform": "PF" };
const KIND = { image: "#64b5f6", video: "#ff9cf9", audio: "#ffa931", text: "#77dd99", widget: "#a79db3", "3d": "#81c784" };
const WORKSPACES = {
  image: { title: "Image", kind: "image", layout: "bar", tabs: [["Create Image", "Text to image"], ["Edit Image", "Image edit"], ["Upscale", "Image upscale"], ["Image to 3D", "Image to 3D"]] },
  video: { title: "Video", kind: "video", layout: "panel", tabs: [["Create Video", "Image to video"], ["Text to Video", "Text to video"], ["References", "Reference to video"],
    ["First & Last", "First / last frame"], ["Motion Control", "Motion control"], ["Edit Video", "Video edit"]] },
  audio: { title: "Audio", kind: "audio", layout: "bar", tabs: [["Speech", "Text to speech"], ["Music", "Music"]] },
};
// Top nav like higgsfield.ai: text items, a badge on hot ones, hover menus listing tools and models. "lo" items hide on narrow screens.
const TOPNAV = [["Explore", "#/"], ["Image", "#/w/image/0", null, "image"], ["Video", "#/w/video/0", null, "video"], ["Audio", "#/w/audio/0", null, "audio"],
  ["Edit", "#/w/image/1"], ["Genjutsu", "#/s/Genjutsu", "Top", "studio"], ["Cinema Studio", "#/cinema", "4.0"],
  ["Soul", "#/s/Soul", null, "studio", "lo"], ["Viral", "#/s/Viral Hub", null, "studio", "lo"], ["Marketing", "#/s/Marketing", "New", "studio", "lo"],
  ["Apps", "#/apps", null, "apps"], ["Elements", "#/assets"], ["Learn", "#/blog", "New", null, "lo"]];

const sockKind = (s) => (["image", "video", "audio"].includes(s.kind) ? s.kind : s.kind === "text" ? "text" : "widget");
const studioColor = (s) => STUDIO_COLOR[s] || "#9e9e9e";
const hash = (s) => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
const isVideo = (url) => /\.(mp4|webm|mov)(\?|#|$)/i.test(url);
const isImage = (url) => /\.(png|jpe?g|webp|gif|svg)(\?|#|$)/i.test(url);
const isAudio = (url) => /\.(mp3|wav|flac|ogg)(\?|#|$)/i.test(url);
const store = { get: (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } }, set: (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } } };

function h(tag, props = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : document.createTextNode(kid));
  return el;
}
const svgEl = (tag, attrs = {}) => { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); return e; };
const badge = (text, cls = "") => h("span", { class: `badge ${cls}` }, text);
const sock = (kind, cls = "") => h("i", { class: `sock ${cls}`, style: `--k:${KIND[kind] || KIND.widget}` });
const marker = (text) => h("h1", { class: "marker" }, h("span", {}, text));
const api = async (path, opts) => {
  const r = await fetch(path, opts);
  if (r.status === 204) return null;
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.detail || `${r.status} ${r.statusText}`);
  return body;
};
const json = (method, body) => ({ method, headers: { "content-type": "application/json" }, body: JSON.stringify(body) });

/* ---------------- registry helpers ---------------- */
const statusLabel = (f) => (f.status === "tested" ? "Ready" : f.status === "built" ? "Untested" : "Soon");
const isOpen = (f) => f.track !== "partner";
const sameNames = (f) => f.group && members(f.group).every((m) => m.name === f.name);
const modelName = (f) => (sameNames(f) ? `${f.engine || (isOpen(f) ? "Open weights" : "Partner")}${isOpen(f) ? " (open)" : ""}` : short(f));
const short = (f) => f.name.replace(/\s*·\s*(Text|Image|Reference|Video|First).*/i, "").replace(/^Seedance(\d)/, "Seedance $1");
function members(group) {
  const list = state.feats.filter((x) => x.group === group);
  const rank = (x) => (x.default ? 0 : /seedance/i.test(x.id) ? 1 : x.status === "tested" ? 2 : 3);
  return list.sort((a, b) => rank(a) - rank(b) || a.name.localeCompare(b.name));
}
function preferred(group) {
  const m = members(group);
  return state.byId[state.pick[group]] || m[0];
}
function studios() {
  const seen = new Map();
  for (const f of state.feats) seen.set(f.studio, (seen.get(f.studio) || 0) + 1);
  const known = state.cfg.studios.filter((s) => seen.has(s));
  return [...known, ...[...seen.keys()].filter((s) => !known.includes(s))];
}
/** One card per group inside a list (Higgsfield shows a task once and puts models in its picker). */
function collapse(list) {
  const out = [], seen = new Set();
  for (const f of list) {
    if (!f.group) { out.push({ f, n: 1 }); continue; }
    if (seen.has(f.group)) continue;
    seen.add(f.group);
    const inList = list.filter((x) => x.group === f.group);
    const best = inList.find((x) => x.default) || inList.find((x) => /seedance/i.test(x.id)) || inList.find((x) => x.status === "tested") || inList[0];
    out.push({ f: best, n: members(f.group).length });
  }
  return out;
}

/* ---------------- media ---------------- */
function exampleEl(url, cls, opts = {}) {
  const src = url.startsWith("/") ? url : "/" + url;
  if (isAudio(src)) return h("audio", { src, controls: true, preload: "none" });
  if (/\.(glb|gltf)$/i.test(src)) return h("a", { class: "st", href: src, download: "" }, `Download 3D model (${src.split("/").pop()})`);
  if (/\.html$/i.test(src)) return h("div", { class: `htmlprev ${cls || ""}` }, h("iframe", { src, loading: "lazy", title: "Website preview", sandbox: "allow-same-origin" }),
    h("a", { class: "mini", href: src, target: "_blank", rel: "noopener" }, "Open site ↗"));
  if (/\.txt$/i.test(src)) return h("a", { class: "st", href: src, target: "_blank", rel: "noopener" }, `Open ${src.split("/").pop()}`);
  if (!isVideo(src)) return h("img", { class: cls, src, alt: opts.alt || "", loading: "lazy" });
  return h("video", { class: cls, src: src + "#t=1.5", muted: true, loop: true, playsinline: true, preload: "metadata",
    controls: opts.controls, autoplay: opts.autoplay && !reduceMotion, "aria-hidden": opts.controls ? null : "true" });
}
function hoverPlay(el) {
  const v = el.querySelector("video");
  if (v && !reduceMotion) { el.addEventListener("mouseenter", () => v.play().catch(() => {})); el.addEventListener("mouseleave", () => v.pause()); }
  return el;
}

/* ---------------- chrome: top nav, sidebar ---------------- */
function routeKey() { return location.hash || "#/"; }
function menuLink(href, label, sub, tag) {
  return h("a", { href, class: "mlink" }, h("span", { class: "mlt" }, label, tag && h("span", { class: `tag t-${tag.toLowerCase()}` }, tag)), sub && h("small", {}, sub));
}
function modelLinks(group, n = 8) {
  const seen = new Set();
  return members(group).filter((m) => { const k = modelName(m); if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, n)
    .map((m) => menuLink(`#/f/${m.id}`, modelName(m), m.engine && m.engine !== modelName(m) ? m.engine : (isOpen(m) ? "open weights" : m.output_kind), m.default ? "Top" : null));
}
function menuFor(kind, label) {
  const col = (title, links) => links.length > 0 && h("div", { class: "mcol" }, h("div", { class: "mhead2" }, title), ...links);
  const tool = (id, label2, sub) => state.byId[id] && menuLink(`#/f/${id}`, label2 || state.byId[id].name, sub);
  if (kind === "image") return [col("Create", WORKSPACES.image.tabs.map(([t, g], i) => members(g).length && menuLink(`#/w/image/${i}`, t, g)).filter(Boolean)
    .concat([tool("soul.location", "Soul Location"), tool("marketing.product-photoshoot", "Product photoshoot"), tool("image.bg-remove", "Background remover")].filter(Boolean))),
    col("Image models", modelLinks("Text to image")), col("Edit models", modelLinks("Image edit", 6))];
  if (kind === "video") return [col("Create", WORKSPACES.video.tabs.map(([t, g], i) => members(g).length && menuLink(`#/w/video/${i}`, t, g)).filter(Boolean)
    .concat([tool("cinema.extend", "Extend video"), tool("video.lipsync", "Lip sync"), tool("cinema.draw-to-video", "Draw to video"), tool("video.upscale", "Upscale video")].filter(Boolean))),
    col("Video models", modelLinks("Image to video", 10)), col("Text to video", modelLinks("Text to video", 6))];
  if (kind === "audio") return [col("Create", WORKSPACES.audio.tabs.map(([t, g], i) => members(g).length && menuLink(`#/w/audio/${i}`, t, g)).filter(Boolean)
    .concat([tool("audio.sfx", "Sound effects"), tool("audio.voice-change", "Voice change"), tool("audio.voice-clone", "Voice clone"), tool("audio.dubbing", "Dubbing"), tool("audio.captions", "Captions")].filter(Boolean))),
    col("Voice models", modelLinks("Text to speech", 6))];
  if (kind === "studio") {
    const list = collapse(state.feats.filter((f) => f.studio === label));
    return [col(label, list.slice(0, 9).map(({ f, n }) => menuLink(`#/f/${f.id}`, n > 1 && f.group ? f.group : f.name, n > 1 ? `${n} models` : statusLabel(f)))),
      list.length > 9 && col("More", list.slice(9, 18).map(({ f, n }) => menuLink(`#/f/${f.id}`, n > 1 && f.group ? f.group : f.name, statusLabel(f))))];
  }
  if (kind === "apps") {
    const all = studios().map((s) => menuLink(`#/s/${encodeURIComponent(s)}`, s, `${collapse(state.feats.filter((f) => f.studio === s)).length} tools`));
    return [col("Studios", all.slice(0, 7)), col(" ", all.slice(7)), col("Library", [menuLink("#/cinema", "Cinema Studio", "Direct a shot"), menuLink("#/apps", "All apps"), menuLink("#/assets", "My elements"), menuLink("#/generations", "History"), menuLink("#/community", "Community"), menuLink("#/blog", "Learn", "Guides and tutorials"), menuLink("#/usage", "Credits & usage")])];
  }
  return [];
}
function renderChrome() {
  const cur = routeKey();
  const key = (href) => decodeURIComponent(href);
  const isCur = (href) => {
    const c = key(cur), hrf = key(href);
    if (hrf === "#/") return c === "#/" || c === "#";
    if (hrf === "#/w/image/1") return c === hrf;
    if (hrf.startsWith("#/w/")) return c.startsWith(hrf.replace(/\/\d+$/, "/")) && !(hrf.startsWith("#/w/image") && c === "#/w/image/1");
    if (hrf.startsWith("#/s/")) { const f = /^#\/f\/(.+)$/.exec(c); return c === hrf || (f && state.byId[f[1]] && `#/s/${state.byId[f[1]].studio}` === hrf); }
    return c === hrf;
  };
  $("#topnav").replaceChildren(...TOPNAV.map(([t, href, tag, menu, lo]) => {
    const link = h("a", { href, class: "navlink", "aria-current": isCur(href) ? "page" : null, "aria-haspopup": menu ? "true" : null }, t, tag && h("span", { class: `tag t-${tag.toLowerCase()}` }, tag));
    const cols = menu ? menuFor(menu, menu === "studio" ? href.slice(4).replace(/%20/g, " ") : t).filter(Boolean) : [];
    return h("div", { class: `navitem${lo ? " lo" : ""}` }, link, cols.length > 0 && h("div", { class: "menu", role: "menu" }, ...cols));
  }));
}

/* ---------------- explore / apps / studio grids ---------------- */
function card(f, n = 1) {
  const cover = (f.examples || []).find((u) => isVideo(u) || isImage(u));
  const title = n > 2 && f.group ? f.group : f.group && n === 2 ? f.group : f.name;
  const sub = n > 1 ? `${n} models · ${short(f)}` : f.engine || f.higgsfield;
  return hoverPlay(h("a", { class: `card${cover ? "" : " plain"}`, href: `#/f/${f.id}`, style: `--h:${hash(f.id) % 360}` },
    cover && exampleEl(cover, "bg"),
    h("span", { class: `pill ${f.status === "tested" ? "" : "dim"}` }, statusLabel(f)),
    h("span", { class: "ckind" }, f.output_kind.toUpperCase() + (n > 1 ? "" : isOpen(f) ? " · OPEN" : " · API")),
    h("span", { class: "ctext" }, h("b", {}, title), h("small", {}, sub))));
}
const FILTERS = [["all", "All"], ["ready", "Ready"], ["image", "Image"], ["video", "Video"], ["audio", "Audio"], ["3d", "3D"]];
const matches = (f) => state.filter === "all" || (state.filter === "ready" ? f.status === "tested" : f.output_kind === state.filter);
function filterBar() {
  return h("div", { class: "filters", role: "group", "aria-label": "Filter tools" },
    FILTERS.map(([k, l]) => h("button", { type: "button", class: "fpill", "aria-pressed": String(state.filter === k), onclick: () => { state.filter = k; route(); } }, l)));
}
const exOf = (id) => (state.byId[id]?.examples || []).find((u) => isVideo(u) || isImage(u));
// higgsfield.ai home: three big feature banners, then a promo block next to six feature tiles
const BANNERS = [["model.seedance2-5-i2v-1080p", "SEEDANCE 2.5", "The most advanced video model, with the open LTX-2.5 one click away"],
  ["genjutsu.motion-control", "GENJUTSU", "Motion control, character replace and restyle from one driving video", "#/s/Genjutsu"],
  ["model.kling-v3-video", "KLING 3.0", "Multi-shot video with consistent subjects"]];
const TILES = [["model.seedance2-5-i2v-1080p", "Seedance 2.5", "The most advanced video model", "Top", "▶"],
  ["model.nano-banana-2-1-image-edit", "Nano Banana 2.1", "Edit any image with words", null, "✎"],
  ["marketing.ai-influencer-seedance", "AI Influencer", "Build your next hype machine", "New", "☺"],
  ["viral.effects-seedance", "Viral effects", "Clones, Vanish, Giant and more on Seedance", null, "✦"],
  ["cinema.director", "AI Director", "A short idea becomes a directed Seedance shot", "New", "🎬"],
  ["#/assets", "Assets & Elements", "Characters, props and locations you reuse with @", null, "◈"]];
function explore() {
  const ready = state.feats.filter((f) => f.status === "tested").length;
  const banners = h("section", { class: "banners" }, BANNERS.filter(([id]) => state.byId[id]).map(([id, t, sub, href]) => hoverPlay(h("a", { class: "banner", href: href || `#/f/${id}` },
    h("span", { class: "bmedia" }, exOf(id) && exampleEl(exOf(id), "bg", { autoplay: true })), h("b", {}, t), h("small", {}, sub)))));
  const tiles = TILES.filter(([id]) => id.startsWith("#") || state.byId[id]).map(([id, t, sub, tag, ico]) => h("a", { class: "ftile", href: id.startsWith("#") ? id : `#/f/${id}` },
    h("span", { class: "fico" }, ico), h("span", { class: "ftext" }, h("b", {}, t, tag && h("span", { class: `tag t-${tag.toLowerCase()}` }, tag)), h("small", {}, sub))));
  const promoArt = exOf("marketing.click-to-ad") || exOf("cinema.camera-rig");
  const promo = h("div", { class: "promo" }, promoArt && exampleEl(promoArt, "bg", { autoplay: true }),
    h("div", { class: "ptext2" }, h("h2", {}, "Every Higgsfield tool,", h("br"), h("span", {}, "on ComfyUI")),
      h("ul", {}, h("li", {}, "Seedance 2.5, Kling, Nano Banana, GPT Image"), h("li", {}, "Open-weight LTX, Wan and Qwen workflows"), h("li", {}, `${ready} tools run end to end`)),
      h("a", { class: "go", href: "#/w/video/0" }, "Start creating")));
  return [banners, h("section", { class: "promogrid" }, promo, h("div", { class: "ftiles" }, tiles))];
}
function topModels() {
  const ids = ["model.seedance2-5-i2v-1080p", "model.seedance2-5-t2v-1080p", "model.kling-v3-video", "model.minimax-h3-max-i2v", "model.wan2-6-i2v",
    "model.nano-banana-2-1-t2i", "model.openai-gpt-image-2-t2i", "model.bfl-flux3-t2i", "model.kling-o3-t2v", "model.seedance2-0-r2v"];
  const list = ids.map((i) => state.byId[i]).filter(Boolean);
  return list.length > 0 && h("section", { class: "row" }, h("div", { class: "rowhead" }, h("h3", {}, "Top models")),
    h("div", { class: "strip" }, list.map((f) => card(f))));
}
function renderGrid(mode, studio) {
  const q = state.query.toLowerCase();
  let body;
  if (q) {
    const list = state.feats.filter((f) => `${f.name} ${f.higgsfield} ${f.studio} ${f.id} ${f.group || ""}`.toLowerCase().includes(q)).filter(matches);
    body = [marker(`Search: ${state.query}`), filterBar(), list.length ? h("div", { class: "cards" }, list.map((f) => card(f))) : h("p", { class: "empty" }, "No tools match.")];
  } else if (studio) {
    const list = collapse(state.feats.filter((f) => f.studio === studio).filter(matches));
    body = [marker(studio), filterBar(), list.length ? h("div", { class: "cards" }, list.map(({ f, n }) => card(f, n))) : h("p", { class: "empty" }, "Nothing here for this filter.")];
  } else {
    const rows = studios().map((s) => {
      const list = collapse(state.feats.filter((f) => f.studio === s).filter(matches));
      return list.length > 0 && h("section", { class: "row" },
        h("div", { class: "rowhead" }, h("h3", {}, s), h("a", { class: "more", href: `#/s/${encodeURIComponent(s)}` }, `See all ${list.length} →`)),
        h("div", { class: "strip" }, list.map(({ f, n }) => card(f, n))));
    });
    body = mode === "apps" ? [marker("Apps"), filterBar(), ...rows] : [...explore(), topModels(), filterBar(), ...rows];
  }
  $("#main").replaceChildren(...body.filter(Boolean), siteFooter());
}

/* ---------------- composer controls ---------------- */
const ratioOf = (o) => { const m = /^(\d+):(\d+)/.exec(String(o)); return m ? [Number(m[1]), Number(m[2])] : null; };
function initial(f, spec) {
  if (state.prefill && state.prefill.feature_id === f.id && state.prefill.inputs[spec.name] != null) return state.prefill.inputs[spec.name];
  if (spec.kind === "text" && spec.name === "prompt" && state.carry) return state.carry;
  return spec.default;
}

async function upload(file, spec, vals, ui) {
  ui.label.textContent = "uploading...";
  try {
    const fd = new FormData(); fd.append("file", file);
    const up = await api("/api/uploads", { method: "POST", body: fd });
    vals[spec.name] = up.id; ui.label.textContent = file.name;
    if (spec.kind === "image") { ui.img.src = URL.createObjectURL(file); ui.img.hidden = false; }
  } catch (e) { delete vals[spec.name]; ui.label.textContent = `upload failed: ${e.message}`; }
}
function dropzone(zone, spec, vals, ui) {
  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("over"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("over"));
  zone.addEventListener("drop", (e) => { e.preventDefault(); zone.classList.remove("over"); if (e.dataTransfer.files[0]) upload(e.dataTransfer.files[0], spec, vals, ui); });
}
function uploadTile(f, spec, vals, compact = false) {
  const id = `f-${spec.name}`;
  const img = h("img", { alt: "", hidden: true });
  const cap = h("span", { class: "cap" }, compact ? "" : spec.kind === "image" ? "Add image" : spec.kind === "video" ? "Add video" : "Add audio");
  const ui = { img, label: cap, spec };
  const pre = initial(f, spec);
  if (pre && spec.kind !== "text") { vals[spec.name] = pre; if (spec.kind === "image") { img.src = `/outputs/uploads/${pre}`; img.hidden = false; } else cap.textContent = "reused input"; }
  const input = h("input", { class: "sr", id, type: "file", accept: { image: "image/*", video: "video/*", audio: "audio/*" }[spec.kind],
    onchange: (e) => e.target.files[0] && upload(e.target.files[0], spec, vals, ui) });
  const zone = h("label", { class: `utile${compact ? " small" : ""}`, for: id, title: spec.label }, img,
    h("span", { class: "plus", "aria-hidden": "true" }, spec.kind === "image" ? "+" : spec.kind === "video" ? "▶" : "♪"), cap, input);
  dropzone(zone, spec, vals, ui);
  state.mediaUIs.push(ui);
  if (compact) return zone;
  return h("div", { class: "ufield" }, zone, h("div", { class: "flabel" }, spec.label, spec.required && h("b", {}, " *")),
    h("button", { class: "libbtn", type: "button", onclick: () => pickAsset(spec, vals, ui) }, "From assets"));
}

function field(spec, body, hint) {
  return h("div", { class: "field" }, h("div", { class: "flabel" }, spec.label, spec.required && h("b", {}, " *")), body, hint && h("div", { class: "fhint" }, hint));
}
function presetCards(spec, vals) {
  const group = h("div", { class: "opts", role: "radiogroup", "aria-label": spec.label });
  const set = (o) => { vals[spec.name] = o; group.querySelectorAll("button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.v === String(o)))); };
  for (const o of spec.options) group.append(h("button", { type: "button", role: "radio", "data-v": o, "aria-checked": "false", title: spec.presets?.[o] || o, onclick: () => set(o) }, o));
  set(vals[spec.name]);
  return group;
}
function numberOptions(spec) {
  const step = spec.step || 1, n = Math.round((spec.max - spec.min) / step);
  if (!Number.isFinite(n) || n > 40 || n < 1) return null;
  return Array.from({ length: n + 1 }, (_, i) => +(spec.min + i * step).toFixed(3));
}
const CHIP_ICON = { duration: "◷", ratio: "▭", aspect_ratio: "▭", aspect: "▭", resolution: "◇", quality: "♡", size: "▭" };
function chip(spec, vals) {
  const opts = spec.kind === "choice" ? spec.options : numberOptions(spec);
  const unit = /duration/.test(spec.name) ? "s" : "";
  const label = (o) => `${String(o).replace(/ \(.*\)$/, "")}${unit}`;
  const ico = CHIP_ICON[spec.name] || (ratioOf(spec.options?.[0]) ? "▭" : "•");
  if (!opts) {
    return h("label", { class: "chipctl", title: spec.label }, h("span", { class: "cico" }, ico), h("span", { class: "clab" }, spec.label),
      h("input", { type: "number", value: vals[spec.name], min: spec.min, max: spec.max, step: spec.step || 1, "aria-label": spec.label,
        oninput: (e) => (vals[spec.name] = Number(e.target.value)) }));
  }
  const shown = h("span", { class: "cval" }, label(vals[spec.name]));
  const sel = h("select", { "aria-label": spec.label, title: spec.label, onchange: (e) => {
    vals[spec.name] = spec.kind === "number" ? Number(e.target.value) : e.target.value; shown.textContent = label(e.target.value);
  } }, opts.map((o) => h("option", { value: o, selected: String(o) === String(vals[spec.name]) }, `${spec.label}: ${label(o)}`)));
  return h("span", { class: "chipctl", title: spec.label }, h("span", { class: "cico" }, ico), shown, sel);
}

function elementsButton(f, vals, ta) {
  return h("button", { type: "button", class: "mini", title: "Insert an element (or type @ in the prompt)", onclick: () => pickAsset(
    f.inputs.find((s) => s.kind === "image") || { kind: "image", name: "_element", label: "Element" }, vals,
    state.mediaUIs.find((u) => u.spec.kind === "image") || { img: h("img"), label: h("span"), spec: {} }, (a) => {
      ta.value = `${ta.value}${ta.value && !ta.value.endsWith(" ") ? " " : ""}@${a.name.replace(/\s+/g, "_")} `;
      ta.dispatchEvent(new Event("input"));
    }) }, "@ Elements");
}

function buildControls(f, vals, layout) {
  state.mediaUIs = [];
  const media = f.inputs.filter((s) => ["image", "video", "audio"].includes(s.kind));
  const texts = f.inputs.filter((s) => s.kind === "text");
  const presets = f.inputs.filter((s) => s.kind === "choice" && s.presets);
  const options = f.inputs.filter((s) => (s.kind === "choice" && !s.presets && s.options.length > 1) || s.kind === "number");
  const seed = f.inputs.find((s) => s.kind === "seed");
  for (const s of [...presets, ...options]) vals[s.name] = initial(f, s) ?? s.default ?? 0;
  if (seed) vals[seed.name] = 0;
  const textEls = texts.map((s) => {
    const v = initial(f, s) || "";
    if (v) vals[s.name] = v;
    const ta = h("textarea", { id: `f-${s.name}`, "aria-label": s.label, rows: layout === "bar" ? 2 : 4,
      placeholder: s.required ? (layout === "bar" ? "Describe the scene you imagine" : "Describe what you want...") : (/optional/i.test(s.label) ? s.label : `${s.label} (optional)`),
      oninput: (e) => (vals[s.name] = e.target.value) }, v);
    attachMentions(ta, (el) => useElement(f, vals, el));
    return { s, ta };
  });
  state.carry = null;
  return { media, presets, options, seed, textEls };
}

/* ---------------- model picker (popover) ---------------- */
function modelButton(f, onPick) {
  if (!f.group || members(f.group).length < 2) return null;
  const btn = h("button", { type: "button", class: "modelbtn", "aria-haspopup": "listbox" },
    h("span", { class: "mico", style: `--h:${hash(f.id) % 360}` }, modelName(f).slice(0, 2).toUpperCase()),
    h("span", { class: "mtext" }, h("small", {}, "Model"), h("b", {}, modelName(f))), h("span", { class: "chev" }, "›"));
  btn.addEventListener("click", (e) => { e.stopPropagation(); openPicker(btn, f, onPick); });
  return btn;
}
function openPicker(anchor, f, onPick) {
  document.querySelector(".picker")?.remove();
  const list = h("div", { class: "plist", role: "listbox" });
  const search = h("input", { type: "search", placeholder: "Search...", "aria-label": "Search models" });
  const draw = () => {
    const q = search.value.toLowerCase();
    const ms = members(f.group).filter((m) => !q || m.name.toLowerCase().includes(q));
    list.replaceChildren(h("div", { class: "phead" }, `✦ ${f.group}`), ...ms.map((m) => h("button", { type: "button", role: "option", "aria-selected": String(m.id === f.id), class: "prow",
      onclick: () => { pop.remove(); onPick(m); } },
      h("span", { class: "mico", style: `--h:${hash(m.id) % 360}` }, modelName(m).slice(0, 2).toUpperCase()),
      h("span", { class: "ptext" }, h("b", {}, modelName(m), m.default && h("span", { class: "tag t-top" }, "TOP"), isOpen(m) && h("span", { class: "tag t-open" }, "OPEN")),
        h("small", {}, [m.engine || (isOpen(m) ? "open weights" : "partner API"), m.cost ? `✦ ${m.cost}` : null, m.status === "tested" ? null : "untested"].filter(Boolean).join("  ·  "))),
      m.id === f.id && h("span", { class: "check" }, "✓"))));
  };
  search.addEventListener("input", draw);
  const pop = h("div", { class: "picker" }, search, list);
  draw();
  document.body.append(pop);
  const r = anchor.getBoundingClientRect();
  const top = Math.min(r.top, window.innerHeight - 440);
  Object.assign(pop.style, { left: `${Math.min(r.right + 8, window.innerWidth - 380)}px`, top: `${Math.max(64, top)}px` });
  if (r.right + 380 > window.innerWidth) Object.assign(pop.style, { left: `${Math.max(8, r.left)}px`, top: `${Math.max(64, r.top - 440)}px` });
  search.focus();
  const close = (e) => { if (!pop.contains(e.target)) { pop.remove(); document.removeEventListener("mousedown", close); } };
  setTimeout(() => document.addEventListener("mousedown", close), 0);
  pop.addEventListener("keydown", (e) => { if (e.key === "Escape") { pop.remove(); anchor.focus(); } });
}
function carryPrompt() { const t = $("#f-prompt"); state.carry = t && t.value ? t.value : null; }

/* ---------------- generate ---------------- */
function generateButton(f, vals, err) {
  const go = h("button", { class: "go wide", type: "button" }, "Generate", f.cost ? h("span", { class: "cost" }, `✦ ${f.cost}`) : null);
  const run = async () => {
    err.textContent = ""; go.disabled = true;
    try {
      await api("/api/jobs", json("POST", { feature_id: f.id, inputs: vals }));
      state.prefill = null;
      poll();
    } catch (e) { err.textContent = e.message; }
    go.disabled = false;
  };
  go.addEventListener("click", run);
  state.run = run;
  return go;
}
const fineprint = (f) => (!f.runnable && state.cfg.mode === "comfy" ? "No workflow built yet for this tool." : f.local ? "Runs on this computer's CPU."
  : isOpen(f) ? "Open weights on Comfy (GPU time only). Ctrl+Enter to run." : `Partner model via Comfy Cloud${f.cost ? `, about ${f.cost} credits a run` : ""}. Ctrl+Enter to run.`);

/* ---------------- panel composer (Video, every tool page) ---------------- */
function panelComposer(f, vals, onPick, tabs) {
  const c = buildControls(f, vals, "panel");
  const err = h("span", { class: "err", role: "alert" });
  const cover = (f.examples || []).find((u) => isVideo(u) || isImage(u));
  return h("aside", { class: "panel" },
    tabs,
    h("div", { class: "pcard", style: `--h:${hash(f.id) % 360}` }, cover && exampleEl(cover, "bg", { autoplay: true }),
      h("span", { class: "pctext" }, h("b", {}, (f.group || f.name).toUpperCase()), h("small", {}, modelName(f)))),
    modelButton(f, onPick),
    c.media.length > 0 && h("div", { class: "uploads" }, c.media.map((s) => uploadTile(f, s, vals))),
    ...c.presets.map((s) => field(s, presetCards(s, vals), "Hover a preset to read its prompt.")),
    ...c.textEls.map(({ s, ta }) => h("div", { class: "field prompt" }, h("div", { class: "flabel" }, s.name === "prompt" && s.required ? "Prompt" : s.label, s.required && h("b", {}, " *")), ta,
      h("div", { class: "prow2" }, elementsButton(f, vals, ta)))),
    c.options.length > 0 && h("div", { class: "chiprow" }, c.options.map((s) => chip(s, vals))),
    c.seed && h("details", { class: "adv" }, h("summary", {}, "Advanced"),
      field(c.seed, h("input", { type: "number", min: 0, value: 0, "aria-label": c.seed.label, oninput: (e) => (vals[c.seed.name] = Number(e.target.value)) }), "0 picks a random seed each run.")),
    h("div", { class: "gen" }, err, generateButton(f, vals, err), h("div", { class: "fine" }, fineprint(f))));
}

/* ---------------- bottom prompt bar (Image, Audio) ---------------- */
function barComposer(f, vals, onPick) {
  const c = buildControls(f, vals, "bar");
  const err = h("span", { class: "err", role: "alert" });
  const main = c.textEls[0];
  return h("div", { class: "pbar" },
    h("div", { class: "pbrow" },
      c.media.map((s) => uploadTile(f, s, vals, true)),
      main ? main.ta : h("div", { class: "fine" }, "Add the input above, then Generate."),
      ...c.textEls.slice(1).map(({ ta }) => ta)),
    h("div", { class: "pbrow2" },
      main && elementsButton(f, vals, main.ta),
      modelButton(f, onPick),
      ...c.presets.map((s) => chip(s, vals)),
      ...c.options.map((s) => chip(s, vals)),
      h("span", { class: "grow" }), err, generateButton(f, vals, err)));
}

/* ---------------- generations gallery ---------------- */
function genCard(j) {
  const o = j.outputs.find((x) => !x.mock && x.kind !== "3d") || j.outputs[0];
  const running = j.status === "queued" || j.status === "running";
  const prompt = j.inputs.prompt || j.inputs.text || "";
  const media = running ? h("div", { class: "gwait" }, h("div", { class: "spin" }), h("small", {}, j.status === "queued" ? "Queued" : `Generating ${Math.round(j.progress * 100)}%`))
    : j.status === "error" ? h("div", { class: "gwait err" }, h("small", {}, j.error || "failed"))
      : o ? (o.kind === "audio" ? h("div", { class: "gaudio" }, "♪", h("audio", { src: o.url, controls: true })) : exampleEl(o.url, "gmedia", { controls: o.kind === "video" }))
        : h("div", { class: "gwait" }, h("small", {}, "no output"));
  const act = (label, title, fn) => h("button", { type: "button", class: "gact", title, "aria-label": title, onclick: (e) => { e.preventDefault(); e.stopPropagation(); fn(e.currentTarget); } }, label);
  return h("figure", { class: `gcard ${j.kind || ""}` }, media,
    h("figcaption", {},
      h("span", { class: "gtitle" }, j.feature_name), prompt && h("span", { class: "gprompt" }, prompt),
      h("span", { class: "gacts" },
        o && !running && h("a", { class: "gact", href: o.url, download: o.name, title: "Download", "aria-label": "Download" }, "↓"),
        !running && act(j.fav ? "♥" : "♡", j.fav ? "Remove from favorites" : "Add to favorites", async () => {
          const r = await api(`/api/jobs/${j.id}`, json("PATCH", { fav: !j.fav })).catch(() => null);
          if (r) { Object.assign(j, r); renderGallery(); }
        }),
        o && !running && !o.mock && act("★", "Save as element", (b) => saveToAssets(o, b)),
        act("↺", "Reuse these settings", () => { state.prefill = { feature_id: j.feature_id, inputs: j.inputs }; location.hash = `#/f/${j.feature_id}`; }),
        !running && act("✕", "Remove from history", async () => { await api(`/api/jobs/${j.id}`, { method: "DELETE" }).catch(() => {}); state.jobs = state.jobs.filter((x) => x.id !== j.id); renderGallery(); }))));
}
/** state.gallery = {filter(job) -> bool, examples: [urls], title} set by the current page; re-rendered on every poll. */
function renderGallery() {
  const box = $("#gallery");
  if (!box || !state.gallery) return;
  const g = state.gallery;
  const mine = state.jobs.filter(g.filter);
  const ex = g.examples || [];
  box.className = `gallery size-${state.genSize}`;
  const howto = !mine.length && g.howto ? [h("div", { class: "howto" },
    h("h2", {}, g.howto.title), h("p", {}, g.howto.sub),
    h("div", { class: "steps" }, g.howto.steps.map(([t, sub, url]) => h("div", { class: "step" }, h("div", { class: "smedia" }, url && exampleEl(url, "bg", { autoplay: true })),
      h("b", {}, t), h("small", {}, sub)))))] : [];
  box.replaceChildren(
    ...howto,
    ...(mine.length ? mine.map(genCard) : []),
    ...(!mine.length && ex.length ? [h("h4", {}, g.exTitle || "Example renders (real runs through this app)"),
      ...ex.map((u) => h("figure", { class: "gcard ex" }, exampleEl(u, "gmedia", { controls: true })))] : []),
    ...(!mine.length && !ex.length ? [h("div", { class: "gempty" }, h("b", {}, "Nothing here yet"), h("small", {}, g.empty || "Your generations appear here."))] : []));
}
function galleryHead(title, withFilter) {
  const sizes = h("div", { class: "seg", role: "group", "aria-label": "Thumbnail size" },
    [["s", "S"], ["m", "M"], ["l", "L"]].map(([k, l]) => h("button", { type: "button", "aria-pressed": String(state.genSize === k), onclick: (e) => {
      state.genSize = k; store.set("osf.genSize", k); e.currentTarget.parentElement.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b === e.currentTarget))); renderGallery();
    } }, l)));
  return h("div", { class: "ghead" }, h("span", { class: "gtab" }, "◷ ", title), withFilter, h("span", { class: "grow" }), sizes);
}

/* ---------------- pages ---------------- */
function renderTool(f) {
  if (f.page) { location.replace(f.page); return; }  // app pages (credits & usage) live at their own route
  const vals = {};
  const onPick = (m) => { carryPrompt(); location.hash = `#/f/${m.id}`; };
  const head = h("div", { class: "fhead" },
    h("a", { class: "back", href: `#/s/${encodeURIComponent(f.studio)}` }, `← ${f.studio}`),
    h("div", { class: "seg", role: "group", "aria-label": "View" },
      ["studio", "graph"].map((v) => h("button", { type: "button", "aria-pressed": String(state.view === v), onclick: () => { state.view = v; route(); } }, v === "studio" ? "Studio" : "Node graph"))));
  const sub = h("div", { class: "sub" }, f.engine && badge(f.engine, "A"), badge(statusLabel(f)), badge(isOpen(f) ? "open weights" : "partner", isOpen(f) ? "B" : "partner"),
    f.cost && badge(`✦ ${f.cost} credits`), h("span", {}, f.higgsfield));
  if (state.obs) { state.obs.disconnect(); state.obs = null; }
  state.gallery = { filter: (j) => j.feature_id === f.id || (f.group && state.byId[j.feature_id]?.group === f.group), examples: f.examples,
    empty: "Run this tool to see results here." };
  if (state.view === "graph") {
    const err = h("span", { class: "err", role: "alert" });
    const graph = buildGraph(f, vals);
    $("#main").replaceChildren(head, marker(f.name), sub, graph,
      h("div", { class: "runbar" }, h("div", { class: "sum" }, `${f.inputs.length} input${f.inputs.length === 1 ? "" : "s"} -> ${f.output_kind}`), err, h("kbd", {}, "Ctrl+Enter"), generateButton(f, vals, err)));
    state.obs = new ResizeObserver(() => requestAnimationFrame(drawLinks));
    state.obs.observe(graph); graph.querySelectorAll(".node").forEach((n) => state.obs.observe(n));
    drawLinks(); renderPreviewNode();
    return;
  }
  state.links = [];
  $("#main").replaceChildren(head, marker(f.name), sub,
    h("div", { class: "create" }, panelComposer(f, vals, onPick, null),
      h("section", { class: "results", "aria-label": "Generations" }, galleryHead("History"), h("div", { id: "gallery" }))));
  renderGallery();
}

function renderWorkspace(key, tabIdx) {
  const ws = WORKSPACES[key];
  const tabsAvail = ws.tabs.filter(([, g]) => members(g).length);
  const [, group] = tabsAvail[Math.min(tabIdx, tabsAvail.length - 1)] || tabsAvail[0];
  const realIdx = ws.tabs.findIndex(([, g]) => g === group);
  const f = preferred(group);
  const vals = {};
  const onPick = (m) => { carryPrompt(); state.pick[group] = m.id; store.set("osf.pick", state.pick); route(); };
  const tabs = h("div", { class: "wtabs", role: "tablist" }, tabsAvail.map(([t, g]) => h("a", { role: "tab", href: `#/w/${key}/${ws.tabs.findIndex(([, gg]) => gg === g)}`,
    "aria-selected": String(g === group) }, t)));
  const HOWTO = {
    video: { title: "MAKE VIDEOS IN ONE CLICK", sub: "Pick a model, add a start frame or just a prompt, then Generate. Seedance 2.5 is the default; open LTX-2.5 is in the model list.",
      steps: [["ADD IMAGE", "Upload an image, or pick one from Assets", "examples/char_a.png"], ["CHOOSE PRESET", "Use a Viral, UGC or product preset, or write your own prompt", "examples/effect_clones.mp4"],
        ["GET VIDEO", "Your clip lands in History, ready to download or reuse", "examples/models/kling-v3-video.mp4"]] },
    image: { title: "START CREATING", sub: "Describe the scene you imagine, pick a model from the bar and Generate.",
      steps: [["DESCRIBE", "Write the scene, or @ an asset from your library", "examples/models/openai-gpt-image-2-t2i.png"], ["PICK A MODEL", "GPT Image 2, Nano Banana, FLUX 3, Seedream, Ideogram...", "examples/models/bfl-flux3-t2i.png"],
        ["GET IMAGES", "Results land in History: download, save to Assets, or reuse", "examples/models/nano-banana-2-1-t2i.png"]] },
  };
  state.gallery = { howto: HOWTO[ws.kind], filter: (j) => (j.kind || state.byId[j.feature_id]?.output_kind) === ws.kind, examples: f.examples,
    exTitle: `Made with ${short(f)} (real runs through this app)`, empty: `Your ${ws.kind} generations appear here.` };
  if (ws.layout === "panel") {
    $("#main").replaceChildren(h("div", { class: "create ws" }, panelComposer(f, vals, onPick, tabs),
      h("section", { class: "results", "aria-label": "Generations" }, galleryHead("History"), h("div", { id: "gallery" }))));
  } else {
    $("#main").replaceChildren(h("div", { class: "wsbar" }, h("div", { class: "wstop" }, tabs, h("span", { class: "grow" })),
      galleryHead("History"), h("div", { id: "gallery" }), barComposer(f, vals, onPick)));
  }
  document.title = `${ws.tabs[realIdx][0]} · OpenSfield`;
  renderGallery();
}

function renderGenerations() {
  const kinds = [["all", "All"], ["image", "Images"], ["video", "Videos"], ["audio", "Audio"]];
  const filter = h("div", { class: "filters inline" }, kinds.map(([k, l]) => h("button", { type: "button", class: "fpill", "aria-pressed": String(state.genFilter === k),
    onclick: () => { state.genFilter = k; renderGenerations(); } }, l)));
  state.gallery = { filter: (j) => state.genFilter === "all" || (j.kind || state.byId[j.feature_id]?.output_kind) === state.genFilter,
    empty: "Everything you generate is kept here, newest first, across restarts." };
  $("#main").replaceChildren(marker("Generations"), h("p", { class: "sub" }, `${state.jobs.length} in history. Download, save to Assets, reuse the settings or remove them.`),
    galleryHead("All generations", filter), h("div", { id: "gallery" }));
  renderGallery();
}

/* ---------------- assets ---------------- */
async function saveToAssets(o, btn) {
  btn.disabled = true;
  try {
    await api("/api/assets/save", json("POST", { url: o.url, name: o.name.replace(/\.[a-z0-9]+$/i, "").slice(0, 40) }));
    btn.textContent = "✓"; btn.title = "Saved to Assets";
  } catch (e) { btn.disabled = false; btn.title = `Could not save: ${e.message}`; }
}
function assetThumb(a) {
  if (a.kind === "video") return h("video", { src: a.url + "#t=0.5", muted: true, preload: "metadata", playsinline: true });
  if (a.kind === "audio") return h("div", { class: "aud" }, "♪", h("audio", { src: a.url, controls: true, preload: "none" }));
  return h("img", { src: a.url, alt: a.name, loading: "lazy" });
}
/* ---------------- My elements (Higgsfield's elements: named references you @mention) ---------------- */
const ELEMENT_TABS = [["All", "All"], ["Character", "Characters"], ["Location", "Locations"], ["Prop", "Props"], ["Style", "Styles"], ["Product", "Products"], ["Other", "Other"]];
async function renderAssets(target) {
  const main = target || $("#main");
  main.replaceChildren(h("div", { class: "elhead" }, h("div", {}, marker("My elements"),
    h("p", { class: "sub" }, "Characters, locations and props you @mention in any prompt. Add several reference images to keep them consistent.")),
    h("label", { class: "go", for: "asset-up" }, "+ New element")));
  let data;
  try { data = await api("/api/assets"); } catch (e) { main.append(h("p", { class: "err" }, e.message)); return; }
  state.elements = data.items;
  let filter = state.assetFilter || "All";
  const grid = h("div", { class: "elgrid" });
  const tabs = h("div", { class: "wtabs eltabs", role: "tablist" });
  const file = h("input", { type: "file", multiple: true, accept: "image/*,video/*,audio/*", class: "sr", id: "asset-up",
    onchange: async (e) => {
      for (const fl of e.target.files) {
        const fd = new FormData(); fd.append("file", fl); fd.append("type", filter === "All" ? "Character" : filter); fd.append("name", fl.name.replace(/\.[a-z0-9]+$/i, "").slice(0, 30));
        try { await api("/api/assets", { method: "POST", body: fd }); } catch (err) { alert(`${fl.name}: ${err.message}`); }
      }
      renderAssets(target);
    } });
  const patch = (el, body) => api(`/api/assets/${el.id}`, json("PATCH", body)).catch(() => {});
  const draw = () => {
    tabs.replaceChildren(...ELEMENT_TABS.map(([k, l]) => h("button", { type: "button", role: "tab", class: "tabbtn", "aria-selected": String(filter === k),
      onclick: () => { filter = k; state.assetFilter = k; draw(); } }, l, " ", h("small", {}, String(k === "All" ? data.items.length : data.items.filter((x) => x.type === k).length)))));
    const items = data.items.filter((x) => filter === "All" || x.type === filter);
    grid.replaceChildren(...(items.length ? items.map((el) => {
      const add = h("input", { type: "file", accept: "image/*", class: "sr", id: `add-${el.id}`, onchange: async (e) => {
        const fd = new FormData(); fd.append("file", e.target.files[0]);
        try { await api(`/api/assets/${el.id}/images`, { method: "POST", body: fd }); renderAssets(target); } catch (err) { alert(err.message); }
      } });
      return h("div", { class: "elcard" },
        h("div", { class: "elcover" }, assetThumb(el), h("span", { class: "eltype" }, el.type), h("span", { class: "elat" }, `@${el.name.replace(/\s+/g, "_")}`)),
        h("div", { class: "elstrip" }, (el.images || []).map((im) => h("img", { src: im.url, alt: "" })),
          el.kind === "image" && h("label", { class: "eladd", for: `add-${el.id}`, title: "Add another reference image" }, "+"), add),
        h("div", { class: "ameta" },
          h("input", { class: "aname", value: el.name, "aria-label": "Name", onchange: (e) => patch(el, { name: e.target.value }) }),
          h("button", { class: "adel", type: "button", title: "Delete", "aria-label": `Delete ${el.name}`, onclick: async () => {
            if (!confirm(`Delete the element "${el.name}"?`)) return;
            await api(`/api/assets/${el.id}`, { method: "DELETE" }).catch(() => {}); renderAssets(target);
          } }, "✕"),
          h("select", { "aria-label": "Type", onchange: (e) => patch(el, { type: e.target.value }) }, data.types.map((t) => h("option", { value: t, selected: t === el.type }, t)))));
    }) : [h("div", { class: "gempty" }, h("b", {}, "No elements yet"), h("small", {}, "Upload a character or location, or press ★ on any generation."))]));
  };
  main.append(file, tabs, grid);
  draw();
}

/* @ mentions: type @ in any prompt box to insert an element and use its image */
async function loadElements() {
  if (!state.elements) { try { state.elements = (await api("/api/assets")).items; } catch { state.elements = []; } }
  return state.elements;
}
function attachMentions(ta, onPick) {
  let pop = null;
  const close = () => { pop?.remove(); pop = null; };
  ta.addEventListener("blur", () => setTimeout(close, 150));
  ta.addEventListener("keydown", (e) => { if (pop && e.key === "Escape") { e.stopPropagation(); close(); } });
  ta.addEventListener("input", async () => {
    const m = /(^|\s)@([\w-]*)$/.exec(ta.value.slice(0, ta.selectionStart));
    if (!m) { close(); return; }
    const q = m[2].toLowerCase();
    const els = (await loadElements()).filter((el) => el.name.toLowerCase().replace(/\s+/g, "_").includes(q)).slice(0, 8);
    close();
    if (!els.length) return;
    pop = h("div", { class: "mention", role: "listbox" }, h("div", { class: "phead" }, "Elements"), ...els.map((el) => h("button", { type: "button", role: "option", class: "prow",
      onmousedown: (e) => {
        e.preventDefault();
        const caret = ta.selectionStart;
        const before = ta.value.slice(0, caret).replace(/@[\w-]*$/, `@${el.name.replace(/\s+/g, "_")} `);
        ta.value = before + ta.value.slice(caret);
        ta.dispatchEvent(new Event("input")); close(); ta.focus();
        if (onPick) onPick(el);
      } }, h("img", { class: "mthumb", src: el.url, alt: "" }), h("span", { class: "ptext" }, h("b", {}, `@${el.name}`), h("small", {}, el.type)))));
    document.body.append(pop);
    const r = ta.getBoundingClientRect();
    Object.assign(pop.style, { left: `${r.left}px`, top: `${Math.min(r.bottom + 4, window.innerHeight - 320)}px` });
  });
}
async function useElement(f, vals, el) {
  const spec = f.inputs.find((s) => s.kind === "image" && !vals[s.name]) || f.inputs.find((s) => s.kind === "image");
  if (!spec || el.kind !== "image") return;
  try {
    const up = await api(`/api/assets/${el.id}/use`, { method: "POST" });
    vals[spec.name] = up.id;
    const ui = (state.mediaUIs || []).find((u) => u.spec === spec);
    if (ui) { ui.img.src = el.url; ui.img.hidden = false; ui.label.textContent = el.name; }
  } catch { /* the mention text still helps the prompt */ }
}
async function pickAsset(spec, vals, ui, onChosen) {
  let data;
  try { data = await api("/api/assets"); } catch (e) { alert(e.message); return; }
  const items = data.items.filter((a) => a.kind === spec.kind);
  const close = () => { overlay.remove(); document.removeEventListener("keydown", onKey); };
  const onKey = (e) => { if (e.key === "Escape") close(); };
  const overlay = h("div", { class: "modal", role: "dialog", "aria-modal": "true", "aria-label": "Choose an asset", onclick: (e) => e.target === overlay && close() },
    h("div", { class: "mbox" },
      h("div", { class: "mhead" }, h("b", {}, onChosen ? "Elements" : `Choose ${spec.kind === "image" ? "an image" : spec.kind === "video" ? "a video" : "an audio clip"}`),
        h("button", { type: "button", class: "adel", "aria-label": "Close", onclick: close }, "✕")),
      items.length ? h("div", { class: "cards assets" }, items.map((a) => h("button", { type: "button", class: "acard pick", onclick: async () => {
        try {
          if (spec.name && spec.name !== "_element") {
            const up = await api(`/api/assets/${a.id}/use`, { method: "POST" });
            vals[spec.name] = up.id; ui.label.textContent = a.name;
            if (spec.kind === "image") { ui.img.src = a.url; ui.img.hidden = false; }
          }
          if (onChosen) onChosen(a);
          close();
        } catch (e) { alert(e.message); }
      } }, h("div", { class: "athumb" }, assetThumb(a)), h("div", { class: "ameta" }, h("span", { class: "aname" }, a.name), h("small", {}, a.type)))))
        : h("p", { class: "empty" }, `No ${spec.kind} assets yet. Add some in Assets, or press ★ on a generation.`)));
  document.body.append(overlay);
  document.addEventListener("keydown", onKey);
}

/* ---------------- node-graph view (ComfyUI style) ---------------- */
function node({ title, kind, color, req, body, out = false, inn = false, cls = "" }) {
  return h("div", { class: `node ${cls}` },
    h("div", { class: "ntitle", style: `--c:${color || KIND[kind]}` }, h("i", { class: "dot" }), h("span", {}, title), req && h("span", { class: "req" }, "*"),
      kind && h("span", { class: "ntype" }, kind === "widget" ? "SETTINGS" : kind.toUpperCase())),
    out && sock(kind, "out"), inn && sock(kind, "in"),
    h("div", { class: "nbody" }, body));
}
function mediaBody(spec, vals) {
  const id = `f-${spec.name}`;
  const img = h("img", { alt: "", hidden: true }), label = h("span", {}, `Drop or click: ${spec.kind}`);
  const ui = { img, label };
  const input = h("input", { class: "sr", id, type: "file", accept: { image: "image/*", video: "video/*", audio: "audio/*" }[spec.kind],
    onchange: (e) => e.target.files[0] && upload(e.target.files[0], spec, vals, ui) });
  const zone = h("label", { class: "drop", for: id }, img, label, input);
  dropzone(zone, spec, vals, ui);
  return zone;
}
function widgetRow(spec, vals) {
  const id = `f-${spec.name}`;
  vals[spec.name] = spec.default ?? 0;
  const ctl = spec.kind === "choice"
    ? h("select", { id, onchange: (e) => (vals[spec.name] = e.target.value) }, spec.options.map((o) => h("option", { value: o, selected: o === spec.default }, o)))
    : h("input", { id, type: "number", value: vals[spec.name], min: spec.min, max: spec.max, step: spec.step || 1, oninput: (e) => (vals[spec.name] = Number(e.target.value)) });
  return h("div", { class: "widget" }, h("label", { for: id }, spec.label), ctl);
}
function buildGraph(f, vals) {
  const media = f.inputs.filter((s) => ["image", "video", "audio"].includes(s.kind));
  const texts = f.inputs.filter((s) => s.kind === "text");
  const widgets = f.inputs.filter((s) => ["choice", "number", "seed"].includes(s.kind));
  const ins = [
    ...media.map((s) => ({ label: s.label, kind: s.kind, el: node({ title: s.label, kind: s.kind, req: s.required, out: true, body: mediaBody(s, vals) }) })),
    ...texts.map((s) => ({ label: s.label, kind: "text", el: node({ title: s.label, kind: "text", req: s.required, out: true,
      body: h("textarea", { id: `f-${s.name}`, "aria-label": s.label, placeholder: s.label, oninput: (e) => (vals[s.name] = e.target.value) }) }) })),
  ];
  if (widgets.length) ins.push({ label: "Settings", kind: "widget", el: node({ title: "Settings", kind: "widget", out: true, body: widgets.map((s) => widgetRow(s, vals)) }) });
  const slotEls = ins.map((n) => h("div", { class: "slot in" }, sock(n.kind), n.label));
  const outSock = sock(f.output_kind), prevSock = sock(f.output_kind, "in");
  const fnode = node({ title: f.name, color: studioColor(f.studio), cls: "fnode", body: [
    h("div", { class: "hf" }, f.higgsfield),
    slotEls.length ? h("div", {}, slotEls) : h("div", { class: "note" }, "No inputs"),
    h("div", { class: "chips", title: "Template" }, h("span", {}, f.engine || f.studio)),
    f.note && h("p", { class: "note" }, f.note),
    h("div", { class: "slot out" }, f.output_kind.toUpperCase(), outSock)] });
  const onode = h("div", { class: "node onode" }, h("div", { class: "ntitle", style: `--c:${KIND[f.output_kind]}` }, h("i", { class: "dot" }), "Preview", h("span", { class: "ntype" }, f.output_kind.toUpperCase())),
    prevSock, h("div", { class: "nbody" }, h("div", { id: "gallery", class: "preview" })));
  const svg = svgEl("svg", { class: "links", "aria-hidden": "true" });
  const graph = h("div", { class: "graph" }, svg, h("div", { class: "col" }, ins.map((n) => n.el)), fnode, onode);
  state.links = [
    ...ins.map((n, i) => ({ from: n.el.querySelector(":scope > .sock.out"), to: slotEls[i].querySelector(".sock"), color: KIND[n.kind] })),
    { from: outSock, to: prevSock, color: KIND[f.output_kind] },
  ];
  state.svg = svg;
  return graph;
}
function renderPreviewNode() { renderGallery(); }
function drawLinks() {
  const svg = state.svg, g = svg && svg.parentElement;
  if (!g || !g.isConnected || getComputedStyle(svg).display === "none") return;
  const r = g.getBoundingClientRect();
  svg.setAttribute("viewBox", `0 0 ${r.width} ${r.height}`);
  svg.replaceChildren(...state.links.flatMap((l) => {
    if (!l.from || !l.to) return [];
    const a = l.from.getBoundingClientRect(), b = l.to.getBoundingClientRect();
    const x1 = a.left + a.width / 2 - r.left, y1 = a.top + a.height / 2 - r.top, x2 = b.left + b.width / 2 - r.left, y2 = b.top + b.height / 2 - r.top;
    const dx = Math.max(40, Math.abs(x2 - x1) * 0.5), d = `M${x1},${y1} C${x1 + dx},${y1} ${x2 - dx},${y2} ${x2},${y2}`;
    return [svgEl("path", { d, fill: "none", stroke: "rgba(0,0,0,.45)", "stroke-width": 6, "stroke-linecap": "round" }),
            svgEl("path", { d, fill: "none", stroke: l.color, "stroke-width": 3, "stroke-linecap": "round" })];
  }));
}

/* ---------------- polling + routing ---------------- */
async function poll() {
  clearTimeout(state.timer);
  try { state.jobs = await api("/api/jobs"); } catch { /* keep the last list */ }
  const active = state.jobs.filter((j) => j.status === "queued" || j.status === "running").length;
  const q = $("#qcount"); q.textContent = active; q.hidden = !active;
  renderGallery();
  if (active) state.timer = setTimeout(poll, 1200);
}

function route() {
  const raw = decodeURIComponent(routeKey().slice(1));
  const legacy = /^([sfp])=(.+)$/.exec(raw);  // old deep links: #s=Studio, #f=id, #p=assets
  if (legacy) { location.replace(legacy[1] === "p" ? "#/assets" : `#/${legacy[1]}/${legacy[2]}`); return; }
  const parts = raw.replace(/^\//, "").split("/");
  document.body.classList.toggle("cinema-mode", parts[0] === "cinema");
  renderChrome();
  document.querySelector(".picker")?.remove();
  state.gallery = null; state.run = null;
  if (state.obs && parts[0] !== "f") { state.obs.disconnect(); state.obs = null; }
  if (state.query) { renderGrid("search"); return; }
  document.title = "OpenSfield";
  const [p, a, b] = parts;
  if (p === "f" && state.byId[a]) { document.title = `${state.byId[a].name} · OpenSfield`; renderTool(state.byId[a]); }
  else if (p === "w" && WORKSPACES[a]) renderWorkspace(a, Number(b) || 0);
  else if (p === "s" && a) renderGrid("studio", a);
  else if (p === "apps") renderGrid("apps");
  else if (p === "assets") renderAssets();
  else if (p === "cinema") renderCinema(a, b);
  else if (p === "blog") renderBlog(a);
  else if (p === "community") renderCommunity();
  else if (p === "usage") renderUsage();
  else if (p === "generations") renderGenerations();
  else renderGrid("explore");
  window.scrollTo(0, 0);
}

async function init() {
  [state.cfg, state.feats] = await Promise.all([api("/api/config"), api("/api/features")]);
  state.byId = Object.fromEntries(state.feats.map((f) => [f.id, f]));
  state.pick = store.get("osf.pick", {});
  state.genSize = store.get("osf.genSize", "m");
  const mode = $("#mode");
  mode.textContent = state.cfg.mode === "mock" ? "Mock mode" : "Live";
  mode.className = `chip ${state.cfg.mode === "mock" ? "mock" : "live"}`;
  mode.title = state.cfg.mode === "mock" ? "Mock mode: no ComfyUI calls are made" : "Connected to Comfy";
  $("#search").addEventListener("input", (e) => { state.query = e.target.value.trim(); route(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && state.run) { e.preventDefault(); state.run(); } });
  window.addEventListener("resize", () => requestAnimationFrame(drawLinks));
  window.addEventListener("hashchange", () => { state.query = ""; $("#search").value = ""; route(); });
  route(); poll();
}
init().catch((e) => ($("#main").textContent = `Failed to load: ${e.message}`));
