// LipiSetu demo page. Plain JavaScript, no framework.
// Everything shown comes from the backend (app/server.py), which calls the real engine.

const SYSTEM_ORDER = ["B0", "B1", "B1N", "B2", "V1", "S0", "S1", "S2", "S3", "D0", "D1", "H1", "L1", "G1"];
const SYSTEM_LABELS = {
  B0: "Raw tokens, BM25", B1: "BM25 + stemming", B1N: "BM25, no stemming", B2: "Transliterate + BM25",
  V1: "tf-idf lnc.ltc", S0: "+ Soundex zone", S1: "+ Dhvani zone", S2: "+ pooled df", S3: "+ title, proximity",
  D0: "e5-small dense", D1: "SCD encoder", H1: "Hybrid (RRF)", L1: "Learning to rank", G1: "Gated cascade",
};
const FORMS = [
  { code: "F1", name: "Devanagari", color: "--series-1" },
  { code: "F2", name: "Standard Roman", color: "--series-2" },
  { code: "F3", name: "Casual Roman", color: "--series-3" },
];
const EXAMPLES = [
  "kal ka mausam kaisa rahega",
  "भारत का संविधान कब लागू हुआ",
  "bharat ka samvidhan kab lagu hua",
  "congress party ka leader kaun hai",
  "गूगल की खोज किसने की",
  "taj mahal kisne banwaya",
];
const BRIDGE_GROUPS = [
  ["mausam", "mosam", "मौसम", "mousam"],
  ["samvidhan", "sanvidhaan", "संविधान", "samvidhaan"],
  ["zindagi", "jindagi", "ज़िंदगी", "zindgi"],
  ["krishna", "krishn", "कृष्ण", "krisna"],
  ["gyan", "gyaan", "ज्ञान", "gyaana"],
];
const STATIONS = [
  ["01", "Tokenise", "Split by script with explicit Unicode ranges, so vowel signs stay inside their word.", "text/tokenize.py"],
  ["02", "Normalise and stem", "NFC, nukta and nasal folding, case folding, stop words, a light Hindi suffix stemmer.", "text/normalize.py · stemmer.py"],
  ["03", "Dhvani key", "Each word becomes a phonetic key shared by its Devanagari and Roman spellings.", "text/dhvani.py"],
  ["04", "Inverted index", "Positional postings in zones: surface, title, Dhvani. Champion lists and skip pointers.", "index/inverted_index.py"],
  ["05", "Score", "BM25 per zone with pooled df across spellings, then query-term proximity on the top 100.", "retrieval/bm25.py · proximity.py"],
  ["06", "Gate", "A small model reads IR signals and decides whether the neural stage is worth running.", "cascade/gate.py"],
  ["07", "Dense and fuse", "A distilled, int8 query encoder searches passage vectors; ranks merge with RRF.", "dense/scd.py · retrieval/rrf.py"],
];

let currentSystem = "S3";
let systemsInfo = [];

// ---------- small helpers ----------
function $(id) { return document.getElementById(id); }

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function hasDevanagari(text) { return /[ऀ-ॿ]/.test(text); }

function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

function fmt(value, digits) {
  const number = Number(value);
  if (Number.isNaN(number)) return "—";
  return number.toFixed(digits === undefined ? 3 : digits);
}

async function getJson(url) {
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "request failed");
  return data;
}

// ---------- theme ----------
function initTheme() {
  let saved = null;
  try { saved = localStorage.getItem("lipisetu-theme"); } catch (e) { saved = null; }
  if (saved) document.documentElement.setAttribute("data-theme", saved);
  updateThemeLabel();
  $("themeToggle").addEventListener("click", function () {
    const dark = isDark();
    const next = dark ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("lipisetu-theme", next); } catch (e) { /* storage not available */ }
    updateThemeLabel();
    if (window.lastResults) renderEvidence(window.lastResults);
  });
}

