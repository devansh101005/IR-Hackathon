"""The text of the report. make_report.py fills in the numbers and tables from results/.

Written as plain HTML strings so it is easy to edit. Keep every claim tied to a number
that comes from results/ (passed in through `n` and the tables).
Style: a normal college report (Times New Roman text, Arial headings, plain grid tables).
"""

VIDEO_LINK = "https://drive.google.com/file/d/1TqHq50ZBkyzUqQHaT9QEZ2kipsKy6S4D/view?usp=sharing"
CODE_LINK = "https://github.com/devansh101005/IR-Hackathon"


def pct(value):
    return "%.0f%%" % (100.0 * float(value))


def figure(path, caption, width="100%"):
    return '<figure><img src="%s" style="width:%s"><figcaption>%s</figcaption></figure>' % (path, width, caption)


def caption(text):
    """Table captions go above the table, like in Word."""
    return '<p class="tcap">' + text + "</p>"


def simple_table(headers, rows):
    html = "<table><thead><tr>"
    for h in headers:
        html += "<th>" + h + "</th>"
    html += "</tr></thead><tbody>"
    for row in rows:
        html += "<tr>"
        for cell in row:
            html += "<td>" + cell + "</td>"
        html += "</tr>"
    return html + "</tbody></table>"


CSS = """
@page { size: A4; margin: 17mm 16mm 17mm 16mm; }
body { font-family: 'Times New Roman', Times, 'Nirmala UI', Mangal, serif; font-size: 10.5pt; line-height: 1.27; color: #000; }
h1 { font-family: Arial, Helvetica, sans-serif; font-size: 18pt; text-align: center; margin: 0 0 3pt; }
.subtitle { text-align: center; font-size: 11.5pt; font-style: italic; margin: 0 0 4pt; }
.course { text-align: center; font-size: 10.5pt; margin: 0 0 8pt; }
.links { text-align: center; font-size: 10pt; margin: 6pt 0 0; }
a { color: #1f4e9c; text-decoration: none; }
h2 { font-family: Arial, Helvetica, sans-serif; font-size: 12.5pt; margin: 11pt 0 4pt; break-after: avoid; page-break-after: avoid; }
h3 { font-family: Arial, Helvetica, sans-serif; font-size: 10.5pt; margin: 7pt 0 2pt; break-after: avoid; page-break-after: avoid; }
p { margin: 0 0 5pt; text-align: justify; }
.abstract-title { font-family: Arial, Helvetica, sans-serif; font-weight: bold; text-align: center; margin: 10pt 0 3pt; }
.abstract { margin: 0 24pt 6pt; font-size: 10.5pt; text-align: justify; }
hr { border: none; border-top: 1px solid #000; margin: 8pt 0; }
code, .mono { font-family: 'Courier New', Courier, monospace; font-size: 9.5pt; }
table { border-collapse: collapse; margin: 0 auto 7pt; font-size: 9pt; page-break-inside: avoid; }
th, td { border: 1px solid #000; padding: 1.8pt 4.5pt; vertical-align: top; }
th { background: #d9d9d9; font-weight: bold; text-align: center; }
th.num, td.num { text-align: right; }
tr.hl td { font-weight: bold; }
table.team { margin: 4pt auto 0; font-size: 10pt; }
.tcap { text-align: center; font-weight: bold; font-size: 9.5pt; margin: 6pt 0 2pt; break-after: avoid; page-break-after: avoid; }
figure { margin: 6pt 0 8pt; page-break-inside: avoid; text-align: center; }
figure img { max-width: 100%; }
.two figure img { max-height: 56mm; width: auto !important; }
figcaption { font-size: 9.5pt; margin-top: 3pt; text-align: center; }
figcaption b { font-weight: bold; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 12pt; align-items: start; }
.eq { text-align: center; font-style: italic; margin: 4pt 0 7pt; }
.eq .no { float: right; font-style: normal; }
ul, ol { margin: 2pt 0 6pt 18pt; padding: 0; }
li { margin-bottom: 2pt; text-align: justify; }
.refs li { font-size: 10pt; }
.pb { page-break-before: always; }
.note { font-size: 10pt; }
"""


def report_html(n, t, corpus, params, scd, point, human, top_terms):
    html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>LipiSetu report</title>'
    html += "<style>" + CSS + "</style></head><body>"
    html += title_block(n)
    html += section_problem(n, corpus)
    html += section_ir(n, t, corpus, params, top_terms)
    html += section_beyond(n, t, scd, point)
    html += section_novelty(n)
    html += section_evaluation(n, t, point, human)
    html += section_limitations(n)
    html += section_work_division()
    html += section_ai()
    html += section_references()
    html += section_appendix(t, params)
    html += "</body></html>"
    return html


