"use strict";
const $ = (s) => document.querySelector(s);
const NS = "http://www.w3.org/2000/svg";
const state = { cfg: null, feats: [], studio: null, query: "", feature: null, jobs: [], timer: null, links: [], obs: null };

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

/* ---------------- studios rail + home grid ---------------- */
function studios() {
  const seen = new Map();
  for (const f of state.feats) seen.set(f.studio, (seen.get(f.studio) || 0) + 1);
  const known = state.cfg.studios.filter((s) => seen.has(s));
  return [...known, ...[...seen.keys()].filter((s) => !known.includes(s))].map((s) => [s, seen.get(s)]);
}

function renderRail() {
  $("#rail").replaceChildren(h("div", { class: "label" }, "STUDIOS"),
    ...studios().map(([s, n]) =>
      h("button", { type: "button", "aria-current": String(!state.query && !state.feature && state.studio === s), style: `--c:${studioColor(s)}`,
        onclick: () => { state.studio = s; state.query = ""; $("#search").value = ""; state.feature = null; render(); } },
        h("i", { class: "dot" }), h("span", { class: "nm" }, s), h("span", { class: "n" }, n))));
}

const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
const isVideo = (url) => /\.(mp4|webm|mov)$/i.test(url);
function exampleEl(url, cls, opts = {}) {
  if (!isVideo(url)) return h("img", { class: cls, src: "/" + url, alt: opts.alt || "", loading: "lazy" });
  return h("video", { class: cls, src: "/" + url + "#t=1.5", muted: true, loop: true, playsinline: true, preload: "metadata",
    controls: opts.controls, autoplay: !opts.controls && !reduceMotion, "aria-hidden": opts.controls ? null : "true" });
}

function tile(f) {
  const kinds = [...new Set(f.inputs.map(sockKind))];
  const cover = f.examples && f.examples[0];
  return h("button", { class: "tile", type: "button", onclick: () => openFeature(f) },
    h("span", { class: "tbar", style: `--c:${studioColor(f.studio)}` }, h("i", { class: "dot" }), h("span", { class: "grow" }, f.studio),
      f.track === "partner" && badge("partner", "partner")),
    h("span", { class: `art${cover ? " has-media" : ""}`, style: `--h:${hash(f.id) % 360}` }, cover && exampleEl(cover, "bg"), h("span", { class: "big" }, f.name)),
    h("span", { class: "tmeta" },
      h("span", { class: "src" }, f.higgsfield),
      h("span", { class: "io" },
        h("span", { class: "ins" }, kinds.map((k) => sock(k, "mini")), h("span", {}, kinds.join(" / ").toUpperCase() || "NO INPUTS")),
        h("span", { class: "out" }, f.output_kind.toUpperCase(), sock(f.output_kind, "mini"))),
      h("span", { class: "badges" }, badge(`Tier ${f.tier}`, f.tier), badge(f.status), f.count > 1 && badge(`${f.count} presets`))));
}

const marker = (text) => h("h1", { class: "marker" }, h("span", {}, text));

