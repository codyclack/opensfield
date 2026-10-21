"use strict";
const $ = (s) => document.querySelector(s);
const NS = "http://www.w3.org/2000/svg";
const state = { cfg: null, feats: [], page: null, studio: null, filter: "all", view: "studio", query: "", feature: null, jobs: [], timer: null, links: [], obs: null };

// node-title colours per studio (ComfyUI node-colour feel)
const STUDIO_COLOR = {
  "Genjutsu": "#ff7a59", "Cinema Studio": "#b39ddb", "Reshoot": "#64b5f6", "Viral Hub": "#ff9cf9", "Soul": "#ffa931",
  "Image models": "#81c784", "Image tools": "#4dd0e1", "Video tools": "#7986cb", "Video models": "#aed581",
  "Audio": "#f06292", "Marketing": "#ffd54f", "Match Cut + Tracelab": "#80cbc4", "Platform": "#9e9e9e",
};
// socket colours per data type (ComfyUI slot-colour feel)
const KIND = { image: "#64b5f6", video: "#ff9cf9", audio: "#ffa931", text: "#77dd99", widget: "#a79db3", "3d": "#81c784" };
const sockKind = (s) => (["image", "video", "audio"].includes(s.kind) ? s.kind : s.kind === "text" ? "text" : "widget");
const studioColor = (s) => STUDIO_COLOR[s] || "#9e9e9e";
const hash = (s) => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);

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
const api = async (path, opts) => {
  const r = await fetch(path, opts);
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.detail || `${r.status} ${r.statusText}`);
  return body;
};


/* ---------------- studios rail + home ---------------- */
const STUDIO_ICON = { "Genjutsu": "GJ", "Cinema Studio": "CS", "Reshoot": "RS", "Viral Hub": "VH", "Soul": "SO", "Image models": "IM", "Image tools": "IT",
  "Video tools": "VT", "Video models": "VM", "Audio": "AU", "Marketing": "MK", "Match Cut + Tracelab": "MC", "Platform": "PF" };
const FILTERS = [["all", "All"], ["ready", "Ready to run"], ["image", "Image"], ["video", "Video"], ["audio", "Audio"], ["3d", "3D"]];

function studios() {
  const seen = new Map();
  for (const f of state.feats) seen.set(f.studio, (seen.get(f.studio) || 0) + 1);
  const known = state.cfg.studios.filter((s) => seen.has(s));
  return [...known, ...[...seen.keys()].filter((s) => !known.includes(s))].map((s) => [s, seen.get(s)]);
}

function goHome() { state.page = null; state.studio = null; state.query = ""; $("#search").value = ""; state.feature = null; render(); }

function renderRail() {
  const home = !state.query && !state.feature && !state.studio && !state.page;
  const item = (label, icon, color, current, onclick) => h("button", { type: "button", "aria-current": String(current), style: `--c:${color}`, title: label, onclick },
    h("span", { class: "ico" }, icon), h("span", { class: "nm" }, label));
  $("#rail").replaceChildren(item("Explore", "★", "#d1fe17", home, goHome),
    item("Assets", "▣", "#ff9cf9", state.page === "assets" && !state.feature, () => { state.page = "assets"; state.feature = null; state.query = ""; $("#search").value = ""; render(); }),
    ...studios().map(([s]) => item(s, STUDIO_ICON[s] || s.slice(0, 2).toUpperCase(), studioColor(s), !state.query && !state.feature && !state.page && state.studio === s,
      () => { state.page = null; state.studio = s; state.query = ""; $("#search").value = ""; state.feature = null; render(); })));
}

const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
const isVideo = (url) => /\.(mp4|webm|mov)$/i.test(url);
const isImage = (url) => /\.(png|jpe?g|webp|gif|svg)$/i.test(url);
function exampleEl(url, cls, opts = {}) {
  if (/\.(mp3|wav|flac|ogg)$/i.test(url)) return h("audio", { src: "/" + url, controls: true, preload: "none" });
  if (/\.(glb|gltf)$/i.test(url)) return h("a", { class: "st", href: "/" + url, download: "" }, `Download 3D model (${url.split("/").pop()})`);
  if (!isVideo(url)) return h("img", { class: cls, src: "/" + url, alt: opts.alt || "", loading: "lazy" });
  return h("video", { class: cls, src: "/" + url + "#t=1.5", muted: true, loop: true, playsinline: true, preload: "metadata",
    controls: opts.controls, autoplay: !opts.controls && !reduceMotion, "aria-hidden": opts.controls ? null : "true" });
}

