"""The text of the report. make_report.py fills in the numbers and tables from results/.

Written as plain HTML strings so it is easy to edit. Keep every claim tied to a number
that comes from results/ (passed in through `n` and the tables).
"""

def pct(value):
    return "%.0f%%" % (100.0 * float(value))


def figure(path, caption, width="100%"):
    return '<figure><img src="%s" style="width:%s"><figcaption>%s</figcaption></figure>' % (path, width, caption)


CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: 'Inter', 'Noto Sans Devanagari', Arial, sans-serif; font-size: 9.6pt; line-height: 1.42; color: #1a1a1a; }
h1 { font-family: 'Fraunces', Georgia, serif; font-weight: 500; font-size: 21pt; margin: 0 0 2pt; letter-spacing: -0.01em; }
h2 { font-size: 12pt; margin: 13pt 0 5pt; padding-bottom: 2pt; border-bottom: 1px solid #1a1a1a; }
h3 { font-size: 10pt; margin: 9pt 0 3pt; break-after: avoid; page-break-after: avoid; }
h2 { break-after: avoid; page-break-after: avoid; }
p { margin: 0 0 5pt; text-align: justify; hyphens: auto; }
.meta { color: #4a4844; font-size: 9pt; margin-bottom: 8pt; }
.meta b { color: #1a1a1a; }
.abstract { border-left: 3px solid #cb6843; padding: 5pt 9pt; background: #fbf6f2; margin: 6pt 0 8pt; }
code, .mono { font-family: 'JetBrains Mono', Menlo, monospace; font-size: 8.4pt; }
table { width: 100%; border-collapse: collapse; margin: 4pt 0 7pt; font-size: 8.4pt; page-break-inside: avoid; }
th { text-align: left; font-weight: 600; border-bottom: 1px solid #1a1a1a; padding: 2.5pt 5pt 2.5pt 0; }
td { border-bottom: 1px solid #e6e3de; padding: 2.2pt 5pt 2.2pt 0; }
th.num, td.num { text-align: right; font-variant-numeric: tabular-nums; }
tr.hl td { font-weight: 600; background: #fbf6f2; }
figure { margin: 6pt 0 8pt; page-break-inside: avoid; text-align: center; }
figure img { max-width: 100%; }
figcaption { font-size: 8.4pt; color: #4a4844; margin-top: 2pt; text-align: left; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 10pt; }
.formula { font-family: 'JetBrains Mono', Menlo, monospace; font-size: 8.4pt; background: #f6f4f0; padding: 4pt 7pt; margin: 3pt 0 6pt; border-radius: 3px; }
ul { margin: 2pt 0 6pt 14pt; padding: 0; }
li { margin-bottom: 2pt; }
.refs li { font-size: 8.4pt; }
.pb { page-break-before: always; }
.small { font-size: 8.4pt; color: #4a4844; }
"""


def report_html(n, t, corpus, params, scd, point, human, top_terms):
    html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>LipiSetu report</title>'
    html += '<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500&family=Inter:wght@400;600&family=JetBrains+Mono&family=Noto+Sans+Devanagari:wght@400;600&display=swap" rel="stylesheet">'
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
    return (
        "<h1>LipiSetu: Script-Invariant Hindi Search</h1>"
        '<div class="meta"><b>CSD358 IR Hackathon · Track T5: Multilingual and Indic-language search</b><br>'
        "Team: Devansh Pandey (2310110461), Anamika Pal (2310110037), Abhinav Bachchas (2310110383) · "
        "Code: <a href=\"https://github.com/devansh101005/IR-Hackathon\">github.com/devansh101005/IR-Hackathon</a> · "
        "Demo video: <a href=\"https://drive.google.com/file/d/1TqHq50ZBkyzUqQHaT9QEZ2kipsKy6S4D/view?usp=sharing\">Google Drive (7:52)</a></div>"
        '<div class="abstract">Most Hindi users type Hindi in Roman letters, each with their own spelling, while most '
        "Hindi text is written in Devanagari. A standard search engine therefore serves them far worse: on 350 judged "
        "MIRACL-Hindi queries, BM25 reaches nDCG@10 " + n["b1_f1"] + " for Devanagari queries but only " + n["b1_f2"] +
        " for the same questions typed in Roman script, and the obvious fix (transliterating the query) only reaches " +
        n["b2_f2"] + ". We call this loss the <b>Script Gap</b>. LipiSetu closes most of it with classic IR: a "
        "cross-script phonetic key (the <b>Dhvani key</b>) indexed as its own zone, <b>pooled document frequency</b> "
        "across spellings, and query-term proximity, all inside a BM25 engine written from scratch. A distilled, "
        "int8 neural query encoder is run only when a gate trained on IR signals predicts that it will help.</div>"
    )


def section_problem(n, corpus):
    return (
        "<h2>1. Problem and track relevance</h2>"
        "<p><b>User need.</b> On phones, Hindi is mostly typed in Roman script (\"kal ka mausam\"), and the same word is "
        "spelled in many ways (mausam / mosam / mousam). The content people search (Wikipedia, news, government pages) "
        "is mostly in Devanagari (\"कल का मौसम\"). An inverted index matches exact terms, so these users silently get "
        "worse results. The problem is also inside the data itself: " + pct(corpus.get("share_of_docs_with_roman_words", 0)) +
        " of the MIRACL-Hindi passages we index already contain Roman-script words.</p>"
        "<p><b>Why it belongs to T5.</b> The track asks for search in an Indian language with code-mixed or "
        "transliterated queries. Our system touches every IR hook listed for T5: tokenisation and normalisation for "
        "Devanagari, a Hindi stemmer compared with no stemming, Soundex-style phonetic matching for transliterated "
        "spellings, the behaviour of stop words and idf on a Hindi corpus, and cross-lingual ranking in a vector space.</p>"
        "<p><b>Papers referred.</b> Mixed-script IR was studied by Gupta et al. (SIGIR 2014) and in the FIRE 2015 MSIR "
        "shared task; we use MIRACL (Zhang et al., TACL 2023) for judged Hindi queries. Pooled df follows Pirkola's "
        "structured queries (SIGIR 1998); the consistency metric is Rank-Biased Overlap (Webber et al., TOIS 2010); "
        "the distillation follows Reimers and Gurevych (EMNLP 2020); the gate follows query performance prediction "
        "(NQC, Shtok et al.) and cascade ranking (Wang, Lin and Metzler, SIGIR 2011). Full list in the references.</p>"
    )


def section_ir(n, t, corpus, params, top_terms):
    stop_hits = corpus.get("top40_df_terms_in_stop_list", "?")
    top_words = ", ".join([r["term"] for r in top_terms[:8]])
    return (
        "<h2>2. How we used IR</h2>"
        + figure("../pipeline.png", "Figure 1. LipiSetu pipeline. Orange boxes are our IR contributions, blue boxes "
                 "are neural components. Every box names the file that implements it.")
        + "<p><b>What is a document.</b> One MIRACL passage is one document (relevance labels are per passage), with "
        "zones <i>title</i> and <i>body</i>. We index every passage judged for a dev or train query plus a seeded random "
        "sample, " + "{:,}".format(corpus.get("documents", 0)) + " passages and " + "{:,}".format(corpus.get("tokens", 0)) +
        " tokens in total (<span class=\"mono\">scripts/build_subsample.py</span>).</p>"
        "<p><b>Tokenisation and normalisation</b> (<span class=\"mono\">text/tokenize.py, normalize.py</span>). Python's "
        "<span class=\"mono\">\\w</span> does not match Devanagari vowel signs, so a regex tokenizer cuts हिन्दी into "
        "three pieces; we tokenise with explicit Unicode ranges instead. Normalisation applies NFC, folds nukta "
        "(क़→क), chandrabindu to anusvara, removes zero-width joiners, maps Devanagari digits, rewrites a half nasal "
        "before a consonant as an anusvara (हिन्दी = हिंदी), and case-folds Roman text.</p>"
        "<p><b>Stop words and idf on Hindi</b> (<span class=\"mono\">text/stopwords.py, scripts/corpus_stats.py</span>). "
        "Hindi stop words are extremely frequent postpositions and auxiliaries: the eight highest-df terms are " +
        top_words + ". " + str(stop_hits) + " of the 40 highest-df terms are in our stop list (Hindi, Hinglish and "
        "English question words included). The corpus follows Zipf's law (appendix), and " +
        "{:,}".format(corpus.get("terms_seen_once", 0)) + " of the " + "{:,}".format(corpus.get("vocabulary", 0)) +
        " vocabulary terms occur only once, so most of the vocabulary has a very high idf. Stop words keep their "
        "positions so phrase queries keep the right gaps.</p>"
        "<p><b>Stemming</b> (<span class=\"mono\">text/stemmer.py</span>). A light suffix stripper after Ramanathan and "
        "Rao (2003) maps लड़का / लड़के / लड़कों to one stem. It raises Devanagari nDCG@10 from " + n["b1n_f1"] +
        " (no stemming, B1N) to " + n["b1_f1"] + " (B1).</p>"
        "<p><b>Dhvani key</b> (<span class=\"mono\">text/dhvani.py</span>). A Soundex-style key that works on both "
        "scripts: every consonant sound maps to one class, aspirated = unaspirated, retroflex = dental, w = v, z = j, "
        "f = ph, a nasal before a consonant becomes N, vowels are dropped except at the start (which also handles "
        "Hindi's silent inherent vowel), and repeated classes collapse. Unlike English Soundex the key is not cut to "
        "four characters. मौसम, mausam, mosam and mousam all become <span class=\"mono\">MSM</span>. Classic Soundex "
        "(<span class=\"mono\">text/soundex.py</span>) is implemented as a comparison.</p>"
        "<p><b>Inverted index with zones</b> (<span class=\"mono\">index/inverted_index.py</span>). A dictionary plus "
        "one postings file packed into numpy arrays, with positions. Zones: <i>all</i> (stemmed title + body), "
        "<i>title</i>, <i>dhvani</i> (keys of every word), plus <i>soundex</i>, <i>nostem</i> and <i>raw</i> zones for "
        "the baselines. Boolean AND/OR/NOT processes terms in order of increasing df and uses skip pointers; phrase "
        "queries use positions (<span class=\"mono\">retrieval/boolean.py</span>).</p>"
        "<p><b>Scoring</b> (<span class=\"mono\">retrieval/bm25.py, tfidf.py, proximity.py, topk.py</span>). BM25 per "
        "zone, combined with zone weights, accumulated term-at-a-time in one score slot per document, with heap-based "
        "top-K. tf-idf lnc.ltc cosine is implemented as the vector-space comparison.</p>"
        '<div class="formula">score(d) = BM25<sub>all</sub>(d) + w<sub>dhvani</sub>·BM25<sub>dhvani</sub>(d) + '
        "w<sub>title</sub>·BM25<sub>title</sub>(d) + λ·(m−1)/(window−1)</div>"
        "<p>The last term is <b>query-term proximity</b>: the smallest window of Dhvani positions that contains all m "
        "matched query words, applied to the top 100. <b>Pooled df</b>: a surface term uses the df of its Dhvani class, "
        "i.e. the number of documents containing any spelling of that word (Pirkola's structured query, applied to "
        "spelling variants instead of translations). All parameters were tuned on the <b>train</b> split only, with "
        "the average nDCG@10 over the three query scripts as the objective: k1 = " + str(params.get("k1")) + ", b = " +
        str(params.get("b")) + ", w<sub>dhvani</sub> = " + str(params.get("w_dhvani")) + ", w<sub>title</sub> = " +
        str(params.get("w_title")) + ", λ = " + str(params.get("lambda_prox")) + ". Champion lists (r = 200) are "
        "precomputed for the speed experiment.</p>"
    )


def section_beyond(n, t, scd, point):
    sizes = scd.get("size_mb", {})
    epochs = scd.get("epochs", [])
    after = epochs[-1]["held_out_cosine"] if epochs else 0
    return (
        "<h2>3. Beyond IR</h2>"
        "<p><b>Dense retrieval</b> (<span class=\"mono\">dense/</span>). Passages are encoded once with "
        "multilingual-e5-small, exported to ONNX and quantised to int8 (cosine with the fp32 vectors ≈ 0.98). "
        "Search is a dot product over the passage vectors, or <b>cluster pruning</b> from the lectures "
        "(√N leaders; only the followers of the 8 nearest leaders are scored).</p>"
        "<p><b>Script-Consistency Distillation (SCD).</b> A student copy of the encoder is trained so that a Roman "
        "spelling of a train query lands on the teacher's embedding of the Devanagari query (loss = 1 − cosine). "
        "Only the query encoder changes, so the passage vectors are reused. On held-out train queries the cosine "
        "between a Roman query and its Devanagari target rises from " + "%.3f" % scd.get("held_out_cosine_before", 0) +
        " to " + "%.3f" % after + ". The 250,002-token vocabulary is then pruned to the " +
        "{:,}".format(scd.get("vocab_pruned", 0)) + " tokens used by the corpus and train queries, and the model is "
        "quantised: " + "%.0f" % sizes.get("full_fp32", 0) + " MB → " + "%.0f" % sizes.get("pruned_int8", 0) + " MB.</p>"
        "<p><b>Learning to rank</b> (<span class=\"mono\">rerank/ltr.py</span>). A logistic regression over IR "
        "features of each candidate (BM25 per zone, proximity, tf-idf, dense cosine, reciprocal ranks, a static "
        "quality prior g(d) for the first passage of an article, length). Trained on train judgments.</p>"
        "<p><b>Gated cascade</b> (<span class=\"mono\">cascade/gate.py</span>). Features that the sparse stage gives "
        "for free (top score, score gap, NQC, share of words matched only through Dhvani, unmatched words, max idf, "
        "length, script) predict whether the neural stage will improve nDCG@10. The threshold is chosen on train as "
        "the fewest neural calls that keep 99% of the always-neural quality.</p>"
    )


def section_novelty(n):
    rows = [
        ["Evaluation", "average nDCG / P@k only", "Script Gap, cross-script consistency (RBO@10), worst-script nDCG"],
        ["Roman queries", "transliterate the query, then BM25 (B2)", "Dhvani zone in the index; no transliteration model"],
        ["df for variants", "each spelling has its own df", "pooled df across spellings (Pirkola-style)"],
        ["Neural stage", "always on, or absent", "run only when an IR-signal gate predicts it helps"],
        ["Model size", "off-the-shelf encoder", "script-consistency distillation + vocabulary pruning + int8"],
        ["Ranking signals", "fixed weights", "zone weights tuned on train; learning to rank over IR features"],
    ]
    html = "<h2>4. Novelty and creativity</h2>"
    html += "<p>The obvious T5 project (and the PDF's own sample idea) is a Hinglish engine that transliterates the "
    html += "query and ranks with BM25; that is our baseline B2. What is different:</p>"
    html += "<table><thead><tr><th>aspect</th><th>obvious baseline</th><th>LipiSetu</th></tr></thead><tbody>"
    for r in rows:
        html += "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (r[0], r[1], r[2])
    html += "</tbody></table>"
    html += ("<p><b>Prior art, honestly.</b> Mixed-script IR is not new (Gupta et al. 2014; FIRE MSIR) and Indic "
             "Soundex variants exist (e.g. libindic). We do not claim to be first. To our knowledge the combination "
             "here is new for Hindi on MIRACL: script invariance measured explicitly, a cross-script phonetic zone "
             "with pooled df inside a classic BM25 engine with a rule-by-rule ablation, and neural inference gated by "
             "IR signals and reported as a quality-versus-compute curve.</p>")
    return html


def section_evaluation(n, t, point, human):
    html = "<h2>5. Evaluation</h2>"
    html += ("<p><b>Setup.</b> Test: the 350 MIRACL-Hindi dev queries (3,494 judgments, about 2.1 relevant passages per "
             "query, so P@10 cannot exceed about 0.2 and nDCG@10 is our main metric). Every query is run in three "
             "forms: F1 the original Devanagari, F2 a standard Hinglish romanisation, F3 a casual romanisation with "
             "seeded spelling noise (<span class=\"mono\">text/romanize.py</span>). Tuning and training use only the "
             "1,169 train queries. Unjudged passages count as non-relevant. <b>Script Gap</b> = nDCG(F1) − nDCG(form); "
             "<b>CSC@10</b> = mean pairwise RBO (p = 0.9) between the top-10 lists of the three forms; "
             "<b>worst-script nDCG</b> = mean over queries of the lowest nDCG@10 among the forms.</p>")
    html += "<h3>Table 1. Effectiveness (dev, 350 queries)</h3>" + t["effectiveness"]
    html += "<h3>Table 2. Script invariance</h3>" + t["invariance"]
    html += ('<div class="two">' + figure("../../results/fig_ndcg_by_system.png", "Figure 2. nDCG@10 by system and query script.")
             + figure("../../results/fig_budget_curve.png", "Figure 3. Quality vs share of queries that run the neural stage.") + "</div>")
    html += ("<p><b>The Script Gap is real and large.</b> BM25 with stemming (B1) reaches " + n["b1_f1"] + " on "
             "Devanagari queries and " + n["b1_f2"] + " on the same questions in Roman script. The obvious fix, "
             "transliterating the query (B2), only recovers " + n["b2_f2"] + " / " + n["b2_f3"] + " (standard / casual "
             "Roman), because casual Hinglish spellings are not valid transliteration input (\"bharat\" becomes भरत, "
             "not भारत). Classic Soundex (S0) helps (" + n["s0_f2"] + ") but its 4-character English codes merge too "
             "much. The Dhvani zone (S1) reaches " + n["s1_f2"] + " / " + n["s1_f3"] + ", and with pooled df (S2) the "
             "casual-Roman Script Gap falls from " + n["b2_gap3"] + " (B2) to " + n["s2_gap3"] + ", while cross-script "
             "consistency rises from " + n["b2_csc"] + " to " + n["s2_csc"] + ". Every one of these Roman-query gains is "
             "significant (p &lt; 0.001).</p>"
             "<p><b>Neural models have their own script problem.</b> The base dense model (D0) is the best single "
             "system for Devanagari (" + n["d0_f1"] + ") but scores " + n["d0_f3"] + " on casual Roman: for a Roman "
             "query it retrieves other Roman-script passages, i.e. it matches the script before the meaning. "
             "Script-consistency distillation (D1) fixes part of this (" + n["d1_f3"] + ") at almost no cost on "
             "Devanagari (" + n["d1_f1"] + "), but stays far below the Dhvani zone on Roman queries. Plain fusion "
             "(H1) is best on Devanagari (" + n["h1_f1"] + ") but drags Roman queries down to " + n["h1_f2"] + ", so "
             "fusion alone is not script-invariant. Learning to rank (L1) uses both signals and is the best system "
             "on every script (" + n["l1_f1"] + " / " + n["l1_f2"] + " / " + n["l1_f3"] + "), with the highest "
             "worst-script nDCG (" + n["l1_worst"] + " vs " + n["b2_worst"] + " for B2).</p>"
             "<p><b>The gate spends neural compute where it helps.</b> Because the neural stage helps Devanagari "
             "queries and hurts many Roman ones, always running it (" + n["op_neural"] + " over all dev queries and "
             "forms) is worse than never running it (" + n["op_sparse"] + "). The gate, with its threshold chosen on "
             "train, runs the neural stage for " + n["op_share"] + " of queries and reaches " + n["op_ndcg"] + ", "
             "better than both extremes and well above a random gate with the same budget (Figure 3; an oracle "
             "reaches " + n["op_oracle"] + " at " + n["op_oracle_share"] + "). The cascade's median latency is " +
             n["g1_ms"] + " ms against " + n["h1_ms"] + " ms for always-hybrid and " + n["l1_ms"] + " ms for LTR.</p>"
             "<p><b>tf-idf vs BM25.</b> lnc.ltc (V1) scores " + n["v1_f1"] + " against " + n["b1_f1"] + " for BM25. "
             "Full cosine normalisation over-rewards short passages: the median length of V1's top passage is " +
             n["v1_len"] + " terms, against " + n["corpus_len"] + " for the corpus and " + n["b1_len"] + " for BM25, "
             "whose tuned b = 0.5 normalises length only partly (results/e13_length_bias.json).</p>"
             "<p><b>Pooled df.</b> On the Devanagari-only corpus pooled df trades a little Devanagari accuracy (" +
             n["s1_f1"] + " → " + n["s2_f1"] + ") for Roman accuracy and consistency. On the mixed-script corpus, "
             "where a word's df really is split between spellings, it helps every form (Table 4): standard Roman "
             + n["mixed_s1_f2"] + " → " + n["mixed_s2_f2"] + ", casual Roman " + n["mixed_s1_f3"] + " → " +
             n["mixed_s2_f3"] + ", consistency " + n["mixed_s1_csc"] + " → " + n["mixed_s2_csc"] + ".</p>"
             "<p><b>Ablation.</b> Dropping vowels is by far the most important Dhvani rule, followed by merging "
             "retroflex and dental sounds (Table 3). Collapsing doubled letters slightly hurts; we keep the rule set "
             "fixed as designed rather than tune it on the test queries.</p>")
    html += "<h3>Table 3. Dhvani rule ablation (one rule switched off, Dhvani zone rebuilt)</h3>" + t["ablation"]
    html += "<h3>Table 4. Pooled df on a mixed-script corpus (30% of passages romanised, synthetic)</h3>"
    html += '<div class="two"><div>' + t["mixed"] + "</div><div>" + t["idf"] + "</div></div>"
    html += "<h3>Table 5. Efficiency structures</h3>" + t["structures"]
    html += ("<p class=\"small\">Skip pointers halve the comparisons of AND merges. Champion lists are 5-6x "
             "faster but lose a lot of quality, mostly for Roman queries whose Dhvani postings are long. Cluster "
             "pruning scores about 5% of the vectors and keeps half of the exact top 100, but on this laptop it is "
             "not faster: one numpy dot product over all 110k vectors already takes only a few milliseconds, so "
             "collecting the followers costs as much as it saves. It should only pay off on a much larger "
             "collection. In pure Python the heap top-K is slower than numpy's C sort even though it is "
             "asymptotically better.</p>")
    html += ("<p><b>Significance.</b> Paired randomisation tests (10,000 permutations, nDCG@10, appendix D) give "
             "p &lt; 0.001 for every Roman-query gain listed above (S1 over B1 and S0, S3 over B2, D1 over D0, L1 and "
             "G1 over H1) and for H1 over S3 on Devanagari. On Devanagari queries the sparse systems are not "
             "significantly different from B1/B2 (no loss), and G1 is not significantly different from the "
             "always-hybrid H1, even though it runs the neural stage for only a third of the queries.</p>")
    if human:
        html += ("<p><b>Human query set.</b> Three team members romanised the same 60 dev queries independently "
                 "(no transliteration tools), and each wrote code-mixed and English versions of 20 of them. All three "
                 "spelled a word identically for " + pct(human.get("same_spelling_all_three", 0)) + " of words, but the "
                 "Dhvani keys agreed for " + pct(human.get("same_dhvani_key_all_three", 0)) + ". On the real "
                 "romanisations BM25 reaches only " + n["hum_b1_r"] + " and transliteration " + n["hum_b2_r"] +
                 ", while S3 reaches " + n["hum_s3_r"] + " (p ≤ " + n["hum_p_s3_b2"] + " against B2 for every "
                 "annotator) and learning to rank " + n["hum_l1_r"] + " (p ≤ " + n["hum_p_l1_h1"] + " against H1). "
                 "So the synthetic results hold for real spelling variation. Code-mixed and English queries are "
                 "different: a phonetic key cannot link <i>leader</i> to नेता, so S3 drops to " + n["hum_s3_cm"] +
                 " (code-mixed) and " + n["hum_s3_en"] + " (English), and only the dense stage helps (D1 " +
                 n["hum_d1_en"] + " on English, L1 " + n["hum_l1_cm"] + " on code-mixed). The gate was trained on "
                 "Devanagari and romanised queries only, and it under-calls the neural stage here: G1 is below the "
                 "always-hybrid H1 on code-mixed (" + n["hum_g1_cm"] + " vs " + n["hum_h1_cm"] + ", p = " +
                 n["hum_p_g1_h1_cm"] + ") and English (" + n["hum_g1_en"] + " vs " + n["hum_h1_en"] + ", p = " +
                 n["hum_p_g1_h1_en"] + ").</p>" + t["human"])
    return html


def section_limitations(n):
    return (
        "<h2>6. Limitations and next steps</h2><ul>"
        "<li>The corpus is a subsample of MIRACL-Hindi (all judged passages + a random sample), so absolute scores are "
        "not comparable to the MIRACL leaderboard; unjudged passages count as non-relevant.</li>"
        "<li>The Roman query forms and the mixed-script corpus are synthetic (my romaniser); the human query set is "
        "the realistic check.</li>"
        "<li>Dhvani merges some different words: <i>kal</i> (कल, yesterday) and खेल (khel, game) share the key KL, "
        "because aspiration and vowels are dropped. Words whose spoken form drops a vowel (कमला / kamla) get different "
        "keys. Zone weights limit the damage but do not remove it.</li>"
        "<li>English words inside code-mixed queries are only matched by the dense stage, and the gate never saw "
        "code-mixed or English queries in training, so it runs the dense stage too rarely for them.</li>"
        "<li>The human set is small (60 queries), and one annotator (me) designed the Dhvani key, so that "
        "romanisation is not blind.</li>"
        "<li>Hindi only.</li></ul>"
        "<p><b>Course-project roadmap.</b> (1) Bengali and Telugu from MIRACL with per-language Dhvani tables; "
        "(2) a larger human query set and voice queries; (3) the int8 encoder in the browser with ONNX Runtime Web, so "
        "search runs fully on the device; (4) learned key rules instead of hand-written ones; (5) a short paper for "
        "FIRE.</p>"
    )


def section_work_division():
    return (
        "<h2>7. Work division</h2>"
        "<p><b>Devansh Pandey</b>: idea and system design; text pipeline, inverted index, Boolean/phrase, tf-idf, BM25, "
        "proximity, top-K and champion lists; the Dhvani key and pooled df; dense retrieval, script-consistency "
        "distillation, vocabulary pruning, cluster pruning; learning to rank; the gated cascade; the evaluation "
        "framework and metrics; the demo; the report. <b>Anamika Pal</b>: annotated the human query set (60 romanised "
        "queries, code-mixed and English versions of rows 21–40); analysed the annotator-agreement results and "
        "presents them in the video. <b>Abhinav Bachchas</b>: annotated the human query set (60 romanised queries, "
        "code-mixed and English versions of rows 41–60); reviewed the final results and plots and proofread the "
        "report; presents the results and the live limitation in the video.</p>"
    )


def section_ai():
    return (
        "<h2>AI-use declaration</h2>"
        "<p>We used Claude Code (an AI coding assistant by Anthropic) to help brainstorm and plan the project, write "
        "and refactor code, write tests, run the experiments and draft documentation. Devansh chose the track and the final idea, directed "
        "the work, reviewed the code and checked the results. The human query annotations were written without AI "
        "tools. Every number in this report was produced by the scripts in the repository on the real data.</p>"
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
    return html + "</ol><p class=\"small\">Data: MIRACL (Apache-2.0), passage text from Wikipedia (CC BY-SA 3.0). "\
        "Model: intfloat/multilingual-e5-small (MIT).</p>"


def section_appendix(t, params):
    return (
        '<h2 class="pb">Appendix</h2>'
        "<h3>A. Query latency per system (laptop CPU, Intel i5-12450H, no GPU)</h3>" + t["efficiency"]
        + '<div class="two"><div><h3>B. Learning-to-rank weights</h3>' + t["ltr"] + "</div>"
        + "<div><h3>C. Gate weights</h3>" + t["gate"] + "</div></div>"
        + "<h3>D. Significance (paired randomisation test, 10,000 permutations, nDCG@10)</h3>" + t["significance"]
        + '<div class="two">' + figure("../../results/fig_zipf.png", "Zipf plot of the corpus.")
        + figure("../../results/fig_idf_hist.png", "idf distribution of the vocabulary.") + "</div>"
        + figure("../../results/fig_dhvani_ablation.png", "Dhvani rule ablation (CSC@10).", "70%")
    )
