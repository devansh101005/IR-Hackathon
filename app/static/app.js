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
// [number, name, what it does, lecture topic, file]
const STATIONS = [
  ["01", "Tokenise", "Split the text into words, script by script, so Hindi vowel signs stay inside their word.", "Lecture: term vocabulary", "text/tokenize.py"],
  ["02", "Normalise and stem", "Unicode clean-up, lower case, remove stop words (ka, hai, ...), cut common Hindi suffixes.", "Lecture: term vocabulary", "text/normalize.py · stemmer.py"],
  ["03", "Dhvani key", "Turn each word into a sound key that is the same for its Devanagari and Roman spellings.", "Lecture: Soundex (our version)", "text/dhvani.py"],
  ["04", "Inverted index", "For every term, a postings list of passages and word positions, in three zones: words, title, sound keys.", "Lecture: inverted index, zones", "index/inverted_index.py"],
  ["05", "Score", "BM25 in each zone with pooled df, added with weights; then boost passages where query words are close.", "Lecture: scoring, proximity", "retrieval/bm25.py · proximity.py"],
  ["06", "Gate", "A small model looks at how confident the fast search is and decides if the neural stage should run.", "Beyond syllabus: cascades", "cascade/gate.py"],
  ["07", "Dense and fuse", "A small distilled encoder finds passages by meaning; the two ranked lists are merged (RRF).", "Beyond syllabus: dense retrieval", "dense/scd.py · retrieval/rrf.py"],
];

// What each system in the picker does, in plain words, and which IR ideas it uses
const SYSTEM_INFO = {
  S3: ["LipiSetu, the main system. BM25 on the exact words, plus the Dhvani (sound) zone so Roman spellings match Devanagari text, pooled df, a title zone and a proximity boost. No neural model, answers in milliseconds.",
       ["BM25", "Dhvani zone", "pooled df", "title zone", "proximity"]],
  G1: ["The cascade. Runs S3 first, then a small gate model decides whether the slower neural stage is worth running for this query. Scroll the right panel to the Gate step to see the decision.",
       ["S3", "gate (logistic regression)", "dense retrieval", "RRF fusion"]],
  H1: ["The hybrid. Always runs both S3 and the distilled neural encoder, then merges the two ranked lists with reciprocal rank fusion.",
       ["S3", "dense retrieval", "RRF fusion"]],
  L1: ["Learning to rank. Takes candidates from S3 and the neural encoder and re-orders them with a model trained on the train split, using IR features (BM25 per zone, proximity, tf-idf, dense score, ...).",
       ["learning to rank", "IR features", "dense retrieval"]],
  B2: ["The obvious baseline. Converts a Roman query to Devanagari letter by letter, then runs normal BM25. Breaks on casual spellings: bharat becomes भरत (a name), not भारत (India).",
       ["transliteration", "BM25"]],
};

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
      renderSystemInfo();
      if ($("query").value.trim()) runSearch();
    });
  });
  renderSystemInfo();
}

function renderSystemInfo() {
  const info = SYSTEM_INFO[currentSystem];
  if (!info) { $("systemInfo").hidden = true; return; }
  let html = "<b>" + escapeHtml(systemName(currentSystem)) + " (" + currentSystem + "):</b> " + escapeHtml(info[0]);
  html += '<div class="ideas">';
  for (const idea of info[1]) html += '<span class="pill">' + escapeHtml(idea) + "</span>";
  html += "</div>";
  $("systemInfo").innerHTML = html;
  $("systemInfo").hidden = false;
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
  const badge = label ? '<span class="badge base">baseline</span>' : '<span class="badge ours">selected</span>';
  let html = '<div class="column">';
  html += '<div class="column-head"><span class="column-title">' + escapeHtml(systemName(data.system)) + " (" + data.system + ")" + badge + "</span>"
    + '<span class="column-meta">top ' + data.results.length + " · " + data.took_ms + " ms</span></div>";
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
  let text = "words " + fmt(b.all, 2) + " · sound " + fmt(b.dhvani || 0, 2);
  if (b.title !== undefined) text += " · title " + fmt(b.title, 2);
  if (b.proximity !== undefined) text += " · prox " + fmt(b.proximity, 2) + " (w " + b.window + ")";
  return text;
}