const statusLabel = (f) => (f.status === "tested" ? "Ready" : f.status === "built" ? "Built" : "Soon");
function card(f) {
  const cover = (f.examples || []).find((u) => isVideo(u) || isImage(u));
  const el = h("button", { class: `card${cover ? "" : " plain"}`, type: "button", style: `--h:${hash(f.id) % 360}`, onclick: () => openFeature(f) },
    cover && exampleEl(cover, "bg"),
    h("span", { class: "pill" }, statusLabel(f)),
    h("span", { class: "ckind" }, f.output_kind.toUpperCase() + (f.track === "partner" ? " · API" : "")),
    h("span", { class: "ctext" }, h("b", {}, f.name), h("small", {}, f.engine || f.higgsfield)));
  const v = el.querySelector("video");
  if (v && !reduceMotion) { v.autoplay = false; v.removeAttribute("autoplay"); el.addEventListener("mouseenter", () => v.play().catch(() => {})); el.addEventListener("mouseleave", () => v.pause()); }
  return el;
}

const marker = (text) => h("h1", { class: "marker" }, h("span", {}, text));
const matches = (f) => state.filter === "all" || (state.filter === "ready" ? f.status === "tested" : f.output_kind === state.filter);

function hero() {
  const ready = state.feats.filter((f) => f.status === "tested").length;
  const pick = state.feats.find((f) => f.id === "marketing.click-to-ad") || state.feats.find((f) => f.examples.some(isVideo));
  const art = pick && pick.examples.find(isVideo);
  return h("section", { class: "hero" },
    art && h("video", { class: "bg", src: "/" + art, muted: true, loop: true, autoplay: !reduceMotion, playsinline: true, "aria-hidden": "true" }),
    h("div", { class: "htext" },
      h("span", { class: "eyebrow" }, "COMFYUI · OPEN WEIGHTS + PARTNER MODELS"),
      h("h2", {}, "Every Higgsfield tool, on ComfyUI."),
      h("p", {}, `${ready} tools verified end to end, ${state.feats.length} in the catalog. Open-weight workflows plus Seedance, Kling, GPT Image, Nano Banana and more. Built on the Comfy Developer Platform.`),
      h("div", { class: "hbtns" },
        h("button", { class: "go", type: "button", onclick: () => { const f = state.feats.find((x) => x.id === "cinema.camera-rig"); if (f) openFeature(f); } }, "Start creating"),
        h("a", { class: "ghost", href: "https://github.com/codyclack/opensfield", target: "_blank", rel: "noopener" }, "View source"))));
}

function renderGrid() {
  const q = state.query.toLowerCase();
  const filters = h("div", { class: "filters", role: "group", "aria-label": "Filter tools" },
    FILTERS.map(([k, l]) => h("button", { type: "button", class: "fpill", "aria-pressed": String(state.filter === k), onclick: () => { state.filter = k; render(); } }, l)));
  let body;
  if (q || state.studio) {
    const list = state.feats.filter((f) => (q ? `${f.name} ${f.higgsfield} ${f.studio} ${f.id}`.toLowerCase().includes(q) : f.studio === state.studio)).filter(matches);
    body = [marker(q ? `Search: ${state.query}` : state.studio), filters,
      list.length ? h("div", { class: "cards" }, list.map(card)) : h("p", { class: "empty" }, "Nothing here for this filter.")];
  } else {
    body = [hero(), filters, ...studios().map(([s]) => {
      const list = state.feats.filter((f) => f.studio === s).filter(matches).sort((a, b) => (b.status === "tested") - (a.status === "tested"));
      return list.length && h("section", { class: "row" },
        h("div", { class: "rowhead" }, h("h3", {}, s), h("button", { type: "button", class: "more", onclick: () => { state.studio = s; render(); } }, `See all ${list.length} →`)),
        h("div", { class: "strip" }, list.map(card)));
    })];
  }
  $("#main").replaceChildren(...body.filter(Boolean));
  state.links = [];
}