function isDark() {
  const attr = document.documentElement.getAttribute("data-theme");
  if (attr) return attr === "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function updateThemeLabel() { $("themeLabel").textContent = isDark() ? "Light" : "Dark"; }

// ---------- the bridge illustration ----------
function drawBridgeLines() {
  const svg = $("bridgeLines");
  const narrow = window.innerWidth <= 560;
  let paths = "";
  const starts = narrow ? [150, 450, 150, 450] : [75, 225, 375, 525];
  for (let i = 0; i < 4; i++) {
    const x = starts[i];
    paths += '<path d="M ' + x + ' 0 C ' + x + ' 34, 300 30, 300 64" />';
  }
  svg.innerHTML = paths;
}

async function initBridge() {
  drawBridgeLines();
  window.addEventListener("resize", drawBridgeLines);
  const groups = [];
  for (const words of BRIDGE_GROUPS) {
    try {
      const keys = await getJson("/api/dhvani?words=" + encodeURIComponent(words.join(",")));
      groups.push(keys);
    } catch (e) { /* server not ready */ }
  }
  if (groups.length === 0) return;
  let index = 0;
  showBridgeGroup(groups[0]);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduceMotion) return;
  setInterval(function () {
    index = (index + 1) % groups.length;
    const items = document.querySelectorAll(".bridge-word, .bridge-key-value");
    items.forEach(function (item) { item.classList.add("fading"); });
    setTimeout(function () { showBridgeGroup(groups[index]); }, 360);
  }, 3800);
}

function showBridgeGroup(group) {
  let html = "";
  let key = "";
  for (const item of group) {
    const lang = hasDevanagari(item.word) ? ' lang="hi"' : "";
    html += '<span class="bridge-word"' + lang + ' title="Dhvani key: ' + escapeHtml(item.key) + '">' + escapeHtml(item.word) + "</span>";
    if (hasDevanagari(item.word)) key = item.key;
  }
  $("bridgeWords").innerHTML = html;
  $("bridgeKey").textContent = key.split("").join(" ");
  $("bridgeKey").classList.remove("fading");
}

// ---------- search controls ----------
function renderExamples() {
  let html = "";
  for (const text of EXAMPLES) {
    const lang = hasDevanagari(text) ? ' lang="hi"' : "";
    html += '<button type="button" class="example"' + lang + ">" + escapeHtml(text) + "</button>";
  }
  $("examples").innerHTML = html;
  document.querySelectorAll(".example").forEach(function (button) {
    button.addEventListener("click", function () {
      $("query").value = button.textContent;
      runSearch();
    });
  });
}

async function renderSystemPicker() {
  try {
    systemsInfo = await getJson("/api/systems");
  } catch (e) {
    systemsInfo = [{ code: "S3", name: "LipiSetu (sparse)", available: true }];
  }
  let html = "";
  for (const system of systemsInfo) {
    const checked = system.code === currentSystem ? "true" : "false";
    const disabled = system.available ? "" : " disabled title=\"Not built yet\"";
    html += '<button type="button" role="radio" aria-checked="' + checked + '" data-code="' + system.code + '"' + disabled + ">"
      + escapeHtml(system.name) + '<span class="code">' + system.code + "</span></button>";
  }
  $("systemPicker").innerHTML = html;
  document.querySelectorAll("#systemPicker button").forEach(function (button) {
    button.addEventListener("click", function () {
      currentSystem = button.dataset.code;
      document.querySelectorAll("#systemPicker button").forEach(function (b) {
        b.setAttribute("aria-checked", b === button ? "true" : "false");
      });
      if ($("query").value.trim()) runSearch();
    });
  });
}

// ---------- search ----------
async function runSearch() {
  const query = $("query").value.trim();
  if (!query) return;
  $("resultsSection").hidden = false;
  $("resultsColumns").innerHTML = '<p class="empty">Searching…</p>';
  const compare = $("compareToggle").checked && currentSystem !== "B2";
  try {
    const main = await getJson("/api/search?q=" + encodeURIComponent(query) + "&system=" + currentSystem);
    let baseline = null;
    if (compare) baseline = await getJson("/api/search?q=" + encodeURIComponent(query) + "&system=B2");
    renderColumns(main, baseline);
    renderTrace(main);
    renderConsistency(query);
  } catch (error) {
    $("resultsColumns").innerHTML = '<p class="empty">' + escapeHtml(error.message) + "</p>";
    $("trace").innerHTML = "";
  }
}

function systemName(code) {
  for (const system of systemsInfo) if (system.code === code) return system.name;
  return SYSTEM_LABELS[code] || code;
}