def title_block(n):
    team = simple_table(["Name", "Roll No.", "Main contribution"], [
        ["Devansh Pandey", "2310110461", "Design, IR engine, Dhvani key, neural parts, evaluation, demo, report"],
        ["Anamika Pal", "2310110037", "Human query annotation, annotator-agreement analysis"],
        ["Abhinav Bachchas", "2310110383", "Human query annotation, results review, report proofreading"],
    ]).replace("<table>", '<table class="team">')
    return (
        "<h1>LipiSetu: Script-Invariant Hindi Search</h1>"
        '<p class="subtitle">One question, every script</p>'
        '<p class="course">CSD358 Information Retrieval &nbsp;|&nbsp; Mid-term Hackathon 2026 &nbsp;|&nbsp; '
        "Track T5: Multilingual and Indic-language Search</p>"
        + team +
        '<p class="links"><b>Code:</b> <a href="' + CODE_LINK + '">github.com/devansh101005/IR-Hackathon</a>'
        ' &nbsp;&nbsp; <b>Demo video:</b> <a href="' + VIDEO_LINK + '">Google Drive link (7:52)</a></p>'
        '<p class="abstract-title">Abstract</p>'
        '<p class="abstract">Most people type Hindi in Roman letters, and everyone spells it differently '
        "(<i>mausam, mosam, mousam</i>). Most Hindi text on the web, however, is written in Devanagari (मौसम). "
        "A normal search engine matches exact words, so these users get much worse results. On 350 judged "
        "MIRACL-Hindi test queries, BM25 reaches nDCG@10 " + n["b1_f1"] + " for questions typed in Devanagari, "
        "but only " + n["b1_f2"] + " for the same questions typed in Roman letters, and the obvious fix "
        "(transliterating the query first) only reaches " + n["b2_f2"] + ". We call this loss the <b>Script Gap</b>. "
        "LipiSetu closes most of it with classic IR, written from scratch: a sound-based key for every word "
        "(the <b>Dhvani key</b>) stored as its own index zone, <b>pooled document frequency</b> across spellings, "
        "and query-term proximity inside BM25. With these, Roman queries reach " + n["s2_f2"] + ". A small "
        "distilled neural encoder (448 MB → 37 MB) runs only when a gate trained on IR signals predicts it will "
        "help. A human query set typed by our three team members confirms the results on real spellings.</p>"
        "<hr>"
    )


# ---------------------------------------------------------------- 1. Problem
def section_problem(n, corpus):
    return (
        "<h2>1. Problem and Track Relevance</h2>"
        "<h3>1.1 The user need</h3>"
        "<p>On phones, Hindi is mostly typed in Roman letters (\"kal ka mausam\"), and every person spells words "
        "in their own way. But most content people search for (Wikipedia, news, government pages) is written in "
        "Devanagari (\"कल का मौसम\"). An inverted index matches exact terms, so a Roman query finds almost nothing, "
        "even when the answer is in the index. The mixing also happens inside the data: " +
        pct(corpus.get("share_of_docs_with_roman_words", 0)) + " of the MIRACL-Hindi passages we index already "
        "contain Roman-script words. Our goal is simple to state: <b>the same question should get the same results, "
        "whatever script it is typed in.</b></p>"
        "<h3>1.2 Why it belongs to Track T5</h3>"
        "<p>Track T5 asks for search in an Indian language with code-mixed or transliterated queries. Our system "
        "covers every IR topic listed for the track:</p><ul>"
        "<li>Tokenisation and normalisation for a non-English script (Devanagari).</li>"
        "<li>A Hindi stemmer, compared with no stemming.</li>"
        "<li>Soundex-style phonetic matching for transliterated spellings (our Dhvani key, compared with Soundex).</li>"
        "<li>How stop words and idf behave on a Hindi corpus.</li>"
        "<li>Cross-lingual ranking in a vector space (tf-idf cosine and a multilingual embedding model).</li></ul>"
        "<h3>1.3 Papers referred</h3>"
        "<p>Mixed-script retrieval was studied by Gupta et al. [2] and in the FIRE 2015 shared task [3]; we use the "
        "MIRACL dataset [1] for judged Hindi queries. Pooled df is based on Pirkola's structured queries [4]; our "
        "consistency metric uses Rank-Biased Overlap [5]; BM25 follows Robertson and Zaragoza [6]; the distillation "
        "follows Reimers and Gurevych [11]; the gate uses ideas from query performance prediction [8] and cascade "
        "ranking [9]. The course textbook [15] is the reference for all classic IR parts.</p>"
    )