/* ---------------- feature view: a ComfyUI-style graph ---------------- */
function node({ title, kind, color, req, body, out = false, inn = false, cls = "" }) {
  return h("div", { class: `node ${cls}` },
    h("div", { class: "ntitle", style: `--c:${color || KIND[kind]}` }, h("i", { class: "dot" }), h("span", {}, title), req && h("span", { class: "req" }, "*"),
      kind && h("span", { class: "ntype" }, kind === "widget" ? "SETTINGS" : kind.toUpperCase())),
    out && sock(kind, "out"), inn && sock(kind, "in"),
    h("div", { class: "nbody" }, body));
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

function mediaBody(spec, vals) {
  const id = `f-${spec.name}`;
  const img = h("img", { alt: "", hidden: true }), label = h("span", {}, `Drop or click: ${spec.kind}`);
  const ui = { img, label };
  const input = h("input", { class: "sr", id, type: "file", accept: { image: "image/*", video: "video/*", audio: "audio/*" }[spec.kind],
    onchange: (e) => e.target.files[0] && upload(e.target.files[0], spec, vals, ui) });
  const zone = h("label", { class: "drop", for: id }, img, label, input);
  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("over"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("over"));
  zone.addEventListener("drop", (e) => { e.preventDefault(); zone.classList.remove("over"); if (e.dataTransfer.files[0]) upload(e.dataTransfer.files[0], spec, vals, ui); });
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
    h("div", { class: "chips", title: "Base graphs" }, f.base.map((b) => h("span", {}, b))),
    f.note && h("p", { class: "note" }, f.note),
    h("div", { class: "slot out" }, f.output_kind.toUpperCase(), outSock)] });
  const onode = h("div", { class: "node onode" }, h("div", { class: "ntitle", style: `--c:${KIND[f.output_kind]}` }, h("i", { class: "dot" }), "Preview", h("span", { class: "ntype" }, f.output_kind.toUpperCase())),
    prevSock, h("div", { class: "nbody" }, h("div", { id: "preview", class: "preview" })));

  const svg = svgEl("svg", { class: "links", "aria-hidden": "true" });
  const graph = h("div", { class: "graph" }, svg, h("div", { class: "col" }, ins.map((n) => n.el)), fnode, onode);
  state.links = [
    ...ins.map((n, i) => ({ from: n.el.querySelector(":scope > .sock.out"), to: slotEls[i].querySelector(".sock"), color: KIND[n.kind] })),
    { from: outSock, to: prevSock, color: KIND[f.output_kind] },
  ];
  state.svg = svg;
  return graph;
}

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

/* ---------------- feature view: Higgsfield-style composer (graph view stays available) ---------------- */
const ratioOf = (o) => { const m = /^(\d+):(\d+)/.exec(o); return m ? [Number(m[1]), Number(m[2])] : null; };

