"use strict";
/* Creator Hub (blog with how-to tutorials, like higgsfield.ai/blog), Community showcase and the site-map footer.
   Uses helpers from app.js. Posts are markdown files in blog/ served by /api/blog. */

const BLOG_TABS = ["All", "Guides", "Listicles", "Editorials", "Inside OpenSfield", "Changelog"];
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/** Small, safe markdown: everything is escaped first, then a few patterns are turned into tags. */
function md(src) {
  const inline = (t) => esc(t)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+|#[^)\s]*)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  const out = [], lines = src.replace(/\r/g, "").split("\n");
  let i = 0;
  while (i < lines.length) {
    const l = lines[i];
    if (/^```/.test(l)) {
      const buf = []; i++;
      while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]);
      out.push(`<pre><code>${esc(buf.join("\n"))}</code></pre>`); i++; continue;
    }
    if (/^#{2,3} /.test(l)) { const n = l.startsWith("### ") ? 3 : 2; out.push(`<h${n}>${inline(l.replace(/^#+ /, ""))}</h${n}>`); i++; continue; }
    if (/^> /.test(l)) { const buf = []; while (i < lines.length && /^> /.test(lines[i])) buf.push(lines[i++].slice(2)); out.push(`<blockquote>${inline(buf.join(" "))}</blockquote>`); continue; }
    if (/^\|/.test(l)) {
      const rows = []; while (i < lines.length && /^\|/.test(lines[i])) rows.push(lines[i++]);
      const cells = (r) => r.replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
      const body = rows.filter((r) => !/^\|[\s|:-]+\|$/.test(r));
      out.push(`<table><thead><tr>${cells(body[0]).map((c) => `<th>${inline(c)}</th>`).join("")}</tr></thead><tbody>${body.slice(1).map((r) => `<tr>${cells(r).map((c) => `<td>${inline(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`);
      continue;
    }
    if (/^(- |\d+\. )/.test(l)) {
      const ordered = /^\d+\. /.test(l), buf = [];
      while (i < lines.length && /^(- |\d+\. )/.test(lines[i])) buf.push(lines[i++].replace(/^(- |\d+\. )/, ""));
      out.push(`<${ordered ? "ol" : "ul"}>${buf.map((b) => `<li>${inline(b)}</li>`).join("")}</${ordered ? "ol" : "ul"}>`); continue;
    }
    if (!l.trim()) { i++; continue; }
    const buf = []; while (i < lines.length && lines[i].trim() && !/^(```|#{2,3} |> |\||- |\d+\. )/.test(lines[i])) buf.push(lines[i++]);
    out.push(`<p>${inline(buf.join(" "))}</p>`);
  }
  return out.join("\n");
}

function hubNav(active) {
  return h("div", { class: "hubnav" }, h("a", { class: "hublogo", href: "#/blog" }, "CREATOR HUB"),
    h("nav", {}, ...[["#/blog", "Blog", "blog"], ["#/blog/first-video-seedance", "Get started", "start"], ["#/blog/changelog-oct-22", "Changelog", "log"],
      ["https://github.com/codyclack/opensfield", "GitHub", "gh"]].map(([href, l, k]) => h("a", { href, "aria-current": active === k ? "page" : null,
      target: href.startsWith("http") ? "_blank" : null, rel: href.startsWith("http") ? "noopener" : null }, l))));
}
const postMeta = (p) => h("span", { class: "pmeta" }, h("span", { class: "ptag" }, p.category || "Post"), h("small", {}, `${p.minutes} min · ${p.date}`));

async function renderBlog(slug) {
  const main = $("#main");
  if (slug) return renderPost(slug);
  let posts = [];
  try { posts = await api("/api/blog"); } catch (e) { main.replaceChildren(h("p", { class: "err" }, e.message)); return; }
  let tab = state.blogTab || "All", q = "";
  const list = h("div", {});
  const search = h("input", { type: "search", placeholder: "Search blog", "aria-label": "Search blog", oninput: (e) => { q = e.target.value.toLowerCase(); draw(); } });
  const tabs = h("div", { class: "wtabs blogtabs", role: "tablist" });
  const draw = () => {
    tabs.replaceChildren(...BLOG_TABS.map((t) => h("button", { type: "button", role: "tab", class: "tabbtn", "aria-selected": String(tab === t), onclick: () => { tab = t; state.blogTab = t; draw(); } }, t)));
    const shown = posts.filter((p) => (tab === "All" || p.category === tab) && (!q || `${p.title} ${p.excerpt}`.toLowerCase().includes(q)));
    if (!shown.length) { list.replaceChildren(h("p", { class: "empty" }, "No posts match.")); return; }
    const [top, ...rest] = shown;
    list.replaceChildren(
      hoverPlay(h("a", { class: "featured", href: `#/blog/${top.slug}` }, h("span", { class: "fcover" }, top.cover && exampleEl(top.cover, "bg", { autoplay: true })),
        h("span", { class: "ftxt" }, postMeta(top), h("b", {}, top.title), h("small", {}, top.excerpt), h("span", { class: "readnow" }, "Read now")))),
      h("div", { class: "postgrid" }, ...rest.map((p) => hoverPlay(h("a", { class: "postcard", href: `#/blog/${p.slug}` }, h("span", { class: "pcover" }, p.cover && exampleEl(p.cover, "bg")),
        postMeta(p), h("b", {}, p.title), h("small", {}, p.excerpt))))));
  };
  main.replaceChildren(hubNav("blog"),
    h("div", { class: "hubhero" }, h("h1", {}, "EVERYTHING ABOUT", h("br"), h("span", {}, "CREATING WITH OPENSFIELD"))),
    h("div", { class: "hubbar" }, tabs, h("label", { class: "search wide" }, h("span", { "aria-hidden": "true" }, "⌕"), search)),
    list, siteFooter());
  document.title = "Creator Hub · OpenSfield";
  draw();
}

async function renderPost(slug) {
  const main = $("#main");
  let post;
  try { post = await api(`/api/blog/${encodeURIComponent(slug)}`); } catch (e) { main.replaceChildren(hubNav("blog"), h("p", { class: "err" }, e.message)); return; }
  const m = post.meta;
  const article = h("article", { class: "post" });
  article.innerHTML = md(post.body);  // md() escapes all text before adding tags
  main.replaceChildren(hubNav(m.category === "Changelog" ? "log" : "blog"),
    h("div", { class: "postwrap" }, h("a", { class: "back", href: "#/blog" }, "← All posts"), postMeta(m), h("h1", { class: "ptitle" }, m.title),
      h("p", { class: "plead" }, m.excerpt), m.cover && h("div", { class: "pheroimg" }, exampleEl(m.cover, "bg", { controls: isVideo(m.cover) })), article,
      h("div", { class: "pcta" }, h("b", {}, "Try it now"), h("a", { class: "go", href: "#/w/video/0" }, "Create video"), h("a", { class: "ghost", href: "#/cinema" }, "Open Cinema Studio"))),
    siteFooter());
  document.title = `${m.title} · OpenSfield`;
}

/* Community: every real render in the repo, like Higgsfield's community feed. */
function renderCommunity(target) {
  const el = target || $("#main");
  const items = [];
  for (const f of state.feats) for (const u of f.examples || []) if (isVideo(u) || isImage(u)) items.push([u, f]);
  const seen = new Set();
  const uniq = items.filter(([u]) => !seen.has(u) && seen.add(u));
  el.replaceChildren(marker("Community"), h("p", { class: "sub" }, `${uniq.length} real renders made with OpenSfield tools. Click one to open the tool that made it.`),
    h("div", { class: "masonry" }, ...uniq.map(([u, f]) => hoverPlay(h("a", { class: "mcard", href: `#/f/${f.id}` }, exampleEl(u, "bg"),
      h("span", { class: "mcap" }, h("b", {}, f.group && f.track === "partner" ? modelName(f) : f.name), h("small", {}, f.studio)))))),
    target ? null : siteFooter());
}

/* Site map footer, like higgsfield.ai's. */
function siteFooter() {
  const col = (title, links) => h("div", { class: "fcol" }, h("b", {}, title), ...links.filter(Boolean).map(([l, href]) => h("a", { href, target: href.startsWith("http") ? "_blank" : null, rel: href.startsWith("http") ? "noopener" : null }, l)));
  const m = (id, l) => state.byId[id] && [l, `#/f/${id}`];
  return h("footer", { class: "sitefoot" },
    h("div", { class: "fbrand" }, h("b", {}, "OPEN", h("span", {}, "SFIELD")), h("small", {}, "AI-native creative suite on ComfyUI. Open source, MIT.")),
    col("Create", [["AI Video", "#/w/video/0"], ["AI Image", "#/w/image/0"], ["Edit Image", "#/w/image/1"], ["Upscale", "#/w/image/2"], ["Audio", "#/w/audio/0"], ["Elements", "#/assets"]]),
    col("Video models", [m("model.seedance2-5-i2v-1080p", "Seedance 2.5"), m("model.seedance2-0-r2v", "Seedance 2.0"), m("model.kling-v3-video", "Kling 3.0"),
      m("model.minimax-h3-max-i2v", "MiniMax H3"), m("model.wan2-6-i2v", "Wan 2.6"), m("model.grok-imagine-video-1-5", "Grok Imagine 1.5"), m("cinema.camera-rig", "LTX-2.5 (open)")]),
    col("Image models", [m("model.nano-banana-2-1-t2i", "Nano Banana 2.1"), m("model.openai-gpt-image-2-t2i", "GPT Image 2"), m("model.bfl-flux3-t2i", "FLUX 3"),
      m("model.bytedance-seedream-5-0-pro-t2i", "Seedream 5"), m("model.ideogram-v4-5-t2i", "Ideogram 4.5"), m("soul.t2i", "Z-Image (open)")]),
    col("Studios", [["Cinema Studio", "#/cinema"], ["Genjutsu", "#/s/Genjutsu"], ["Viral Hub", "#/s/Viral Hub"], ["Marketing Studio", "#/s/Marketing"], ["Soul", "#/s/Soul"], ["Match Cut", "#/s/Match Cut + Tracelab"]]),
    col("Resources", [["Blog", "#/blog"], ["Get started", "#/blog/first-video-seedance"], ["Changelog", "#/blog/changelog-oct-22"], ["Community", "#/community"], ["Credits & usage", "#/usage"],
      ["GitHub", "https://github.com/codyclack/opensfield"], ["Coverage", "https://github.com/codyclack/opensfield/blob/main/COVERAGE.md"]]),
    h("div", { class: "fbottom" }, h("small", {}, "OpenSfield is an independent open-source project for Comfy's #OpenSourceHiggsfield challenge. Not affiliated with Higgsfield AI.")));
}

/* Credits & usage (Higgsfield's credits / plans page): what each generation cost, from the costs measured per model. */
function renderUsage() {
  const rows = state.jobs.map((j) => ({ j, f: state.byId[j.feature_id], cost: state.byId[j.feature_id]?.cost || 0 }));
  const done = rows.filter((r) => r.j.status === "done");
  const total = done.reduce((s, r) => s + r.cost, 0);
  const partner = done.filter((r) => r.f && r.f.track === "partner").length;
  const stat = (label, value, sub) => h("div", { class: "ustat" }, h("small", {}, label), h("b", {}, value), sub && h("small", {}, sub));
  $("#main").replaceChildren(marker("Credits & usage"),
    h("p", { class: "sub" }, "Partner models spend your Comfy credits; open-weight tools only use GPU time. Estimates use the credits measured per model; your exact balance is on Comfy."),
    h("div", { class: "ustats" }, stat("Generations", String(state.jobs.length), `${done.length} finished`), stat("Partner-model runs", String(partner)),
      stat("Estimated credits", `✦ ${Math.round(total)}`, "for models with a measured cost"),
      h("a", { class: "ustat link", href: "https://platform.comfy.org", target: "_blank", rel: "noopener" }, h("small", {}, "Balance and plans"), h("b", {}, "Comfy platform ↗"), h("small", {}, "Add credits or change plan"))),
    h("div", { class: "ulinks" }, h("a", { class: "ghost", href: "#/community" }, "Community"), h("a", { class: "ghost", href: "#/blog" }, "Tutorials"),
      h("a", { class: "ghost", href: "https://form.typeform.com/to/V1dSQrkS", target: "_blank", rel: "noopener" }, "#OpenSourceHiggsfield contest")),
    rows.length ? h("table", { class: "utable" }, h("thead", {}, h("tr", {}, ...["When", "Tool", "Model", "Status", "Est. credits"].map((t) => h("th", {}, t)))),
      h("tbody", {}, ...rows.map(({ j, f, cost }) => h("tr", {}, h("td", {}, new Date(j.created * 1000).toLocaleString()), h("td", {}, h("a", { href: `#/f/${j.feature_id}` }, j.feature_name)),
        h("td", {}, f ? (f.engine || (f.track === "partner" ? "partner" : "open weights")) : "-"), h("td", {}, j.status), h("td", {}, cost ? `✦ ${cost}` : f && f.track !== "partner" ? "GPU only" : "-")))))
      : h("div", { class: "gempty" }, h("b", {}, "No generations yet"), h("small", {}, "Run any tool and its cost shows up here.")),
    siteFooter());
  document.title = "Credits & usage · OpenSfield";
}

/* Apps (higgsfield.ai/apps): one-click effects by category, each opening the tool that runs it. */
const appSlug = (c) => c.toLowerCase().replace(/[^a-z]+/g, "-").replace(/^-|-$/g, "");
async function loadApps() {
  if (!state.apps) state.apps = await api("/api/apps");
  return state.apps;
}
function appCard(a) {
  const f = state.byId[a.feature];
  const cover = (a.examples || []).find((u) => isVideo(u) || isImage(u)) || (f && (f.examples || []).find((u) => isVideo(u) || isImage(u)));
  return hoverPlay(h("a", { class: "appcard", href: `#/f/${a.feature}`, style: `--h:${hash(a.slug) % 360}`,
    onclick: () => { if (Object.keys(a.preset || {}).length) state.prefill = { feature_id: a.feature, inputs: a.preset }; } },
    h("span", { class: "appart" }, cover ? exampleEl(cover, "bg") : h("span", { class: "appglyph" }, a.name.slice(0, 1)),
      a.tag && h("span", { class: `tag t-${a.tag.toLowerCase()}` }, a.tag),
      h("span", { class: "appkind" }, a.output_kind === "video" ? "▶ VIDEO" : a.output_kind === "image" ? "▣ IMAGE" : a.output_kind.toUpperCase())),
    h("b", {}, a.name), h("small", {}, a.desc), h("span", { class: "trynow" }, "Try now")));
}
async function renderApps(cat) {
  const main = $("#main");
  let data;
  try { data = await loadApps(); } catch (e) { main.replaceChildren(h("p", { class: "err" }, e.message)); return; }
  const current = data.categories.find((c) => appSlug(c) === cat);
  const tabs = h("div", { class: "wtabs apptabs", role: "tablist" }, h("a", { role: "tab", href: "#/apps", "aria-selected": String(!current) }, "All"),
    ...data.categories.map((c) => h("a", { role: "tab", href: `#/apps/${appSlug(c)}`, "aria-selected": String(current === c) }, c)));
  const rows = (current ? [current] : data.categories).map((c) => {
    const list = data.apps.filter((a) => a.cat === c);
    return h("section", { class: "row" }, h("div", { class: "rowhead" }, h("h3", {}, c), !current && h("a", { class: "more", href: `#/apps/${appSlug(c)}` }, `See all ${list.length} →`)),
      h("div", { class: current ? "appgrid" : "strip apps" }, (current ? list : list.slice(0, 8)).map(appCard)));
  });
  main.replaceChildren(h("div", { class: "appshero" }, h("h1", {}, "WELCOME TO ", h("span", {}, "OPENSFIELD APPS")),
    h("p", {}, `${data.apps.length} one-click effects that turn any photo or clip into ads, viral trends and art. Each runs on a partner model by default with an open-weights version in the model picker.`)),
  tabs, ...rows, siteFooter());
  document.title = `${current || "Apps"} · OpenSfield`;
}