# ---------------------------------------------------------------- 2. IR
def section_ir(n, t, corpus, params, top_terms):
    return (
        "<h2>2. How We Used IR</h2>"
        "<p>Figure 1 shows the whole pipeline. The left half is built once (offline); the right half runs for every "
        "query. Each box names the file that implements it, so every IR idea can be traced to the code.</p>"
        + figure("../pipeline.png", "<b>Figure 1:</b> LipiSetu pipeline. Orange boxes are our IR contributions, "
                 "blue boxes are neural components.")
        + ir_text_processing(n, corpus, top_terms)
        + ir_dhvani()
        + ir_index_and_scoring(n, params)
        + ir_concept_table()
    )


def ir_text_processing(n, corpus, top_terms):
    top_words = ", ".join([r["term"] for r in top_terms[:6]])
    return (
        "<h3>2.1 Documents and text processing</h3>"
        "<p><b>Documents.</b> One MIRACL passage is one document, because the relevance labels are given per "
        "passage. Each document has a <i>title</i> and a <i>body</i> zone. We index every passage judged for any "
        "query plus a fixed random sample: " + "{:,}".format(corpus.get("documents", 0)) + " passages and " +
        "{:,}".format(corpus.get("tokens", 0)) + " tokens.</p>"
        "<p><b>Tokenisation and normalisation</b> (<span class=\"mono\">text/tokenize.py, normalize.py</span>). "
        "Python's <span class=\"mono\">\\w</span> does not match Devanagari vowel signs, so a normal regex breaks "
        "हिन्दी into three pieces. We tokenise with explicit Unicode ranges instead. Normalisation applies Unicode NFC, "
        "folds nukta letters (क़ → क), maps chandrabindu to anusvara, removes invisible joiners, converts Devanagari "
        "digits, and lower-cases Roman text.</p>"
        "<p><b>Stop words and idf.</b> Hindi stop words are very frequent postpositions and helper verbs; the most "
        "frequent terms in our corpus are " + top_words + ". " + str(corpus.get("top40_df_terms_in_stop_list", "?")) +
        " of the 40 highest-df terms are in our stop list (Hindi, Hinglish and English). The corpus follows "
        "Zipf's law (Appendix G), and " + "{:,}".format(corpus.get("terms_seen_once", 0)) + " of the " +
        "{:,}".format(corpus.get("vocabulary", 0)) + " vocabulary terms occur only once.</p>"
        "<p><b>Stemming</b> (<span class=\"mono\">text/stemmer.py</span>). A light suffix stripper, after Ramanathan "
        "and Rao [13], maps लड़का / लड़के / लड़कों to one stem. It raises Devanagari nDCG@10 from " + n["b1n_f1"] +
        " (no stemming) to " + n["b1_f1"] + ".</p>"
    )


def ir_dhvani():
    rows = [
        ["Aspirated = unaspirated", "kh = k, bh = b (ख = क)", "people often skip the h"],
        ["Retroflex = dental", "ट = त, ड = द", "Roman letters cannot show the difference"],
        ["Drop vowels (keep a first vowel as A)", "mausam, mosam → MSM", "vowels are spelled in many ways"],
        ["w = v, z = j, f = ph", "zindagi = jindagi", "common spelling swaps"],
        ["Nasal before a consonant → N", "samvidhan = संविधान", "anusvara has no Roman letter"],
        ["Collapse repeated sounds", "pakka = पक्का → PK", "double letters are optional"],
    ]
    return (
        "<h3>2.2 The Dhvani key (our phonetic key)</h3>"
        "<p>Soundex gives words that sound alike the same code, but it only works for English letters and cuts "
        "codes to four characters. Our Dhvani key (<span class=\"mono\">text/dhvani.py</span>) works on <b>both "
        "scripts</b>: each consonant sound in Devanagari or Roman maps to one letter class, and the rules in Table 1 "
        "remove the differences that Roman spelling cannot show. मौसम, mausam, mosam and mousam all become "
        "<span class=\"mono\">MSM</span>. We do not cut the key to four characters, because Hindi words are short "
        "and cutting merges too many different words. Classic Soundex is also implemented, as a baseline.</p>"
        + caption("Table 1: Dhvani key rules") + simple_table(["Rule", "Example", "Why"], rows)
    )