function pills(spec, vals, render = (o) => o) {
  const group = h("div", { class: "opts", role: "radiogroup", "aria-label": spec.label });
  const set = (o) => { vals[spec.name] = o; group.querySelectorAll("button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.v === String(o)))); };
  for (const o of spec.options) group.append(h("button", { type: "button", role: "radio", "data-v": o, "aria-checked": "false", title: spec.presets?.[o] || o, onclick: () => set(o) }, render(o)));
  set(vals[spec.name]);
  return group;
}

function aspectChip(o) {
  const r = ratioOf(o), [w, hh] = r, k = 22 / Math.max(w, hh);
  return [h("i", { class: "ar", style: `width:${Math.round(w * k)}px;height:${Math.round(hh * k)}px` }), h("span", {}, o.split(" ")[0])];
}

function field(spec, body, hint) {
  return h("div", { class: "field" }, h("div", { class: "flabel" }, spec.label, spec.required && h("b", {}, " *")), body, hint && h("div", { class: "fhint" }, hint));
}

function uploadTile(spec, vals) {
  const id = `f-${spec.name}`;
  const img = h("img", { alt: "", hidden: true }), cap = h("span", { class: "cap" }, spec.kind === "image" ? "Add image" : spec.kind === "video" ? "Add video" : "Add audio");
  const ui = { img, label: cap };
  const input = h("input", { class: "sr", id, type: "file", accept: { image: "image/*", video: "video/*", audio: "audio/*" }[spec.kind],
    onchange: (e) => e.target.files[0] && upload(e.target.files[0], spec, vals, ui) });
  const zone = h("label", { class: "utile", for: id }, img, h("span", { class: "plus", "aria-hidden": "true" }, spec.kind === "image" ? "+" : spec.kind === "video" ? "▶" : "♪"), cap, input);
  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("over"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("over"));
  zone.addEventListener("drop", (e) => { e.preventDefault(); zone.classList.remove("over"); if (e.dataTransfer.files[0]) upload(e.dataTransfer.files[0], spec, vals, ui); });
  return h("div", { class: "ufield" }, zone, h("div", { class: "flabel" }, spec.label, spec.required && h("b", {}, " *")),
    h("button", { class: "libbtn", type: "button", onclick: () => pickAsset(spec, vals, ui) }, "From assets"));
}

function control(spec, vals) {
  const n = spec.options?.length || 0;
  vals[spec.name] = spec.default ?? vals[spec.name] ?? 0;
  if (spec.kind === "choice") {
    if (spec.options.every((o) => ratioOf(o))) return field(spec, pills(spec, vals, aspectChip));
    if (n <= 6) return field(spec, pills(spec, vals), spec.presets && "Hover a style to read its prompt.");
    return field(spec, h("select", { onchange: (e) => (vals[spec.name] = e.target.value) }, spec.options.map((o) => h("option", { value: o, selected: o === spec.default }, o))));
  }
  const steps = (spec.max - spec.min) / (spec.step || 1);
  if (steps <= 12 && Number.isFinite(steps)) {
    const o = { ...spec, options: Array.from({ length: steps + 1 }, (_, i) => spec.min + i * (spec.step || 1)) };
    return field(spec, pills(o, vals));
  }
  const out = h("output", {}, String(vals[spec.name]));
  const range = h("input", { type: "range", min: spec.min, max: spec.max, step: spec.step || 1, value: vals[spec.name], "aria-label": spec.label,
    oninput: (e) => { vals[spec.name] = Number(e.target.value); out.textContent = e.target.value; } });
  return field(spec, h("div", { class: "slider" }, range, out));
}

function buildComposer(f, vals) {
  const media = f.inputs.filter((s) => ["image", "video", "audio"].includes(s.kind));
  const texts = f.inputs.filter((s) => s.kind === "text");
  const opts = f.inputs.filter((s) => ["choice", "number"].includes(s.kind));
  const seed = f.inputs.find((s) => s.kind === "seed");
  const presetOpts = opts.filter((s) => s.presets), plainOpts = opts.filter((s) => !s.presets);
  if (seed) vals[seed.name] = 0;
  return h("div", { class: "composer" },
    modelSwitch(f),
    media.length > 0 && h("div", { class: "uploads" }, media.map((s) => uploadTile(s, vals))),
    ...presetOpts.map((s) => control(s, vals)),
    ...texts.map((s) => field(s, h("textarea", { id: `f-${s.name}`, "aria-label": s.label, rows: 4, placeholder: s.required ? "Describe what you want..." : "Optional", oninput: (e) => (vals[s.name] = e.target.value) },
      s.name === "prompt" && state.carry ? (vals[s.name] = state.carry, state.carry = null, vals[s.name]) : ""))),
    ...plainOpts.map((s) => control(s, vals)),
    seed && h("details", { class: "adv" }, h("summary", {}, "Advanced"),
      field(seed, h("input", { type: "number", min: 0, value: 0, "aria-label": seed.label, oninput: (e) => (vals[seed.name] = Number(e.target.value)) }), "0 picks a random seed each run.")));
}

function renderFeature(f) {
  const vals = {}, err = h("span", { class: "err", role: "alert" });
  const go = h("button", { class: "go wide", type: "button" }, "Generate");
  const run = async () => {
    err.textContent = ""; go.disabled = true;
    try { await api("/api/jobs", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ feature_id: f.id, inputs: vals }) }); poll(); }
    catch (e) { err.textContent = e.message; }
    go.disabled = false;
  };
  go.addEventListener("click", run);
  state.run = run;
  const head = h("div", { class: "fhead" },
    h("button", { class: "back", type: "button", onclick: () => { state.feature = null; render(); } }, `← ${state.query ? "Search" : f.studio}`),
    h("div", { class: "seg", role: "group", "aria-label": "View" },
      ["studio", "graph"].map((v) => h("button", { type: "button", "aria-pressed": String(state.view === v), onclick: () => { state.view = v; render(); } }, v === "studio" ? "Studio" : "Node graph"))));
  const sub = h("div", { class: "sub" }, f.engine && badge(f.engine, "A"), badge(statusLabel(f)), f.count > 1 && badge(`${f.count} presets`), f.track === "partner" && badge("partner", "partner"), h("span", {}, `outputs ${f.output_kind}`));
  if (state.obs) { state.obs.disconnect(); state.obs = null; }
  if (state.view === "graph") {
    const graph = buildGraph(f, vals);
    $("#main").replaceChildren(head, marker(f.name), sub, graph,
      h("div", { class: "runbar" }, h("div", { class: "sum" }, `${f.inputs.length} input${f.inputs.length === 1 ? "" : "s"} -> ${f.output_kind}`), err, h("kbd", {}, "Ctrl+Enter"), go));
    state.obs = new ResizeObserver(() => requestAnimationFrame(drawLinks));
    state.obs.observe(graph); graph.querySelectorAll(".node").forEach((n) => state.obs.observe(n));
    drawLinks();
  } else {
    state.links = [];
    $("#main").replaceChildren(head, marker(f.name), sub,
      h("div", { class: "create" },
        h("aside", { class: "panel" }, h("p", { class: "hf" }, f.higgsfield), f.note && h("p", { class: "note" }, f.note), buildComposer(f, vals),
          h("div", { class: "gen" }, err, go, h("div", { class: "fine" }, !f.runnable && state.cfg.mode === "comfy" ? "No workflow built yet for this tool." : f.local ? "Runs on this computer's CPU." : f.track === "partner" ? "Partner model through Comfy Cloud. Uses your Comfy credits. Ctrl+Enter to run." : "Open weights on Comfy. Ctrl+Enter to run."))),
        h("section", { class: "results", "aria-label": "Results" }, h("div", { id: "preview", class: "gallery" }))));
  }
  updatePreview();
}