function renderColumns(main, baseline) {
  let html = "";
  if (baseline) html += renderColumn(baseline, "Baseline");
  html += renderColumn(main, "");
  $("resultsColumns").innerHTML = html;
  $("resultsColumns").classList.toggle("two", baseline !== null);
  $("resultsColumns").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderColumn(data, label) {
  const title = (label ? label + " · " : "") + systemName(data.system);
  let html = '<div class="column">';
  html += '<div class="column-head"><span class="column-title">' + escapeHtml(title) + "</span>"
    + '<span class="column-meta">' + data.results.length + " passages · " + data.took_ms + " ms</span></div>";
  const hasZones = data.results.length > 0 && data.results[0].breakdown && data.results[0].breakdown.all !== undefined;
  if (hasZones) {
    html += '<div class="breakdown-legend"><span><span class="swatch" style="background:var(--series-1)"></span>surface BM25</span>'
      + '<span><span class="swatch" style="background:var(--series-2)"></span>Dhvani zone</span>'
      + '<span><span class="swatch" style="background:var(--series-3)"></span>title + proximity</span></div>';
  }
  if (data.results.length === 0) html += '<p class="empty">Nothing matched.</p>';
  let top = 0;
  for (const result of data.results) top = Math.max(top, partsTotal(result.breakdown));
  for (const result of data.results) html += renderResult(result, top);
  html += "</div>";
  return html;
}

function partsTotal(b) {
  if (!b) return 0;
  return (b.all || 0) + (b.dhvani || 0) + (b.title || 0) + (b.proximity || 0);
}

function renderResult(result, top) {
  let snippet = "";
  for (const piece of result.snippet) {
    snippet += piece.hit ? '<span class="hit">' + escapeHtml(piece.text) + "</span> " : escapeHtml(piece.text) + " ";
  }
  let html = '<article class="result">';
  html += '<div class="result-rank">' + String(result.rank).padStart(2, "0") + "</div>";
  html += '<div class="result-head"><span class="result-title" lang="hi">' + escapeHtml(result.title) + "</span>"
    + '<span class="result-id">' + escapeHtml(result.docid) + "</span></div>";
  html += '<p class="result-snippet" lang="hi">' + snippet + "</p>";
  html += '<div class="result-score">' + scoreBar(result.breakdown, top) + '<span class="score-text">' + scoreText(result) + "</span></div>";
  html += "</article>";
  return html;
}

function scoreBar(b, top) {
  if (!b || b.all === undefined || top <= 0) return "";
  const parts = [
    ["--series-1", b.all || 0, "surface BM25"],
    ["--series-2", b.dhvani || 0, "Dhvani zone"],
    ["--series-3", (b.title || 0) + (b.proximity || 0), "title + proximity"],
  ];
  let html = '<span class="score-bar">';
  for (const part of parts) {
    if (part[1] <= 0) continue;
    const width = Math.max(2, (part[1] / top) * 100);
    html += '<span style="width:' + width + '%;background:var(' + part[0] + ')" title="' + part[2] + ": " + fmt(part[1], 2) + '"></span>';
  }
  return html + "</span>";
}

function scoreText(result) {
  const b = result.breakdown || {};
  if (b.all === undefined) return "score " + fmt(result.score, 4);
  let text = "surface " + fmt(b.all, 2) + " · dhvani " + fmt(b.dhvani || 0, 2);
  if (b.title !== undefined) text += " · title " + fmt(b.title, 2);
  if (b.proximity !== undefined) text += " · prox " + fmt(b.proximity, 2) + " (w " + b.window + ")";
  return text;
}

// ---------- trace panel ----------
function renderTrace(data) {
  const ex = data.explain || {};
  let html = "";
  let step = 1;
  function stepHead(title) { return '<h4><span class="num">' + String(step++).padStart(2, "0") + "</span>" + title + "</h4>"; }

  if (ex.tokens && ex.tokens.length) {
    html += '<div class="trace-step">' + stepHead("Tokens · script " + escapeHtml(ex.script));
    html += '<div class="scroll-x"><table><thead><tr><th>token</th><th>script</th><th>stem</th><th class="mono">dhvani</th></tr></thead><tbody>';
    for (const t of ex.tokens) {
      html += "<tr" + (t.stop ? ' class="stop" title="stop word"' : "") + "><td>" + escapeHtml(t.token) + '</td><td><span class="tag">' + t.script + "</span></td><td>"
        + escapeHtml(t.stop ? "—" : t.stem) + '</td><td class="mono">' + escapeHtml(t.stop ? "—" : (t.dhvani || "·")) + "</td></tr>";
    }
    html += "</tbody></table></div></div>";
  }

  const zoneNames = { all: "surface", dhvani: "Dhvani", title: "title" };
  const zoneKeys = Object.keys(ex.zones || {});
  if (zoneKeys.length) {
    let maxIdf = 0;
    for (const z of zoneKeys) for (const row of ex.zones[z]) maxIdf = Math.max(maxIdf, row.idf || 0);
    html += '<div class="trace-step">' + stepHead("Term statistics · BM25 idf");
    html += '<div class="scroll-x"><table><thead><tr><th>zone</th><th>term</th><th class="num">df</th><th class="num">idf</th><th></th></tr></thead><tbody>';
    for (const z of zoneKeys) {
      if (z === "title") continue;
      for (const row of ex.zones[z]) {
        const width = maxIdf > 0 ? Math.round(((row.idf || 0) / maxIdf) * 60) : 0;
        html += "<tr><td>" + zoneNames[z] + "</td><td" + (z === "dhvani" ? ' class="mono"' : "") + ">" + escapeHtml(row.term) + '</td><td class="num">'
          + (row.df || 0).toLocaleString() + '</td><td class="num">' + fmt(row.idf || 0, 2) + '</td><td><span class="idf-bar" style="width:' + width + 'px"></span></td></tr>';
      }
    }
    html += "</tbody></table></div></div>";
  }

  if (ex.pooled && ex.pooled.length) {
    html += '<div class="trace-step">' + stepHead("Pooled df · Pirkola-style");
    html += '<table><thead><tr><th>term</th><th class="num">own df</th><th class="num">pooled df</th></tr></thead><tbody>';
    for (const row of ex.pooled) {
      html += "<tr><td>" + escapeHtml(row.term) + '</td><td class="num">' + row.own_df.toLocaleString() + '</td><td class="num">' + row.pooled_df.toLocaleString() + "</td></tr>";
    }
    html += "</tbody></table></div>";
  }

  if (ex.postings && ex.postings.length) {
    html += '<div class="trace-step">' + stepHead("Postings · Dhvani zone");
    for (const p of ex.postings) {
      let sample = "";
      for (const s of p.sample) sample += escapeHtml(s.doc) + " tf " + s.tf + " @" + s.positions.join(",") + "  ";
      html += '<div class="posting"><b>' + escapeHtml(p.key) + "</b> df " + p.df.toLocaleString() + " → " + sample + "</div>";
    }
    html += "</div>";
  }

  if (ex.gate) {
    const g = ex.gate;
    html += '<div class="trace-step">' + stepHead("Gate · run the neural stage?");
    html += '<div class="meter" title="probability ' + fmt(g.probability, 2) + ", threshold " + fmt(g.threshold, 2) + '">'
      + '<div class="meter-fill" style="width:' + Math.round(g.probability * 100) + '%"></div>'
      + '<div class="meter-tick" style="left:calc(' + Math.round(g.threshold * 100) + '% - 1px)"></div></div>';
    html += '<p class="gate-decision">' + (g.use_neural
      ? "<b>Yes.</b> Probability " + fmt(g.probability, 2) + " is above the threshold " + fmt(g.threshold, 2) + ", so the dense stage ran and the lists were fused."
      : "<b>No.</b> Probability " + fmt(g.probability, 2) + " is below the threshold " + fmt(g.threshold, 2) + ", so the sparse result was returned without neural inference.") + "</p>";
    html += '<div class="posting">';
    for (const name in g.features) html += escapeHtml(name) + " " + fmt(g.features[name], 2) + " · ";
    html += "</div></div>";
  }

  html += '<div class="trace-foot">' + escapeHtml(systemName(data.system)) + " · " + data.took_ms + " ms</div>";
  $("trace").innerHTML = html;
}

// ---------- same question, other script ----------
async function renderConsistency(query) {
  const box = $("consistency");
  box.hidden = true;
  if (!hasDevanagari(query)) return;
  try {
    const data = await getJson("/api/consistency?q=" + encodeURIComponent(query) + "&system=" + currentSystem);
    if (!data.available || data.systems.length === 0) return;
    let html = '<span class="label">Same question in Roman</span><span class="roman">' + escapeHtml(data.roman) + "</span>";
    for (const s of data.systems) {
      html += "<span>" + escapeHtml(s.name) + ': top-10 overlap <span class="value">RBO ' + fmt(s.rbo, 2) + "</span> (" + s.shared_top10 + "/10 shared)</span>";
    }
    html += '<button type="button" id="tryRoman">Search the Roman version</button>';
    box.innerHTML = html;
    box.hidden = false;
    $("tryRoman").addEventListener("click", function () {
      $("query").value = data.roman;
      runSearch();
    });
  } catch (e) { box.hidden = true; }
}

// ---------- pipeline ----------
function renderStations() {
  let html = "";
  for (const s of STATIONS) {
    html += '<li class="station"><div class="station-num">' + s[0] + '</div><div class="station-name">' + s[1]
      + '</div><p class="station-text">' + s[2] + '</p><div class="station-file">' + s[3] + "</div></li>";
  }
  $("line").innerHTML = html;
}

// ---------- evidence ----------
async function loadEvidence() {
  try {
    const data = await getJson("/api/results");
    window.lastResults = data;
    renderEvidence(data);
  } catch (e) {
    $("evidenceNote").textContent = "Results could not be loaded.";
  }
}

function metricValue(rows, system, form, metric) {
  for (const row of rows) {
    if (row.system === system && row.query_form === form && row.metric === metric) return Number(row.value);
  }
  return null;
}

function findRow(rows, key, value) {
  for (const row of rows) if (row[key] === value) return row;
  return null;
}

function renderEvidence(data) {
  renderTiles(data);
  renderSystemsChart(data.main || []);
  renderBudgetChart(data.budget || [], data.operating_point);
  renderAblation(data.ablation || []);
  renderEfficiency(data.efficiency || []);
}

function tile(label, value, compare) {
  return '<div class="tile"><p class="tile-label">' + label + '</p><div class="tile-value">' + value + '</div><div class="tile-compare">' + compare + "</div></div>";
}

function renderTiles(data) {
  const inv = data.invariance || [];
  const base = findRow(inv, "system", "B2");
  const ours = findRow(inv, "system", "S3");
  let html = "";
  if (base && ours) {
    html += tile("Script Gap on casual Roman (nDCG@10)", fmt(ours.gap_F3, 3),
      'baseline <span class="from">' + fmt(base.gap_F3, 3) + "</span> · lower is better");
    html += tile("Cross-script consistency (CSC@10, RBO)", fmt(ours["csc@10"], 2),
      'baseline <span class="from">' + fmt(base["csc@10"], 2) + "</span> · 1.0 = same ranking in every script");
  } else {
    html += tile("Script Gap on casual Roman", "—", "not run yet") + tile("Cross-script consistency", "—", "not run yet");
  }
  const op = data.operating_point;
  if (op) {
    html += tile("Queries that needed the neural stage", Math.round(op.gate_neural_share * 100) + "%",
      "nDCG@10 " + fmt(op.gate_ndcg_at_10 !== undefined ? op.gate_ndcg_at_10 : op["gate_ndcg@10"], 3) + " vs " + fmt(op["always_neural_ndcg@10"], 3) + " always-neural");
  } else {
    html += tile("Queries that needed the neural stage", "—", "not run yet");
  }
  const scd = data.scd;
  if (scd && scd.size_mb) {
    html += tile("Query encoder size", Math.round(scd.size_mb.pruned_int8) + " MB",
      'from <span class="from">' + Math.round(scd.size_mb.full_fp32) + " MB</span> · vocabulary pruned + int8");
  } else {
    html += tile("Query encoder size", "—", "not trained yet");
  }
  $("tiles").innerHTML = html;
}

function legendHtml(items) {
  let html = "";
  for (const item of items) {
    html += '<span><span class="swatch" style="background:var(' + item.color + ')"></span>' + escapeHtml(item.name) + "</span>";
  }
  return html;
}

// Grouped columns: one group per system, one column per query script.
function renderSystemsChart(rows) {
  const systems = [];
  for (const code of SYSTEM_ORDER) if (metricValue(rows, code, "F1", "ndcg@10") !== null) systems.push(code);
  if (systems.length === 0) { $("chartSystems").innerHTML = '<p class="empty">Not run yet.</p>'; return; }
  $("systemsLegend").innerHTML = legendHtml(FORMS);

  const width = Math.max(640, systems.length * 76);
  const height = 300;
  const left = 40, right = 8, top = 14, bottom = 44;
  let maxValue = 0;
  for (const s of systems) for (const f of FORMS) maxValue = Math.max(maxValue, metricValue(rows, s, f.code, "ndcg@10") || 0);
  const yMax = Math.ceil(maxValue * 10) / 10;
  const plotH = height - top - bottom;
  const groupW = (width - left - right) / systems.length;
  const barW = Math.min(18, (groupW - 16) / 3 - 2);
  function y(v) { return top + plotH - (v / yMax) * plotH; }

  let svg = '<svg viewBox="0 0 ' + width + " " + height + '" style="min-width:' + width + 'px" role="img" aria-label="nDCG@10 by system and query script">';
  for (let t = 0; t <= yMax + 1e-9; t += 0.1) {
    svg += '<line class="grid-line" x1="' + left + '" x2="' + (width - right) + '" y1="' + y(t) + '" y2="' + y(t) + '"/>';
    svg += '<text x="' + (left - 8) + '" y="' + (y(t) + 4) + '" text-anchor="end">' + t.toFixed(1) + "</text>";
  }
  svg += '<line class="axis-line" x1="' + left + '" x2="' + (width - right) + '" y1="' + y(0) + '" y2="' + y(0) + '"/>';
  systems.forEach(function (s, i) {
    const groupX = left + i * groupW + (groupW - (barW * 3 + 4)) / 2;
    FORMS.forEach(function (f, j) {
      const v = metricValue(rows, s, f.code, "ndcg@10") || 0;
      const x = groupX + j * (barW + 2);
      const h = y(0) - y(v);
      const r = Math.min(4, h, barW / 2);
      svg += '<path d="' + roundedTop(x, y(v), barW, h, r) + '" fill="var(' + f.color + ')" data-tip="' + escapeHtml(s + " · " + SYSTEM_LABELS[s] + "<br>" + f.name + ": nDCG@10 " + fmt(v, 3)) + '"/>';
      svg += '<rect x="' + (x - 1) + '" y="' + top + '" width="' + (barW + 2) + '" height="' + plotH + '" fill="transparent" data-tip="' + escapeHtml(s + " · " + SYSTEM_LABELS[s] + "<br>" + f.name + ": nDCG@10 " + fmt(v, 3)) + '"/>';
    });
    const cx = left + i * groupW + groupW / 2;
    const strong = (s === "S3" || s === "G1") ? ' class="label-strong"' : "";
    svg += '<text x="' + cx + '" y="' + (height - bottom + 18) + '" text-anchor="middle"' + strong + ">" + s + "</text>";
    svg += '<text x="' + cx + '" y="' + (height - bottom + 33) + '" text-anchor="middle" style="font-size:10.5px">' + escapeHtml(shortLabel(s)) + "</text>";
  });
  svg += "</svg>";
  $("chartSystems").innerHTML = '<div class="scroll-x">' + svg + "</div>";
  attachTooltips($("chartSystems"));

  let table = '<table class="data-table"><thead><tr><th>system</th><th></th>';
  for (const f of FORMS) table += '<th class="num">' + f.name + "</th>";
  table += "</tr></thead><tbody>";
  for (const s of systems) {
    table += "<tr><td>" + s + "</td><td>" + escapeHtml(SYSTEM_LABELS[s]) + "</td>";
    for (const f of FORMS) table += '<td class="num">' + fmt(metricValue(rows, s, f.code, "ndcg@10"), 3) + "</td>";
    table += "</tr>";
  }
  $("chartSystemsTable").innerHTML = table + "</tbody></table>";
}

function shortLabel(code) {
  const labels = { B0: "raw", B1: "BM25", B1N: "no stem", B2: "translit", V1: "tf-idf", S0: "Soundex", S1: "Dhvani",
    S2: "pooled df", S3: "zones+prox", D0: "e5", D1: "SCD", H1: "hybrid", L1: "LTR", G1: "cascade" };
  return labels[code] || "";
}

// A column with a 4px rounded top and a square base on the baseline.
function roundedTop(x, yTop, w, h, r) {
  if (h <= 0) return "";
  return "M" + x + "," + (yTop + h) + " V" + (yTop + r) + " Q" + x + "," + yTop + " " + (x + r) + "," + yTop
    + " H" + (x + w - r) + " Q" + (x + w) + "," + yTop + " " + (x + w) + "," + (yTop + r) + " V" + (yTop + h) + " Z";
}

// Line chart: gate vs random gate, x = share of queries using the neural stage.
function renderBudgetChart(rows, op) {
  if (rows.length === 0) { $("chartBudget").innerHTML = '<p class="empty">Not run yet.</p>'; return; }
  const series = [
    { name: "Learned gate", key: "gate_ndcg@10", color: "--series-1" },
    { name: "Random gate, same budget", key: "random_ndcg@10", color: "--series-2" },
  ];
  $("budgetLegend").innerHTML = legendHtml(series);
  const points = rows.map(function (r) {
    return { x: Number(r.neural_share), gate: Number(r["gate_ndcg@10"]), random: Number(r["random_ndcg@10"]) };
  }).sort(function (a, b) { return a.x - b.x; });

  const width = 760, height = 300, left = 48, right = 16, top = 16, bottom = 40;
  let lo = Infinity, hi = -Infinity;
  for (const p of points) { lo = Math.min(lo, p.gate, p.random); hi = Math.max(hi, p.gate, p.random); }
  lo = Math.floor(lo * 100) / 100; hi = Math.ceil(hi * 100) / 100;
  if (hi - lo < 0.02) { hi += 0.01; lo -= 0.01; }
  function x(v) { return left + v * (width - left - right); }
  function y(v) { return top + (height - top - bottom) * (1 - (v - lo) / (hi - lo)); }

  let svg = '<svg viewBox="0 0 ' + width + " " + height + '" role="img" aria-label="nDCG@10 against share of queries using the neural stage">';
  const step = (hi - lo) / 4;
  for (let i = 0; i <= 4; i++) {
    const v = lo + i * step;
    svg += '<line class="grid-line" x1="' + left + '" x2="' + (width - right) + '" y1="' + y(v) + '" y2="' + y(v) + '"/>';
    svg += '<text x="' + (left - 8) + '" y="' + (y(v) + 4) + '" text-anchor="end">' + v.toFixed(3) + "</text>";
  }
  for (let i = 0; i <= 4; i++) {
    svg += '<text x="' + x(i / 4) + '" y="' + (height - bottom + 20) + '" text-anchor="middle">' + (i * 25) + "%</text>";
  }
  svg += '<text x="' + ((left + width - right) / 2) + '" y="' + (height - 4) + '" text-anchor="middle">queries that run the neural stage</text>';
  svg += '<line class="axis-line" x1="' + left + '" x2="' + (width - right) + '" y1="' + (height - bottom) + '" y2="' + (height - bottom) + '"/>';
  const keys = [["random", "--series-2"], ["gate", "--series-1"]];
  for (const k of keys) {
    let d = "";
    points.forEach(function (p, i) { d += (i === 0 ? "M" : " L") + x(p.x).toFixed(1) + "," + y(p[k[0]]).toFixed(1); });
    svg += '<path d="' + d + '" fill="none" stroke="var(' + k[1] + ')" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>';
  }
  if (op) {
    const ox = x(op.gate_neural_share), oy = y(op["gate_ndcg@10"]);
    svg += '<circle cx="' + ox + '" cy="' + oy + '" r="5" fill="var(--series-1)" stroke="var(--surface)" stroke-width="2"/>';
    const anchor = op.gate_neural_share > 0.6 ? "end" : "start";
    const dx = anchor === "end" ? -10 : 10;
    svg += '<text class="label-strong" x="' + (ox + dx) + '" y="' + (oy - 10) + '" text-anchor="' + anchor + '">threshold from train: '
      + Math.round(op.gate_neural_share * 100) + "% neural, nDCG " + fmt(op["gate_ndcg@10"], 3) + "</text>";
  }
  svg += '<line id="crosshair" class="axis-line" x1="0" x2="0" y1="' + top + '" y2="' + (height - bottom) + '" visibility="hidden"/>';
  svg += '<rect id="budgetHit" x="' + left + '" y="' + top + '" width="' + (width - left - right) + '" height="' + (height - top - bottom) + '" fill="transparent"/>';
  svg += "</svg>";
  $("chartBudget").innerHTML = svg;

  const hit = $("budgetHit");
  const tip = $("tooltip");
  hit.addEventListener("mousemove", function (event) {
    const svgEl = $("chartBudget").querySelector("svg");
    const box = svgEl.getBoundingClientRect();
    const share = Math.min(1, Math.max(0, ((event.clientX - box.left) / box.width * width - left) / (width - left - right)));
    let nearest = points[0];
    for (const p of points) if (Math.abs(p.x - share) < Math.abs(nearest.x - share)) nearest = p;
    const cross = $("crosshair");
    cross.setAttribute("x1", x(nearest.x)); cross.setAttribute("x2", x(nearest.x)); cross.setAttribute("visibility", "visible");
    tip.innerHTML = Math.round(nearest.x * 100) + "% of queries use neural<br>Learned gate: " + fmt(nearest.gate, 3) + "<br>Random gate: " + fmt(nearest.random, 3);
    tip.hidden = false;
    placeTooltip(event);
  });
  hit.addEventListener("mouseleave", function () { tip.hidden = true; $("crosshair").setAttribute("visibility", "hidden"); });

  let table = '<table class="data-table"><thead><tr><th class="num">neural share</th><th class="num">learned gate</th><th class="num">random gate</th></tr></thead><tbody>';
  for (const p of points) table += '<tr><td class="num">' + Math.round(p.x * 100) + '%</td><td class="num">' + fmt(p.gate, 4) + '</td><td class="num">' + fmt(p.random, 4) + "</td></tr>";
  $("chartBudgetTable").innerHTML = table + "</tbody></table>";
}

function renderAblation(rows) {
  if (rows.length === 0) { $("ablationTable").innerHTML = '<p class="empty">Not run yet.</p>'; return; }
  let best = -1;
  for (const r of rows) best = Math.max(best, Number(r["csc@10"]));
  let html = '<table class="data-table"><thead><tr><th>variant</th><th class="num">keys</th><th class="num">words per key</th>'
    + '<th class="num">nDCG Devanagari</th><th class="num">nDCG Roman</th><th class="num">nDCG casual</th><th class="num">CSC@10</th></tr></thead><tbody>';
  rows.forEach(function (r, i) {
    html += "<tr" + (i === 0 ? ' class="emphasis"' : "") + "><td>" + escapeHtml(r.variant) + '</td><td class="num">' + Number(r.distinct_keys).toLocaleString()
      + '</td><td class="num">' + fmt(r.surface_words_per_key, 2) + '</td><td class="num">' + fmt(r["ndcg@10_F1"], 3) + '</td><td class="num">' + fmt(r["ndcg@10_F2"], 3)
      + '</td><td class="num">' + fmt(r["ndcg@10_F3"], 3) + '</td><td class="num' + (Number(r["csc@10"]) === best ? " best" : "") + '">' + fmt(r["csc@10"], 3) + "</td></tr>";
  });
  $("ablationTable").innerHTML = html + "</tbody></table>";
}

function renderEfficiency(rows) {
  if (rows.length === 0) { $("efficiencyTable").innerHTML = '<p class="empty">Not run yet.</p>'; return; }
  let html = '<table class="data-table"><thead><tr><th>system</th><th></th><th class="num">median ms</th><th class="num">p95 ms</th></tr></thead><tbody>';
  for (const code of SYSTEM_ORDER) {
    const r = findRow(rows, "system", code);
    if (!r) continue;
    html += "<tr><td>" + code + "</td><td>" + escapeHtml(SYSTEM_LABELS[code]) + '</td><td class="num">' + fmt(r.median_ms, 1) + '</td><td class="num">' + fmt(r.p95_ms, 1) + "</td></tr>";
  }
  $("efficiencyTable").innerHTML = html + "</tbody></table>";
}

// ---------- tooltips ----------
function attachTooltips(container) {
  const tip = $("tooltip");
  container.querySelectorAll("[data-tip]").forEach(function (element) {
    element.addEventListener("mousemove", function (event) {
      tip.innerHTML = element.getAttribute("data-tip");
      tip.hidden = false;
      placeTooltip(event);
    });
    element.addEventListener("mouseleave", function () { tip.hidden = true; });
  });
}

function placeTooltip(event) {
  const tip = $("tooltip");
  const x = Math.min(window.innerWidth - tip.offsetWidth - 12, event.clientX + 14);
  const y = Math.max(8, event.clientY - tip.offsetHeight - 12);
  tip.style.left = x + "px";
  tip.style.top = y + "px";
}

function initTableToggles() {
  document.querySelectorAll("[data-table]").forEach(function (button) {
    button.addEventListener("click", function () {
      const table = $(button.dataset.table);
      table.hidden = !table.hidden;
      button.textContent = table.hidden ? "Show table" : "Hide table";
    });
  });
}

// ---------- start ----------
document.addEventListener("DOMContentLoaded", function () {
  initTheme();
  renderExamples();
  renderStations();
  initTableToggles();
  renderSystemPicker();
  initBridge();
  loadEvidence();
  $("searchForm").addEventListener("submit", function (event) {
    event.preventDefault();
    runSearch();
  });
});