def ir_index_and_scoring(n, params):
    return (
        "<h3>2.3 Inverted index with zones</h3>"
        "<p>The index (<span class=\"mono\">index/inverted_index.py</span>) is a dictionary plus postings lists "
        "with positions, stored in numpy arrays. It has three main zones: <i>all</i> (stemmed words of title and "
        "body), <i>title</i>, and <i>dhvani</i> (the key of every word). Extra zones (<i>soundex</i>, <i>nostem</i>, "
        "<i>raw</i>) exist only for the baselines. Boolean AND/OR/NOT processes terms in order of increasing df "
        "and uses skip pointers; phrase queries use the positions (<span class=\"mono\">retrieval/boolean.py</span>).</p>"
        "<h3>2.4 Scoring</h3>"
        "<p>Each zone is scored with BM25 (<span class=\"mono\">retrieval/bm25.py</span>), and the zone scores are "
        "added with weights:</p>"
        '<p class="eq">score(d) = BM25<sub>all</sub>(d) + w<sub>dhvani</sub>·BM25<sub>dhvani</sub>(d) + '
        "w<sub>title</sub>·BM25<sub>title</sub>(d) + λ·(m − 1) / (window − 1)<span class=\"no\">(1)</span></p>"
        "<p>The last term is <b>query-term proximity</b> (<span class=\"mono\">proximity.py</span>): the smallest "
        "window of word positions that contains all m matched query words. It is applied to the top 100 results. "
        "<b>Pooled df</b> fixes a subtle problem: one word can have many spellings, and each spelling alone looks "
        "rare, so its idf becomes too high. With pooled df, every spelling uses the df of its whole Dhvani class "
        "(all documents that contain any spelling of the word). This is Pirkola's idea [4], applied to spellings "
        "instead of translations. Scores are accumulated term-at-a-time and the top K are taken with a heap "
        "(<span class=\"mono\">topk.py</span>). We also implement tf-idf (lnc.ltc cosine) as the vector-space "
        "comparison. All parameters were tuned on the <b>train split only</b>: k1 = " + str(params.get("k1")) +
        ", b = " + str(params.get("b")) + ", w<sub>dhvani</sub> = " + str(params.get("w_dhvani")) +
        ", w<sub>title</sub> = " + str(params.get("w_title")) + ", λ = " + str(params.get("lambda_prox")) + ".</p>"
    )


def ir_concept_table():
    rows = [
        ["Boolean retrieval", "AND/OR/NOT, df-ordered merge, skip pointers, phrase queries", "retrieval/boolean.py"],
        ["Term vocabulary", "Tokeniser, normaliser, stop words, stemmer, Soundex, Dhvani key", "text/"],
        ["Index construction", "Positional inverted index with zones, lnc norms", "index/inverted_index.py"],
        ["tf-idf and VSM", "log tf, idf, lnc.ltc cosine", "retrieval/tfidf.py"],
        ["Scoring", "BM25 per zone, zone weights, pooled df", "retrieval/bm25.py"],
        ["Result assembly", "Heap top-K, champion lists, query-term proximity", "retrieval/topk.py, proximity.py"],
        ["Static quality g(d)", "Lead-passage prior used as a ranking feature", "rerank/ltr.py"],
        ["Cluster pruning", "√N leaders, followers of the nearest leaders scored", "dense/cluster_pruning.py"],
        ["Evaluation", "P@k, Recall@k, MRR, nDCG, RBO, significance test", "eval/metrics.py"],
    ]
    return caption("Table 2: IR concepts from the course and where they are in our code") + \
        simple_table(["Lecture topic", "What we implemented", "File (src/lipisetu/)"], rows)


# ---------------------------------------------------------------- 3. Beyond IR
def section_beyond(n, t, scd, point):
    sizes = scd.get("size_mb", {})
    epochs = scd.get("epochs", [])
    after = epochs[-1]["held_out_cosine"] if epochs else 0
    return (
        "<h2>3. Beyond IR</h2>"
        "<p><b>Dense retrieval</b> (<span class=\"mono\">dense/</span>). Every passage is turned into a vector once "
        "with the multilingual-e5-small model [14], exported to ONNX and compressed to int8 so it runs fast on a "
        "laptop CPU. A query is answered with a dot product over all passage vectors, or approximately with "
        "cluster pruning from the lectures.</p>"
        "<p><b>Script-consistency distillation (SCD).</b> We train a copy of the encoder (the student) so that a "
        "Roman spelling of a question lands at the same point as the original model's vector for the Devanagari "
        "question (loss = 1 − cosine), following [11]. Only the query side changes, so the passage vectors are "
        "reused. On held-out train questions, the cosine between a Roman question and its Devanagari target rises "
        "from " + "%.3f" % scd.get("held_out_cosine_before", 0) + " to " + "%.3f" % after + ". We then keep only the " +
        "{:,}".format(scd.get("vocab_pruned", 0)) + " tokens our data uses (out of 250,002) [12] and compress to int8: "
        + "%.0f" % sizes.get("full_fp32", 0) + " MB → " + "%.0f" % sizes.get("pruned_int8", 0) + " MB.</p>"
        "<p><b>Learning to rank</b> (<span class=\"mono\">rerank/ltr.py</span>). A logistic regression re-orders the "
        "candidates using IR features: BM25 per zone, proximity, tf-idf, the dense score, ranks in both lists, the "
        "static quality prior and passage length [10]. It is trained on the train judgments only.</p>"
        "<p><b>Gated cascade</b> (<span class=\"mono\">cascade/gate.py</span>). The neural stage is slow, and it "
        "does not always help. The gate looks at signals the fast search gives for free (top score, score gap, "
        "NQC [8], how many words matched only through the Dhvani zone, max idf, query length, script) and predicts "
        "whether running the neural stage will improve the ranking. Its threshold is chosen on the train split.</p>"
    )