function openFeature(f) { state.feature = f; render(); window.scrollTo(0, 0); }
function render() { renderRail(); state.feature ? renderFeature(state.feature) : state.page === "assets" ? renderAssets() : renderGrid(); }

/* ---------------- queue + preview ---------------- */

function jobMedia(j) {
  return [
    h("div", { class: `st ${j.status}` }, j.status + (j.status === "running" ? ` ${Math.round(j.progress * 100)}%` : "")),
    (j.status === "running" || j.status === "queued") && h("div", { class: "bar" }, h("i", { style: `width:${j.progress * 100}%` })),
    j.error && h("div", { class: "st error" }, j.error),
    ...j.outputs.map((o) => o.kind === "video" ? h("video", { class: "thumb", src: o.url, controls: true })
      : o.kind === "audio" ? h("audio", { src: o.url, controls: true }) : h("img", { class: "thumb", src: o.url, alt: `${j.feature_name} output` })),
    ...j.outputs.filter((o) => o.kind !== "3d" && !o.mock).map((o) => h("button", { class: "savebtn", type: "button", onclick: (e) => saveToAssets(o, e.currentTarget) }, "Save to assets")),
    ...j.outputs.filter((o) => o.kind === "3d").map((o) => h("a", { class: "st", href: o.url, download: "" }, `Download ${o.name}`)),
    j.outputs.some((o) => o.mock) && h("div", { class: "st" }, "mock placeholder, no ComfyUI call"),
  ].filter(Boolean);
}

function updatePreview() {
  const box = $("#preview");
  if (!box || !state.feature) return;
  const f = state.feature, mine = state.jobs.filter((x) => x.feature_id === f.id), ex = f.examples || [];
  box.replaceChildren(
    ...(mine.length ? [h("h4", {}, "Your generations"), ...mine.map((j) => h("figure", { class: "gcard" }, jobMedia(j)))] : []),
    ...(ex.length ? [h("h4", {}, mine.length ? "Examples" : "Example renders (real runs on Comfy Cloud)"), ...ex.map((u) => h("figure", { class: "gcard" }, exampleEl(u, "thumb", { controls: true, alt: f.name + " example" })))] : []),
    ...(!mine.length && !ex.length ? [h("div", { class: "empty" }, "Your results appear here.")] : []));
}