// ---------- trace panel: every step the engine took, with a plain-English line ----------
function renderTrace(data) {
  const ex = data.explain || {};
  const state = { step: 1 };
  let html = '<p class="trace-title">What the engine did</p>'
    + '<p class="trace-sub">Real values from the index for this query, step by step.</p>';
  html += traceTokens(ex, state);
  html += traceTerms(ex, state);
  html += tracePooled(ex, state);
  html += tracePostings(ex, state);
  html += traceGate(ex, state);
  html += '<div class="trace-foot">' + escapeHtml(systemName(data.system)) + " · " + data.took_ms + " ms</div>";
  $("trace").innerHTML = html;
}

function stepHead(state, title, explain) {
  const number = String(state.step).padStart(2, "0");
  state.step += 1;
  return '<h4><span class="num">' + number + "</span>" + title + '</h4><p class="explain">' + explain + "</p>";
}

function traceTokens(ex, state) {
  if (!ex.tokens || ex.tokens.length === 0) return "";
  let html = '<div class="trace-step">' + stepHead(state, "Split into words · script: " + escapeHtml(ex.script),
    "Struck-out words are <b>stop words</b> (too common to help). <b>stem</b> is the word after suffix removal; <b>dhvani</b> is its sound key.");
  html += '<div class="scroll-x"><table><thead><tr><th>word</th><th>script</th><th>stem</th><th class="mono">dhvani</th></tr></thead><tbody>';
  for (const t of ex.tokens) {
    html += "<tr" + (t.stop ? ' class="stop" title="stop word"' : "") + "><td>" + escapeHtml(t.token) + '</td><td><span class="tag">' + t.script + "</span></td><td>"
      + escapeHtml(t.stop ? "—" : t.stem) + '</td><td class="mono">' + escapeHtml(t.stop ? "—" : (t.dhvani || "·")) + "</td></tr>";
  }
  return html + "</tbody></table></div></div>";
}

function traceTerms(ex, state) {
  const zoneNames = { all: "words", dhvani: "sound", title: "title" };
  const zoneKeys = Object.keys(ex.zones || {});
  if (zoneKeys.length === 0) return "";
  let maxIdf = 0;
  for (const z of zoneKeys) for (const row of ex.zones[z]) maxIdf = Math.max(maxIdf, row.idf || 0);
  let html = '<div class="trace-step">' + stepHead(state, "How rare is each term? (df and idf)",
    "<b>df</b> = passages that contain the term (out of 110,855). <b>idf</b> = how much a match is worth: rare terms count more. A red <b>0</b> means that exact spelling never appears, so only the sound zone can match.");
  html += '<div class="scroll-x"><table><thead><tr><th>zone</th><th>term</th><th class="num">df</th><th class="num">idf</th><th></th></tr></thead><tbody>';
  for (const z of zoneKeys) {
    if (z === "title") continue;
    for (const row of ex.zones[z]) {
      const width = maxIdf > 0 ? Math.round(((row.idf || 0) / maxIdf) * 60) : 0;
      const zeroClass = (row.df || 0) === 0 ? " zero" : "";
      html += "<tr><td>" + zoneNames[z] + "</td><td" + (z === "dhvani" ? ' class="mono"' : "") + ">" + escapeHtml(row.term) + '</td><td class="num' + zeroClass + '">'
        + (row.df || 0).toLocaleString() + '</td><td class="num">' + fmt(row.idf || 0, 2) + '</td><td><span class="idf-bar" style="width:' + width + 'px"></span></td></tr>';
    }
  }
  return html + "</tbody></table></div></div>";
}