# ---------------------------------------------------------------- 4. Novelty
def section_novelty(n):
    rows = [
        ["Evaluation", "Average nDCG or P@k only", "Script Gap, cross-script consistency (RBO), worst-script nDCG"],
        ["Roman queries", "Transliterate the query, then BM25", "Dhvani zone inside the index, no transliteration model"],
        ["df of spelling variants", "Each spelling has its own df", "Pooled df across spellings"],
        ["Neural stage", "Always on, or not used", "Runs only when an IR-signal gate says it helps"],
        ["Model size", "Off-the-shelf encoder", "Distilled for script consistency, pruned, int8 (37 MB)"],
        ["Test queries", "Generated variants only", "Also 60 questions romanised by 3 people independently"],
    ]
    return (
        "<h2>4. Novelty and Creativity</h2>"
        "<p>The obvious T5 project, and the sample idea in the assignment, is a Hinglish search engine that "
        "transliterates the query and ranks it with BM25. In our project that is only the baseline (B2). Table 3 "
        "lists what we do differently.</p>"
        + caption("Table 3: The obvious approach compared with LipiSetu")
        + simple_table(["Aspect", "Obvious approach", "LipiSetu"], rows)
        + "<p><b>Prior work.</b> Mixed-script search is not new [2, 3], and Soundex variants for Indian languages "
        "exist. We do not claim to be the first. To our knowledge, what is new for Hindi on MIRACL is the "
        "combination: measuring script invariance directly, a cross-script phonetic zone with pooled df inside a "
        "classic BM25 engine (with a rule-by-rule ablation), and neural inference that is gated by IR signals and "
        "reported as a quality-versus-compute trade-off.</p>"
    )


# ---------------------------------------------------------------- 5. Evaluation
def section_evaluation(n, t, point, human):
    return (
        "<h2>5. Evaluation</h2>"
        + eval_setup()
        + eval_main(n, t)
        + eval_neural_and_gate(n)
        + eval_human(n, t, human)
        + eval_ablation(n, t)
        + eval_efficiency_and_significance(n)
    )


def eval_setup():
    return (
        "<h3>5.1 Setup</h3>"
        "<p><b>Queries and judgments.</b> The test set is the 350 MIRACL-Hindi dev queries (3,494 judged passages, "
        "about 2.1 relevant passages per query). All tuning and training uses the separate 1,169 train queries "
        "only. Every test query is asked in three forms: <b>F1</b> the original Devanagari, <b>F2</b> a standard "
        "Roman spelling, and <b>F3</b> a casual Roman spelling with random spelling noise "
        "(<span class=\"mono\">text/romanize.py</span>). Unjudged passages count as not relevant.</p>"
        "<p><b>Metrics.</b> nDCG@10 is the main metric. P@10 is reported too, but with only about 2 relevant "
        "passages per query it cannot go above about 0.2. To measure script invariance we add three metrics:</p><ul>"
        "<li><b>Script Gap</b> = nDCG@10 for Devanagari minus nDCG@10 for a Roman form (0 = script does not matter).</li>"
        "<li><b>CSC@10</b> (cross-script consistency) = average Rank-Biased Overlap [5] between the top-10 lists of "
        "the three forms (1 = identical rankings).</li>"
        "<li><b>Worst-script nDCG@10</b> = for each query, the nDCG@10 of its worst form, averaged.</li></ul>"
        "<p><b>Systems.</b> B0 raw BM25; B1 BM25 with normalisation and stemming; B1N without stemming; B2 "
        "transliteration + BM25 (the obvious baseline); V1 tf-idf cosine; S0 B1 + Soundex zone; S1 B1 + Dhvani "
        "zone; S2 S1 + pooled df; S3 S2 + title zone + proximity; D0 dense e5-small; D1 our distilled encoder; H1 "
        "S3 + D1 fused with RRF [7]; L1 learning to rank; G1 the gated cascade.</p>"
    )