function renderJobs() {
  const active = state.jobs.filter((j) => j.status === "queued" || j.status === "running").length;
  $("#qcount").textContent = active;
  const box = $("#jobs");
  if (!state.jobs.length) { box.className = "empty"; box.textContent = "No jobs yet."; }
  else {
    box.className = "";
    box.replaceChildren(...state.jobs.map((j) => h("div", { class: "job", title: "Open this feature", onclick: () => { const f = state.feats.find((x) => x.id === j.feature_id); if (f) openFeature(f); } },
      h("div", { class: "t" }, j.feature_name), ...jobMedia(j))));
  }
  updatePreview();
}

async function poll() {
  clearTimeout(state.timer);
  try { state.jobs = await api("/api/jobs"); renderJobs(); } catch (e) { $("#jobs").textContent = e.message; }
  if (state.jobs.some((j) => j.status === "queued" || j.status === "running")) state.timer = setTimeout(poll, 700);
}

/* ---------------- model switcher, asset library, asset picker ---------------- */
function modelSwitch(f) {
  const sibs = f.group ? state.feats.filter((x) => x.group === f.group) : [];
  if (sibs.length < 2) return null;
  const opt = (x) => h("option", { value: x.id, selected: x.id === f.id }, `${x.name}${x.status === "tested" ? "" : "  (untested)"}`);
  const open = sibs.filter((x) => x.track !== "partner"), part = sibs.filter((x) => x.track === "partner");
  const sel = h("select", { "aria-label": "Model", onchange: (e) => {
    const next = state.feats.find((x) => x.id === e.target.value);
    const t = $("#f-prompt");
    state.carry = t && t.value ? t.value : null;
    if (next) openFeature(next);
  } }, open.length && h("optgroup", { label: "Open weights" }, open.map(opt)), part.length && h("optgroup", { label: "Partner models (Comfy credits)" }, part.map(opt)));
  return h("div", { class: "field modelsel" }, h("div", { class: "flabel" }, `Model · ${f.group}`), sel);
}

async function saveToAssets(o, btn) {
  btn.disabled = true; btn.textContent = "Saving...";
  try {
    await api("/api/assets/save", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ url: o.url, name: o.name.replace(/\.[a-z0-9]+$/i, "").slice(0, 40) }) });
    btn.textContent = "Saved. Organise it in Assets";
  } catch (e) { btn.disabled = false; btn.textContent = `Could not save: ${e.message}`; }
}

function assetThumb(a) {
  if (a.kind === "video") return h("video", { src: a.url + "#t=0.5", muted: true, preload: "metadata", playsinline: true });
  if (a.kind === "audio") return h("div", { class: "aud" }, "♪", h("audio", { src: a.url, controls: true, preload: "none" }));
  return h("img", { src: a.url, alt: a.name, loading: "lazy" });
}

async function renderAssets() {
  const main = $("#main");
  main.replaceChildren(marker("Assets"), h("p", { class: "sub" }, "Characters, props, locations and styles you reuse across tools. Pick them as inputs with “From assets”."));
  let data;
  try { data = await api("/api/assets"); } catch (e) { main.append(h("p", { class: "err" }, e.message)); return; }
  let filter = state.assetFilter || "All";
  const grid = h("div", { class: "cards assets" });
  const pillsEl = h("div", { class: "filters" });
  const typeSel = h("select", { "aria-label": "Type for new uploads" }, data.types.map((t) => h("option", { value: t }, t)));
  const file = h("input", { type: "file", multiple: true, accept: "image/*,video/*,audio/*", class: "sr", id: "asset-up",
    onchange: async (e) => {
      for (const fl of e.target.files) {
        const fd = new FormData(); fd.append("file", fl); fd.append("type", typeSel.value); fd.append("name", fl.name.replace(/\.[a-z0-9]+$/i, ""));
        try { await api("/api/assets", { method: "POST", body: fd }); } catch (err) { alert(`${fl.name}: ${err.message}`); }
      }
      renderAssets();
    } });
  const draw = () => {
    pillsEl.replaceChildren(...["All", ...data.types].map((t) => h("button", { type: "button", class: "fpill", "aria-pressed": String(filter === t), onclick: () => { filter = t; state.assetFilter = t; draw(); } }, t)));
    const items = data.items.filter((a) => filter === "All" || a.type === filter);
    grid.replaceChildren(...(items.length ? items.map((a) => h("div", { class: "acard" },
      h("div", { class: "athumb" }, assetThumb(a)),
      h("div", { class: "ameta" },
        h("input", { class: "aname", value: a.name, "aria-label": "Name", onchange: (e) => api(`/api/assets/${a.id}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: e.target.value }) }) }),
        h("select", { "aria-label": "Type", onchange: (e) => api(`/api/assets/${a.id}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ type: e.target.value }) }) },
          data.types.map((t) => h("option", { value: t, selected: t === a.type }, t))),
        h("button", { class: "adel", type: "button", title: "Delete", "aria-label": `Delete ${a.name}`, onclick: async () => { await api(`/api/assets/${a.id}`, { method: "DELETE" }).catch(() => {}); renderAssets(); } }, "✕")))
    ) : [h("p", { class: "empty" }, data.items.length ? "Nothing of this type yet." : "No assets yet. Upload some, or use “Save to assets” on any result.")]));
  };
  main.append(h("div", { class: "uprow" }, h("label", { class: "go", for: "asset-up" }, "+ Upload"), typeSel, file), pillsEl, grid);
  draw();
}