function tracePooled(ex, state) {
  if (!ex.pooled || ex.pooled.length === 0) return "";
  let html = '<div class="trace-step">' + stepHead(state, "Pooled df (all spellings together)",
    "Each spelling alone looks rare, which would inflate its idf. So every spelling uses the df of its whole sound class (<b>pooled df</b>) instead of its <b>own df</b>.");
  html += '<table><thead><tr><th>term</th><th class="num">own df</th><th class="num">pooled df</th></tr></thead><tbody>';
  for (const row of ex.pooled) {
    html += "<tr><td>" + escapeHtml(row.term) + '</td><td class="num">' + row.own_df.toLocaleString() + '</td><td class="num">' + row.pooled_df.toLocaleString() + "</td></tr>";
  }
  return html + "</tbody></table></div>";
}

function tracePostings(ex, state) {
  if (!ex.postings || ex.postings.length === 0) return "";
  let html = '<div class="trace-step">' + stepHead(state, "Postings lists (sound zone)",
    "The first entries of each key's postings list, read from the index: <b>passage id</b>, <b>tf</b> (times it appears) and <b>@ word positions</b>. Positions are used for the proximity boost.");
  for (const p of ex.postings) {
    let sample = "";
    for (const s of p.sample) sample += escapeHtml(s.doc) + " tf " + s.tf + " @" + s.positions.join(",") + "  ";
    html += '<div class="posting"><b>' + escapeHtml(p.key) + "</b> df " + p.df.toLocaleString() + " → " + sample + "</div>";
  }
  return html + "</div>";
}

function traceGate(ex, state) {
  if (!ex.gate) return "";
  const g = ex.gate;
  let html = '<div class="trace-step">' + stepHead(state, "Gate: run the neural stage?",
    "The gate reads signals from the fast search (how strong and clear the top score is, how many words matched only by sound, ...). The bar is its probability that the neural stage will help; the black tick is the threshold learned on the train split.");
  html += '<div class="meter" title="probability ' + fmt(g.probability, 2) + ", threshold " + fmt(g.threshold, 2) + '">'
    + '<div class="meter-fill" style="width:' + Math.round(g.probability * 100) + '%"></div>'
    + '<div class="meter-tick" style="left:calc(' + Math.round(g.threshold * 100) + '% - 1px)"></div></div>';
  html += '<p class="gate-decision">' + (g.use_neural
    ? '<b class="yes">Yes.</b> Probability ' + fmt(g.probability, 2) + " is above the threshold " + fmt(g.threshold, 2) + ", so the neural stage ran and the two lists were merged."
    : '<b class="no">No.</b> Probability ' + fmt(g.probability, 2) + " is below the threshold " + fmt(g.threshold, 2) + ", so the fast result was returned and no neural model ran.") + "</p>";
  html += '<div class="posting">';
  for (const name in g.features) html += escapeHtml(name) + " " + fmt(g.features[name], 2) + " · ";
  return html + "</div></div>";
}