function renderGrid() {
  const q = state.query.toLowerCase();
  const list = state.feats.filter((f) => (q ? `${f.name} ${f.higgsfield} ${f.studio} ${f.id}`.toLowerCase().includes(q) : f.studio === state.studio));
  const tiers = ["A", "B", "C"].map((t) => [t, list.filter((f) => f.tier === t).length]).filter(([, n]) => n);
  $("#main").replaceChildren(
    marker(q ? `Search: ${state.query}` : state.studio),
    h("div", { class: "sub" }, `${list.length} feature${list.length === 1 ? "" : "s"}`, tiers.map(([t, n]) => badge(`Tier ${t}: ${n}`, t)),
      !state.cfg.partner_enabled && h("span", {}, "Partner-model modules hidden")),
    h("div", { class: "grid" }, list.map(tile)));
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

function renderFeature(f) {
  const vals = {}, err = h("span", { class: "err", role: "alert" });
  const go = h("button", { class: "go", type: "button" }, h("span", {}, "Generate"));
  go.prepend(svgEl("svg", { viewBox: "0 0 14 14", "aria-hidden": "true" }));
  go.firstChild.append(svgEl("path", { d: "M3 1.5v11l9-5.5z" }));
  const run = async () => {
    err.textContent = ""; go.disabled = true;
    try { await api("/api/jobs", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ feature_id: f.id, inputs: vals }) }); poll(); }
    catch (e) { err.textContent = e.message; }
    go.disabled = false;
  };
  go.addEventListener("click", run);
  state.run = run;

  const graph = buildGraph(f, vals);
  $("#main").replaceChildren(
    h("button", { class: "back", type: "button", onclick: () => { state.feature = null; render(); } }, `< ${state.query ? "Search" : f.studio}`),
    marker(f.name),
    h("div", { class: "sub" }, badge(`Tier ${f.tier}`, f.tier), f.track === "partner" && badge("partner", "partner"), badge(f.status), `outputs ${f.output_kind}`),
    graph,
    h("div", { class: "runbar" },
      h("div", { class: "sum" }, `${f.inputs.length} input${f.inputs.length === 1 ? "" : "s"} -> ${f.output_kind}`,
        !f.runnable && state.cfg.mode === "comfy" ? " (no workflow built yet)" : ""),
      err, h("kbd", {}, "Ctrl+Enter"), go));
  if (state.obs) state.obs.disconnect();
  state.obs = new ResizeObserver(() => requestAnimationFrame(drawLinks));
  state.obs.observe(graph); graph.querySelectorAll(".node").forEach((n) => state.obs.observe(n));
  drawLinks(); updatePreview();
}

function openFeature(f) { state.feature = f; render(); window.scrollTo(0, 0); }
function render() { renderRail(); state.feature ? renderFeature(state.feature) : renderGrid(); }

/* ---------------- queue + preview ---------------- */
function jobMedia(j) {
  return [
    h("div", { class: `st ${j.status}` }, j.status + (j.status === "running" ? ` ${Math.round(j.progress * 100)}%` : "")),
    (j.status === "running" || j.status === "queued") && h("div", { class: "bar" }, h("i", { style: `width:${j.progress * 100}%` })),
    j.error && h("div", { class: "st error" }, j.error),
    ...j.outputs.map((o) => o.kind === "video" ? h("video", { class: "thumb", src: o.url, controls: true })
      : o.kind === "audio" ? h("audio", { src: o.url, controls: true }) : h("img", { class: "thumb", src: o.url, alt: `${j.feature_name} output` })),
    j.outputs.some((o) => o.mock) && h("div", { class: "st" }, "mock placeholder, no ComfyUI call"),
  ].filter(Boolean);
}

function updatePreview() {
  const box = $("#preview");
  if (!box || !state.feature) return;
  const j = state.jobs.find((x) => x.feature_id === state.feature.id);
  const ex = state.feature.examples || [];
  box.replaceChildren(...(j ? jobMedia(j) : ex.length
    ? [h("div", { class: "st" }, "Example renders (real, Comfy Cloud). Run the graph to make your own."),
       ...ex.map((u) => exampleEl(u, "thumb", { controls: true, alt: `${state.feature.name} example` }))]
    : [h("div", { class: "empty" }, "Run the graph to see the result here.")]));
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

async function init() {
  [state.cfg, state.feats] = await Promise.all([api("/api/config"), api("/api/features")]);
  const mode = $("#mode");
  mode.textContent = state.cfg.mode === "mock" ? "Mock mode: no ComfyUI calls" : "ComfyUI connected";
  mode.className = `chip ${state.cfg.mode === "mock" ? "mock" : "live"}`;
  state.studio = studios()[0][0];
  $("#search").addEventListener("input", (e) => { state.query = e.target.value.trim(); state.feature = null; render(); });
  $("#qtoggle").addEventListener("click", () => { const o = document.body.classList.toggle("q-open"); $("#qtoggle").setAttribute("aria-expanded", String(o)); });
  document.addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && state.feature && state.run) { e.preventDefault(); state.run(); } });
  window.addEventListener("resize", () => requestAnimationFrame(drawLinks));
  render(); poll();
}
init().catch((e) => ($("#main").textContent = `Failed to load: ${e.message}`));