def eval_main(n, t):
    return (
        "<h3>5.2 Main results</h3>"
        + '<div class="two">'
        + figure("../../results/fig_ndcg_by_system.png", "<b>Figure 2:</b> nDCG@10 by system and query script.")
        + figure("../../results/fig_budget_curve.png", "<b>Figure 3:</b> Quality against the share of queries "
                 "that run the neural stage.")
        + "</div>"
        + caption("Table 4: Search quality on the 350 test queries (bold = our main systems)") + t["effectiveness"]
        + "<p><b>The Script Gap is real and large.</b> BM25 with stemming (B1) reaches " + n["b1_f1"] + " on "
        "Devanagari questions but " + n["b1_f2"] + " on the same questions in Roman. Transliterating the query "
        "(B2) only recovers " + n["b2_f2"] + " / " + n["b2_f3"] + " (standard / casual Roman), because casual "
        "spellings are not valid transliteration input: <i>bharat</i> becomes भरत (a name), not भारत (India). "
        "Classic Soundex (S0) helps (" + n["s0_f2"] + ") but its four-character English codes merge too many words. "
        "The Dhvani zone (S1) reaches " + n["s1_f2"] + " / " + n["s1_f3"] + ", with almost no loss on Devanagari.</p>"
        + caption("Table 5: Script invariance (lower Script Gap and higher CSC are better)") + t["invariance"]
        + "<p>With pooled df (S2), the Script Gap on casual Roman falls from " + n["b2_gap3"] + " (B2) to " +
        n["s2_gap3"] + ", and cross-script consistency rises from " + n["b2_csc"] + " to " + n["s2_csc"] + ". "
        "In other words, LipiSetu gives almost the same answer whichever script the question is typed in.</p>"
    )


def eval_neural_and_gate(n):
    return (
        "<h3>5.3 Neural models and the gate</h3>"
        "<p><b>Neural models have their own script problem.</b> The plain dense model (D0) is the best single "
        "model on Devanagari (" + n["d0_f1"] + ") but scores " + n["d0_f3"] + " on casual Roman: for a Roman "
        "question it finds other Roman-script passages, so it matches the script before the meaning. Our "
        "distillation (D1) fixes part of this (" + n["d1_f3"] + ") at almost no cost on Devanagari (" + n["d1_f1"] +
        "), but stays far below the Dhvani zone on Roman. Simple fusion (H1) is best on Devanagari (" + n["h1_f1"] +
        ") but pulls Roman down to " + n["h1_f2"] + ". Learning to rank (L1) uses both signals and is the best "
        "system on every script (" + n["l1_f1"] + " / " + n["l1_f2"] + " / " + n["l1_f3"] + "), with the highest "
        "worst-script nDCG (" + n["l1_worst"] + " against " + n["b2_worst"] + " for B2).</p>"
        "<p><b>The gate spends neural compute only where it helps.</b> Because the neural stage helps Devanagari "
        "questions but hurts many Roman ones, always running it (" + n["op_neural"] + ") is worse than never "
        "running it (" + n["op_sparse"] + "). With its threshold chosen on train, the gate runs the neural stage "
        "for " + n["op_share"] + " of queries and reaches " + n["op_ndcg"] + ", better than both, and clearly "
        "above a random gate with the same budget (Figure 3). Its median latency is " + n["g1_ms"] + " ms, against " +
        n["h1_ms"] + " ms for always running the neural stage.</p>"
        "<p><b>tf-idf against BM25.</b> lnc.ltc cosine (V1) scores " + n["v1_f1"] + " against " + n["b1_f1"] +
        " for BM25. Full cosine normalisation favours short passages: the median length of V1's top result is " +
        n["v1_len"] + " terms, against " + n["corpus_len"] + " for the corpus and " + n["b1_len"] + " for BM25.</p>"
    )


def eval_human(n, t, human):
    if not human:
        return ""
    return (
        "<h3>5.4 Human query set</h3>"
        "<p>Our Roman test forms are generated by a program, so we also built a small test set from real typing. "
        "Each of the three team members took the same 60 test questions and typed them in Roman letters on their "
        "own, without any transliteration tool and without looking at each other's sheets. Each member also wrote "
        "code-mixed and English versions of 20 questions. All three spelled a word identically for only " +
        pct(human.get("same_spelling_all_three", 0)) + " of the words, but their Dhvani keys were the same for " +
        pct(human.get("same_dhvani_key_all_three", 0)) + " of the words.</p>"
        + caption("Table 6: nDCG@10 on the human query set (60 questions; A1–A3 are the three annotators)") + t["human"]
        + "<p>On the real romanisations BM25 reaches only " + n["hum_b1_r"] + " and transliteration " +
        n["hum_b2_r"] + ", while LipiSetu (S3) reaches " + n["hum_s3_r"] + " (p ≤ " + n["hum_p_s3_b2"] + " against B2 "
        "for every annotator) and learning to rank " + n["hum_l1_r"] + ". So the results on generated queries hold "
        "for real spelling variation. Code-mixed and English questions are different: a sound key cannot link "
        "<i>leader</i> to नेता, so S3 drops to " + n["hum_s3_cm"] + " (code-mixed) and " + n["hum_s3_en"] +
        " (English), and only the neural encoder helps (D1 " + n["hum_d1_en"] + " on English). The gate never saw "
        "such questions in training and calls the neural stage too rarely for them (G1 " + n["hum_g1_en"] +
        " against H1 " + n["hum_h1_en"] + " on English, p = " + n["hum_p_g1_h1_en"] + ").</p>"
    )