async function pickAsset(spec, vals, ui) {
  let data;
  try { data = await api("/api/assets"); } catch (e) { alert(e.message); return; }
  const items = data.items.filter((a) => a.kind === spec.kind);
  const close = () => { overlay.remove(); document.removeEventListener("keydown", onKey); };
  const onKey = (e) => { if (e.key === "Escape") close(); };
  const overlay = h("div", { class: "modal", role: "dialog", "aria-modal": "true", "aria-label": "Choose an asset", onclick: (e) => e.target === overlay && close() },
    h("div", { class: "mbox" },
      h("div", { class: "mhead" }, h("b", {}, `Choose ${spec.kind === "image" ? "an image" : spec.kind === "video" ? "a video" : "an audio clip"}`), h("button", { type: "button", class: "adel", "aria-label": "Close", onclick: close }, "✕")),
      items.length ? h("div", { class: "cards assets" }, items.map((a) => h("button", { type: "button", class: "acard pick", onclick: async () => {
        try {
          const up = await api(`/api/assets/${a.id}/use`, { method: "POST" });
          vals[spec.name] = up.id; ui.label.textContent = a.name;
          if (spec.kind === "image") { ui.img.src = a.url; ui.img.hidden = false; }
          close();
        } catch (e) { alert(e.message); }
      } }, h("div", { class: "athumb" }, assetThumb(a)), h("div", { class: "ameta" }, h("span", { class: "aname" }, a.name), h("small", {}, a.type)))))
        : h("p", { class: "empty" }, `No ${spec.kind} assets yet. Add some in Assets, or use “Save to assets” on a result.`)));
  document.body.append(overlay);
  document.addEventListener("keydown", onKey);
}

async function init() {
  [state.cfg, state.feats] = await Promise.all([api("/api/config"), api("/api/features")]);
  const mode = $("#mode");
  mode.textContent = state.cfg.mode === "mock" ? "Mock mode: no ComfyUI calls" : "ComfyUI connected";
  mode.className = `chip ${state.cfg.mode === "mock" ? "mock" : "live"}`;
  const link = location.hash.match(/^#([sfp])=(.+)$/);  // deep links: #s=<Studio name>, #f=<feature id>, #p=assets
  if (link) {
    const v = decodeURIComponent(link[2]);
    if (link[1] === "p" && v === "assets") state.page = "assets";
    const f = link[1] === "f" && state.feats.find((x) => x.id === v);
    if (f) { state.feature = f; state.studio = f.studio; } else if (studios().some(([s]) => s === v)) state.studio = v;
  }
  $("#search").addEventListener("input", (e) => { state.query = e.target.value.trim(); state.feature = null; state.page = null; render(); });
  $("#qtoggle").addEventListener("click", () => { const o = document.body.classList.toggle("q-open"); $("#qtoggle").setAttribute("aria-expanded", String(o)); });
  document.addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && state.feature && state.run) { e.preventDefault(); state.run(); } });
  window.addEventListener("resize", () => requestAnimationFrame(drawLinks));
  render(); poll();
}
init().catch((e) => ($("#main").textContent = `Failed to load: ${e.message}`));