// ---------- same question, other script ----------
async function renderConsistency(query) {
  const box = $("consistency");
  box.hidden = true;
  if (!hasDevanagari(query)) return;
  try {
    const data = await getJson("/api/consistency?q=" + encodeURIComponent(query) + "&system=" + currentSystem);
    if (!data.available || data.systems.length === 0) return;
    let html = '<span class="label">Same question, typed in Roman</span> <span class="roman">' + escapeHtml(data.roman) + "</span>";
    html += '<div class="consistency-row">';
    for (const s of data.systems) {
      html += "<span><b>" + escapeHtml(s.name) + "</b>: " + s.shared_top10 + ' of the top 10 are the same · <span class="value">RBO ' + fmt(s.rbo, 2) + "</span></span>";
    }
    html += '<button type="button" id="tryRoman">Search the Roman version</button></div>';
    html += '<p class="explain">We ran your question again in Roman letters and compared the two top-10 lists. RBO 1.0 = identical ranking, 0 = nothing in common. A script-invariant engine scores high here.</p>';
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
      + '</div><p class="station-text">' + s[2] + '</p><p class="station-lecture">' + s[3] + '</p><div class="station-file">' + s[4] + "</div></li>";
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
  renderTakeaways(data);
  renderHuman(data);
}

// ---------- takeaways: one sentence per figure, every number read from results/ ----------
function better(a, b) { return a > b ? "better than" : "not better than"; }

function renderTakeaways(data) {
  const main = data.main || [];
  const b1Deva = metricValue(main, "B1", "F1", "ndcg@10");
  const b1Roman = metricValue(main, "B1", "F2", "ndcg@10");
  const s2Roman = metricValue(main, "S2", "F2", "ndcg@10");
  const d0Roman = metricValue(main, "D0", "F2", "ndcg@10");
  const l1Deva = metricValue(main, "L1", "F1", "ndcg@10");
  if (b1Deva !== null && s2Roman !== null) {
    $("takeawaySystems").innerHTML = "<b>Takeaway:</b> normal BM25 (B1) falls from " + fmt(b1Deva, 3) + " on Devanagari to "
      + fmt(b1Roman, 3) + " on the same questions in Roman. With the Dhvani zone and pooled df (S2) Roman stays at " + fmt(s2Roman, 3)
      + ". The plain neural model (D0) gets " + fmt(d0Roman, 3) + " on Roman: it matches script before meaning. Learning to rank (L1) is highest on Devanagari (" + fmt(l1Deva, 3) + ").";
  }
  const op = data.operating_point;
  if (op) {
    const gate = op["gate_ndcg@10"], sparse = op["always_sparse_ndcg@10"], neural = op["always_neural_ndcg@10"];
    $("takeawayBudget").innerHTML = "<b>Takeaway:</b> with the threshold learned on train, the gate runs the neural stage for "
      + Math.round(op.gate_neural_share * 100) + "% of queries and reaches " + fmt(gate, 3) + ", " + better(gate, sparse)
      + " never running it (" + fmt(sparse, 3) + ") and " + better(gate, neural) + " always running it (" + fmt(neural, 3) + ").";
  }
  renderAblationTakeaway(data.ablation || []);
  const eff = data.efficiency || [];
  const s3 = findRow(eff, "system", "S3"), h1 = findRow(eff, "system", "H1"), g1 = findRow(eff, "system", "G1");
  if (s3 && h1 && g1) {
    $("takeawayEfficiency").innerHTML = "<b>Takeaway:</b> the sparse engine (S3) answers in " + fmt(s3.median_ms, 1)
      + " ms. Always running the neural stage (H1) takes " + fmt(h1.median_ms, 1) + " ms; the gated cascade (G1) takes "
      + fmt(g1.median_ms, 1) + " ms because most queries skip the neural stage.";
  }
}

function renderAblationTakeaway(rows) {
  if (rows.length < 2) return;
  const full = rows[0];
  let worst = rows[1];
  for (const r of rows.slice(1)) if (Number(r["ndcg@10_F2"]) < Number(worst["ndcg@10_F2"])) worst = r;
  const rule = worst.variant.replace("without ", "");
  $("takeawayAblation").innerHTML = "<b>Takeaway:</b> switching off <b>" + escapeHtml(rule) + "</b> hurts most: Roman nDCG@10 falls from "
    + fmt(full["ndcg@10_F2"], 3) + " to " + fmt(worst["ndcg@10_F2"], 3)
    + ". Without it, a Roman spelling rarely gets the same key as the Devanagari word, because people write vowels in many different ways.";
}

// ---------- human query set ----------
const HUMAN_FORMS = [["F1", "Devanagari"], ["H-R1", "Roman A1"], ["H-R2", "Roman A2"], ["H-R3", "Roman A3"], ["H-CM", "code-mixed"], ["H-EN", "English"]];
const HUMAN_SYSTEMS = ["B1", "B2", "S0", "S3", "D0", "D1", "H1", "L1", "G1"];

function renderHuman(data) {
  const rows = data.human_metrics || [];
  const agree = data.agreement;
  if (rows.length === 0 || !agree) {
    $("humanTiles").innerHTML = '<p class="empty">The human query set has not been evaluated yet.</p>';
    return;
  }
  let tiles = tile("Questions typed by each of us", String(agree.queries_with_three_romanisations),
    "3 people, " + agree.words_compared + " words compared");
  tiles += tile("Words spelled the same by all three", Math.round(agree.same_spelling_all_three * 100) + "%",
    "so " + Math.round((1 - agree.same_spelling_all_three) * 100) + "% of words were spelled differently by at least one of us");
  tiles += tile("Words with the same Dhvani key", Math.round(agree.same_dhvani_key_all_three * 100) + "%",
    "the sound key absorbs most of the differences");
  tiles += tile("LipiSetu (S3) on our Roman typing", romanRange(rows, "S3"),
    'baseline B2 <span class="from">' + romanRange(rows, "B2") + "</span> · nDCG@10");
  $("humanTiles").innerHTML = tiles;
  renderWordExamples(data.word_examples || []);
  renderHumanTable(rows);
  renderHumanTakeaway(rows);
}

function romanRange(rows, system) {
  const values = [];
  for (const form of ["H-R1", "H-R2", "H-R3"]) {
    const value = metricValue(rows, system, form, "ndcg@10");
    if (value !== null) values.push(value);
  }
  if (values.length === 0) return "—";
  return fmt(Math.min.apply(null, values), 2) + "–" + fmt(Math.max.apply(null, values), 2);
}

function renderWordExamples(rows) {
  if (rows.length === 0) { $("wordExamples").innerHTML = ""; return; }
  let html = '<table class="data-table"><thead><tr><th>A1 · A2 · A3 typed</th><th>Dhvani keys</th><th>same key?</th></tr></thead><tbody>';
  for (const r of rows.slice(0, 12)) {
    const ok = r.keys_agree === "True";
    html += '<tr><td class="mono">' + escapeHtml(r.spellings) + '</td><td class="mono">' + escapeHtml(r.dhvani_keys)
      + '</td><td class="' + (ok ? "agree" : "disagree") + '">' + (ok ? "✓ yes" : "✗ no") + "</td></tr>";
  }
  $("wordExamples").innerHTML = html + "</tbody></table>";
}

function renderHumanTable(rows) {
  const best = {};
  for (const form of HUMAN_FORMS) {
    best[form[0]] = 0;
    for (const s of HUMAN_SYSTEMS) best[form[0]] = Math.max(best[form[0]], metricValue(rows, s, form[0], "ndcg@10") || 0);
  }
  let html = '<table class="data-table"><thead><tr><th>system</th><th></th>';
  for (const form of HUMAN_FORMS) html += '<th class="num">' + form[1] + "</th>";
  html += "</tr></thead><tbody>";
  for (const s of HUMAN_SYSTEMS) {
    if (metricValue(rows, s, "F1", "ndcg@10") === null) continue;
    html += "<tr><td>" + s + "</td><td>" + escapeHtml(SYSTEM_LABELS[s]) + "</td>";
    for (const form of HUMAN_FORMS) {
      const value = metricValue(rows, s, form[0], "ndcg@10");
      html += '<td class="num' + (value === best[form[0]] ? " best" : "") + '">' + fmt(value, 3) + "</td>";
    }
    html += "</tr>";
  }
  $("humanTable").innerHTML = html + "</tbody></table>";
}

function renderHumanTakeaway(rows) {
  const s3Mixed = metricValue(rows, "S3", "H-CM", "ndcg@10");
  const s3English = metricValue(rows, "S3", "H-EN", "ndcg@10");
  const d1English = metricValue(rows, "D1", "H-EN", "ndcg@10");
  $("takeawayHuman").innerHTML = "<b>Takeaway:</b> on how people really type, LipiSetu (S3) reaches " + romanRange(rows, "S3")
    + " against " + romanRange(rows, "B2") + " for transliteration, so the results on generated queries hold. <b>Limitation:</b> code-mixed and English questions need meaning, not sound "
    + "(<i>leader</i> does not sound like नेता): S3 gets only " + fmt(s3Mixed, 3) + " and " + fmt(s3English, 3)
    + ", while the neural encoder (D1) gets " + fmt(d1English, 3) + " on English.";
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