def eval_ablation(n, t):
    return (
        "<h3>5.5 Which parts matter</h3>"
        + caption("Table 7: Dhvani rule ablation (one rule switched off, Dhvani zone rebuilt)") + t["ablation"]
        + "<p><b>Ablation.</b> Dropping vowels is by far the most important rule, followed by merging retroflex "
        "and dental sounds (Table 7). Collapsing doubled letters slightly hurts; we kept the rule set as designed "
        "instead of tuning it on the test queries.</p>"
        + caption("Table 8: Pooled df on a mixed-script corpus (30% of passages romanised)") + t["mixed"]
        + "<p><b>Pooled df.</b> On the Devanagari-only corpus, pooled df trades a little Devanagari accuracy (" +
        n["s1_f1"] + " → " + n["s2_f1"] + ") for Roman accuracy and consistency. On a corpus where 30% of passages "
        "are romanised, a word's df really is split between its spellings, and pooled df helps every form: "
        "standard Roman " + n["mixed_s1_f2"] + " → " + n["mixed_s2_f2"] + ", casual Roman " + n["mixed_s1_f3"] +
        " → " + n["mixed_s2_f3"] + ", consistency " + n["mixed_s1_csc"] + " → " + n["mixed_s2_csc"] +
        " (idf examples in Appendix F).</p>"
    )


def eval_efficiency_and_significance(n):
    return (
        "<h3>5.6 Efficiency and significance</h3>"
        "<p><b>Efficiency</b> (Appendix A and E, laptop CPU, no GPU). The sparse engine S3 answers in " + n["s3_ms"] +
        " ms (median). Skip pointers halve the comparisons in AND merges. Champion lists are 5–6 times faster but "
        "lose a lot of quality. Cluster pruning scores only about 5% of the passage vectors and keeps half of the "
        "exact top 100, but on our laptop it is not faster, because one numpy dot product over 110k vectors already "
        "takes only a few milliseconds.</p>"
        "<p><b>Significance</b> (Appendix D). Paired randomisation tests (10,000 permutations, nDCG@10) give "
        "p &lt; 0.001 for every Roman-query gain discussed above (S1 over B1 and S0, S3 over B2, D1 over D0, L1 and "
        "G1 over H1). On Devanagari questions the sparse systems are not significantly different from B1/B2, so "
        "the gains on Roman come without a loss on Devanagari.</p>"
    )


# ---------------------------------------------------------------- 6-7
def section_limitations(n):
    return (
        "<h2>6. Limitations and Next Steps</h2><ul>"
        "<li><b>Sound keys merge some different words.</b> <i>kal</i> (कल, tomorrow) and <i>khel</i> (खेल, game) "
        "both become KL, so sports passages can appear for a weather question (shown live in our video). Zone "
        "weights reduce this but do not remove it.</li>"
        "<li><b>Meaning, not sound.</b> English words in code-mixed questions (<i>leader</i> for नेता) are only "
        "matched by the neural stage, and the gate was not trained on such questions.</li>"
        "<li><b>Subsampled corpus.</b> We index a subsample of MIRACL-Hindi, so our scores are not comparable to "
        "the MIRACL leaderboard.</li>"
        "<li><b>Small human set.</b> 60 questions; one annotator (Devansh) also designed the Dhvani key, so his "
        "romanisation is not blind.</li>"
        "<li><b>Hindi only.</b></li></ul>"
        "<p><b>Roadmap (if continued as the course project):</b> (1) Bengali and Telugu from MIRACL with their own "
        "Dhvani tables; (2) a larger human query set, including voice queries; (3) the int8 encoder running in the "
        "browser, so search works fully on a phone; (4) learning the key rules from data instead of writing them "
        "by hand.</p>"
    )


def section_work_division():
    rows = [
        ["Devansh Pandey<br>2310110461",
         "Idea and system design; text pipeline, inverted index, Boolean and phrase search, tf-idf, BM25, proximity, "
         "top-K and champion lists; the Dhvani key and pooled df; dense retrieval, distillation, vocabulary pruning, "
         "cluster pruning; learning to rank; the gated cascade; evaluation framework and metrics; demo; report; one "
         "of the three annotators (code-mixed and English for rows 1–20)."],
        ["Anamika Pal<br>2310110037",
         "Annotated the human query set (60 romanised questions; code-mixed and English for rows 21–40); analysed "
         "the annotator-agreement results and presents them in the video."],
        ["Abhinav Bachchas<br>2310110383",
         "Annotated the human query set (60 romanised questions; code-mixed and English for rows 41–60); reviewed "
         "the final results and plots; proofread the report; presents the evaluation and the live limitation in "
         "the video."],
    ]
    return "<h2>7. Work Division</h2>" + caption("Table 9: Who worked on what") + \
        simple_table(["Member", "Contribution"], rows)


def section_ai():
    return (
        "<h2>AI-Use Declaration</h2>"
        "<p>We used Claude Code (an AI coding agent by Anthropic) to write code, tests and documentation and to run "
        "the experiments, under Devansh's direction. Devansh chose the track and the idea, designed the system, "
        "reviewed the code and checked every result. The human query annotations were written by the three of us "
        "without AI tools. Every number in this report was produced by the scripts in the repository on the real "
        "data.</p>"
    )


def section_references():
    refs = [
        "X. Zhang et al. MIRACL: A Multilingual Retrieval Dataset Covering 18 Diverse Languages. TACL, 2023.",
        "P. Gupta, K. Bali, R. E. Banchs, M. Choudhury, P. Rosso. Query Expansion for Mixed-Script Information Retrieval. SIGIR, 2014.",
        "R. Sequiera et al. Overview of FIRE-2015 Shared Task on Mixed Script Information Retrieval. FIRE, 2015.",
        "A. Pirkola. The Effects of Query Structure and Dictionary Setups in Dictionary-Based Cross-Language Information Retrieval. SIGIR, 1998.",
        "W. Webber, A. Moffat, J. Zobel. A Similarity Measure for Indefinite Rankings. ACM TOIS, 2010.",
        "S. Robertson, H. Zaragoza. The Probabilistic Relevance Framework: BM25 and Beyond. FnTIR, 2009.",
        "G. V. Cormack, C. L. A. Clarke, S. Büttcher. Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods. SIGIR, 2009.",
        "A. Shtok, O. Kurland, D. Carmel, F. Raiber, G. Markovits. Predicting Query Performance by Query-Drift Estimation. ACM TOIS, 2012.",
        "L. Wang, J. Lin, D. Metzler. A Cascade Ranking Model for Efficient Ranked Retrieval. SIGIR, 2011.",
        "T.-Y. Liu. Learning to Rank for Information Retrieval. FnTIR, 2009.",
        "N. Reimers, I. Gurevych. Making Monolingual Sentence Embeddings Multilingual using Knowledge Distillation. EMNLP, 2020.",
        "A. Abdaoui, C. Pradel, G. Sigel. Load What You Need: Smaller Versions of Multilingual BERT. SustaiNLP, 2020.",
        "A. Ramanathan, D. D. Rao. A Lightweight Stemmer for Hindi. EACL Workshop on Computational Linguistics for South Asian Languages, 2003.",
        "L. Wang et al. Multilingual E5 Text Embeddings: A Technical Report. arXiv, 2024.",
        "C. D. Manning, P. Raghavan, H. Schütze. Introduction to Information Retrieval. Cambridge University Press, 2008.",
    ]
    html = '<h2>References</h2><ol class="refs">'
    for r in refs:
        html += "<li>" + r + "</li>"
    return html + "</ol><p class=\"note\">Data: MIRACL (Apache-2.0), passage text from Wikipedia (CC BY-SA 3.0). " \
        "Model: intfloat/multilingual-e5-small (MIT).</p>"


def section_appendix(t, params):
    return (
        '<h2 class="pb">Appendix</h2>'
        + caption("A. Query latency per system (laptop CPU, Intel i5-12450H, no GPU)") + t["efficiency"]
        + '<div class="two"><div>' + caption("B. Learning-to-rank feature weights") + t["ltr"] + "</div>"
        + "<div>" + caption("C. Gate feature weights") + t["gate"] + "</div></div>"
        + caption("D. Significance tests (paired randomisation, 10,000 permutations, nDCG@10)") + t["significance"]
        + caption("E. Efficiency structures") + t["structures"]
        + caption("F. idf of spelling variants on the mixed-script corpus, with and without pooled df") + t["idf"]
        + '<div class="two">' + figure("../../results/fig_zipf.png", "<b>G.</b> Zipf plot of the corpus.")
        + figure("../../results/fig_idf_hist.png", "<b>H.</b> idf distribution of the vocabulary.") + "</div>"
    )
