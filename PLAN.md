# LipiSetu: Script-Invariant Hindi Search

> **लिपि (lipi)** = script, **सेतु (setu)** = bridge.
> **Track:** T5, Multilingual and Indic-language search
> **One line:** If someone types *"kal ka mausam"* in Roman letters, they should get the same results as someone who types *"कल का मौसम"*. Today they don't. I **measure** that gap, **close** it with classic IR, and **run neural models only when the IR signals say they are needed**.

**Status: built.** Everything in phases P1–P9 is implemented and evaluated; see `README.md` for the results and `docs/report/LipiSetu_report.pdf` for the report. The human query set (3 annotators × 60 queries) is in and evaluated. Remaining before submission: the video, its link in the report, the "what actually happened" work-division table, and the fresh-clone check (§9–10).

This is my master plan for the hackathon. Every section maps to marks in the rubric (`Hackathon file/CSD358 IR Mid-term Assignment 2026.pdf`).

---

## 0. Summary

| Item | Decision |
|---|---|
| Problem | Most Hindi users type in Roman script, with inconsistent spellings (*mausam / mosam / mousam*). Search built on Devanagari text serves them worse. I call this loss the **Script Gap**. |
| Core engine | My own BM25 + tf-idf engine: Hindi normalisation, stemmer, positional inverted index with zones, skip pointers, proximity scoring |
| Idea 1 (IR) | **Dhvani key** (ध्वनि = sound): a phonetic key that maps Devanagari *and* Roman spellings of a word to the same code. It's stored as its own **zone** of the index, with **pooled document frequency** across spelling variants. |
| Idea 2 (evaluation) | **Script invariance** as a thing to measure: the Script Gap, **Cross-Script Consistency** (RBO overlap between the rankings for different scripts) and **worst-script nDCG**. Not just an average score. |
| Idea 3 (data) | A **human Hinglish query set**: 3 people romanise the same queries independently, which captures real spelling variation |
| Idea 4 (inference) | A **confidence-gated cascade**: the neural encoder runs only when IR signals predict that sparse retrieval failed. I report quality vs. % of queries that needed neural inference. |
| Idea 5 (model) | **Script-Consistency Distillation (SCD)**: a small query encoder trained so romanised queries land on the same embedding as the Devanagari query. Then I prune its vocabulary and quantise it to int8 ONNX for on-device use. |
| Idea 6 (ranking) | **Learning-to-rank** over IR features (surface BM25, Dhvani BM25, tf-idf cosine, proximity, title match, dense cosine, static quality g(d)) |
| Data | MIRACL-Hindi (Wikipedia passages with human relevance labels): 350 dev queries for testing, 1,169 train queries for tuning and training |
| Interface | A command-line tool with `--explain` (shows postings, idf, Dhvani keys, scores per stage) + a hand-written web demo (FastAPI + one HTML/CSS/JS page) for the video. **The UI is not graded**, so it only displays what the engine returns. |

---

## 1. Problem and track relevance (report §1, track marks 5)

**User need.** Most Hindi speakers type Hindi on their phones in **Roman script**, and spell the same word in many ways. Most Hindi content (Wikipedia, news, government pages) is in **Devanagari**. A normal index matches exact terms, so *"mosam"* finds nothing about *"मौसम"*. These users quietly get worse results.

**Why it's a T5 research problem.** It's exactly the track's theme: code-mixed text, transliteration, a low-resource language. My design covers **every IR hook the PDF lists for T5**:

| T5 hook in the PDF | Where I cover it |
|---|---|
| Tokenisation and normalisation for non-English scripts | Devanagari normaliser (nukta, chandrabindu/anusvara, ZWJ/ZWNJ, Devanagari digits) + a script-aware tokenizer |
| Stemmers for Indic languages, compared with no stemming | Light Hindi suffix stemmer; experiment with stemming on and off |
| Soundex-style phonetic matching for transliterated spellings | **Dhvani key**, compared against classic English Soundex |
| How stop words and idf behave on a Hindi corpus | Corpus analysis: Zipf plot, highest-df terms, idf histogram, stop-list from df vs. a standard list |
| Cross-lingual ranking with the vector space model | tf-idf VSM within a script; multilingual embedding space (cosine) for English and code-mixed queries |

**Papers I'll cite (I'll check each one before the final report):**
- Zhang et al., *MIRACL: A Multilingual Retrieval Dataset Covering 18 Diverse Languages*, TACL 2023. My dataset.
- Gupta, Bali, Banchs, Choudhury, Rosso, *Query Expansion for Mixed-Script Information Retrieval*, SIGIR 2014. **Closest prior work**; I explain how mine differs.
- Sequiera et al., *Overview of FIRE-2015 Shared Task on Mixed Script Information Retrieval*.
- Pirkola, *The effects of query structure and dictionary setups in dictionary-based cross-language IR*, SIGIR 1998. The basis for pooled df.
- Webber, Moffat, Zobel, *A Similarity Measure for Indefinite Rankings* (RBO), ACM TOIS 2010.
- Robertson & Zaragoza, *The Probabilistic Relevance Framework: BM25 and Beyond*, 2009.
- Cormack, Clarke, Büttcher, *Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods*, SIGIR 2009.
- Shtok, Kurland, Carmel et al., *Predicting Query Performance by Query-Drift Estimation* (NQC). Used for the gate features.
- Wang, Lin, Metzler, *A Cascade Ranking Model for Efficient Ranked Retrieval*, SIGIR 2011.
- Liu, *Learning to Rank for Information Retrieval*, 2009.
- Reimers & Gurevych, *Making Monolingual Sentence Embeddings Multilingual using Knowledge Distillation*, EMNLP 2020. **The basis for SCD**; I apply it to script variants.
- Abdaoui et al., *Load What You Need: Smaller Versions of Multilingual BERT*, 2020. Vocabulary pruning.
- Ramanathan & Rao, *A Lightweight Stemmer for Hindi*, 2003.
- Wang et al., *Multilingual E5 Text Embeddings: A Technical Report*, 2024.
- Manning, Raghavan, Schütze, *Introduction to Information Retrieval*. The course textbook.

---

## 2. Novelty (10 marks, and the reason I stand out)

### 2.1 What most other teams will build
Many T5 teams will paste the PDF into an AI coding assistant and get the PDF's own sample idea:

> "Hinglish query engine: transliterate Roman to Devanagari, BM25/tf-idf, maybe a multilingual embedding hybrid, P@k with and without stemming."

The PDF says *"building one exactly as written will score low on novelty."* In my project that pipeline is only the **baseline (B2)**.

### 2.2 What I do differently

| # | Contribution | Why it isn't the obvious build |
|---|---|---|
| N1 | **Script invariance as an evaluation target**: Script Gap, CSC@10 (pairwise RBO between top-10 lists across scripts) and worst-script nDCG@10 | Others report *average* accuracy. I report whether the *same information need gets the same answer* in every script. |
| N2 | **Dhvani key**: a phonetic key designed for Hindi. It collapses aspiration, nukta, retroflex/dental, w/v, z/j and vowel length, and handles silent inherent vowels. Stored as a **separate weighted zone**. I also run an **ablation of each rule** and compare against classic Soundex. | Not plain Soundex and not a transliteration model. A tiny, explainable classic IR structure with no network calls. |
| N3 | **Pooled-df idf across spelling and script variants** (Pirkola-style, applied to spelling variants instead of translations) | I show a specific problem: in a mixed-script corpus a word's df is **split** across its spellings, so each spelling looks rare and gets an inflated idf. Then I fix it. |
| N4 | **Human multi-annotator Hinglish query set**: 3 people romanise the same 60 queries independently, plus code-mixed and English versions | Real spelling variation instead of synthetic only. I can *measure* how inconsistent real romanisation is. |
| N5 | **Confidence-gated neural cascade** using query-performance signals, compared against a **random gate with the same budget** | Others either always run the neural model or never do. I treat compute as a trade-off: *"X% of the hybrid's quality at Y% of the neural calls"*. |
| N6 | **SCD + vocabulary pruning + int8 ONNX**: a small script-invariant query encoder | Reimers & Gurevych's idea applied to a new kind of variation (script and spelling, not language), with a focus on model size (like my LightDep work). |
| N7 | **Cluster pruning (leaders/followers) on dense vectors**: a lecture concept used for approximate neural search instead of a black-box vector library | It connects the scoring lecture to neural retrieval and shows the speed-vs-recall trade-off clearly. |

### 2.3 Honest prior-art statement (goes in the report)
- Mixed-script IR is **not new** (Gupta et al. 2014; FIRE MSIR 2015/16). I don't claim to be first.
- Indic Soundex variants exist (e.g. the libindic Soundex library). I don't claim to have invented phonetic keys for Indic text.
- **What I claim:** (a) explicit evaluation of script invariance with RBO, worst-script nDCG and the Script Gap on human romanisations; (b) a cross-script phonetic zone **with pooled df** inside a classic BM25/VSM engine, with a rule-by-rule ablation; (c) neural inference gated by IR signals, measured as a quality-vs-compute curve; (d) a distilled script-invariant query encoder. To my knowledge this *combination and evaluation framing* hasn't been done for Hindi on MIRACL. I write "to my knowledge", never "first ever".

### 2.4 Claims I must NEVER make
- "State of the art on MIRACL." My corpus is a subsample, so my numbers aren't comparable to the leaderboard.
- Any number not produced by a script in `scripts/` and saved in `results/`.
- "Works for all Indian languages." It's Hindi only; others go in the roadmap.

---

## 3. System design

```
                    ┌──────────────────────── OFFLINE (index time) ────────────────────────┐
 MIRACL-hi passages │ normalise → tokenise → stop-list → stem ──► positional inverted index │
 (subsample ~100k)  │                    └──► Dhvani key ──────► Dhvani zone postings       │
                    │ zones: title / body / dhvani · df, idf, doc lengths · skip pointers   │
                    │ dense passage vectors (multilingual-e5-small, int8 ONNX)              │
                    │ cluster pruning: √N leaders, each passage attached to nearest leader  │
                    └───────────────────────────────────────────────────────────────────────┘

 query (any script) ─► script detector (Devanagari / Roman / mixed)
                     ─► normalise + tokenise + stem      ─► surface-zone terms
                     ─► Dhvani key per token             ─► Dhvani-zone terms (pooled df)
                     ─► SPARSE: BM25 (main) / tf-idf lnc.ltc cosine (VSM comparison)
                        zone weights · proximity · heap top-K · champion lists
                     ─► GATE (logistic regression on IR signals) ──no──► results
                                     │ yes
                                     ▼
                        DENSE: SCD query encoder (int8) · cluster-pruned cosine top-K
                     ─► RRF fusion or learning-to-rank re-ranker ─► results
 --explain prints: tokens, normalised forms, Dhvani keys, postings excerpts, df/idf,
                   per-zone scores, proximity, gate features + decision, dense scores, final rank
```

**What a document is.** One MIRACL passage = one document, keyed by `<article_id>#<passage_no>`, with zones **title** and **body**. I use passages because the MIRACL labels are per passage, and passages keep length normalisation meaningful.

**Corpus size.** Every passage judged for dev or train queries, plus about 100k random passages (fixed seed). That's big enough that ranking matters. Every system uses the same subsample, so comparisons are fair. I state the subsampling as a limitation.

---

## 4. Use of IR principles (30 marks, the biggest block)

The full map (concept → file → why → how it shows in the video) is in `docs/IR_CONCEPTS.md`. Summary:

| Lecture topic | What I implement **myself** |
|---|---|
| Boolean retrieval | Inverted index (dictionary + postings), AND/OR/NOT with postings intersection, terms processed in order of increasing df |
| Term vocabulary and postings | What a document is, tokenisation, Devanagari normalisation, case folding, stop words, Hindi stemmer, Soundex + **Dhvani key**, **skip pointers**, positional index + phrase queries, precision/recall |
| tf-idf and VSM | log tf, idf, **lnc.ltc**, length normalisation, cosine; Jaccard for spelling-variant analysis |
| Scoring and result assembly | Heap top-K, **champion lists**, **zone index** with tuned zone weights, **static quality g(d) and net score**, **query-term proximity**, **cluster pruning**, query parser, the complete system |
| Beyond the syllabus (extra points) | **BM25**, **dense retrieval**, **learning-to-rank**, RRF, gated cascade, distillation |

**Rule:** the core engine is my own code. Libraries are only for loading data, making *synthetic* query variants, running the neural encoder, ONNX, the small logistic-regression models, plots, and **reference checks in tests**. I explain each library's role in IR terms in the report, as the PDF asks.

---

## 5. Evaluation (15 marks)

The full protocol is in `docs/EVALUATION.md`. Summary:
- **Test:** MIRACL-hi **dev** (350 queries, 3,494 judgments, 752 relevant). **Never** used for tuning.
- **Tuning and training:** MIRACL-hi **train** (1,169 queries).
- **Query forms:** Devanagari, standard romanisation, casual romanisation (seeded noise), and the human set (3 romanisations + code-mixed + English for 60 dev queries).
- **Metrics:** nDCG@10 (main), P@5, P@10, Recall@100, MRR@10, plus Script Gap, CSC@10 and worst-script nDCG@10. Efficiency: latency, index size, model size, % neural calls.
- **Statistics:** paired randomisation test for the headline comparisons.
- **P@10 ceiling:** about 2.1 relevant passages per query means P@10 can't exceed about 0.2. I explain this so it doesn't look "low".

---

## 6. Rubric → plan (100 marks)

| Criterion (marks) | Full marks needs | My plan |
|---|---|---|
| Use of IR principles (30) | Correct, explained, integrated | §4 + `docs/IR_CONCEPTS.md`; `--explain` shows real postings, idf and scores live |
| Working system (20) | Runs live on real input; README reproduces it | Command-line tool + web demo on the real corpus; scripts rebuild everything from a fresh clone; tests; no hard-coded outputs |
| Evaluation (15) | Judged queries, P/R/P@k, a baseline | 350 judged queries × 3 forms + 60 human × 5 forms; 4+ baselines; ablations; significance; plots |
| Novelty (10) | New vs. the baseline and existing tools | N1–N7 + honest prior art |
| Track relevance (5) | Directly addresses T5 | Every T5 hook covered (§1) |
| Report (10) | Explains IR, why it matters, novelty, next steps | `docs/REPORT_OUTLINE.md` |
| Video (10) | Clear demo + explanation | `docs/VIDEO_SCRIPT.md` |

---

## 7. Build phases

This runs in a Claude Code cloud session, so the build can keep going while my laptop is closed. **Everything is still built inside the official 36-hour window** (the PDF says *"Build it within the 1.5-day window"*). The cloud session just lets far more get done inside that window. My own time goes to directing, reviewing, annotating, the report and the video.

Each phase ends in a **working, tested, committable state**, so there's always something I can submit.

| Phase | What gets built | Done when |
|---|---|---|
| P1 Setup + data | `requirements.txt`, download script, corpus subsample, train/dev split files | Data on disk; counts match `docs/DATA.md` |
| P2 Text pipeline | normaliser, tokenizer, stop words, Hindi stemmer, script detector, Soundex, Dhvani key | Unit tests pass (incl. `"हिन्दी"` → one token) |
| P3 Index + retrieval | positional inverted index with zones, skip pointers, Boolean + phrase, tf-idf lnc.ltc, BM25, heap top-K, champion lists, proximity, command-line tool with `--explain` | Devanagari search works end to end. **First submittable state.** |
| P4 Evaluation | synthetic query forms, all metrics incl. RBO/Script Gap/CSC/worst-script, baselines B0–B2, results CSVs | First real numbers in `results/` |
| P5 Novelty core | Dhvani zone (S1), pooled df on a mixed-script corpus (S2), proximity (S3), Dhvani rule ablation, Soundex comparison, stemming and stop-word experiments, zone weights + BM25 k1/b tuned on **train** | Script Gap closes measurably (or I report honestly that it doesn't) |
| P6 Neural | dense e5-small int8 ONNX, cluster pruning, RRF hybrid, **SCD** student + vocabulary pruning | Dense results + model size/latency table |
| P7 Ranking + cascade | learning-to-rank re-ranker (logistic regression over IR features, trained on train), gated cascade vs. random gate | Budget curve plot |
| P8 Human set + final eval | merge human annotations, run everything, significance tests, all plots | Final `results/` |
| P9 Demo + docs | Web demo page, README filled from real results, report draft from `docs/REPORT_OUTLINE.md`, video run-through | Fresh-clone reproduction test passes |

**Optional extras if time allows:** neural transliteration baseline (AI4Bharat IndicXlit); a browser demo of the int8 encoder using ONNX Runtime Web; a second language from MIRACL (Bengali or Telugu) to show the method generalises.

**If something breaks or runs late, cut in this order:** optional extras → web demo polish → cluster pruning → learning-to-rank → SCD → cascade → dense. **Never cut** evaluation, the README or `--explain`.

---

## 8. Risks

| Risk | Fix |
|---|---|
| Dhvani merges too many words (hurts precision) | Separate zone with a **tuned lower weight**; measure collisions; per-rule ablation; show it as a limitation |
| Synthetic romanisation isn't realistic | The human set (N4) is the realistic test; synthetic forms are a controlled stress test |
| Test leakage | Tune and train on **train** only (rule in `CLAUDE.md`) |
| P@10 looks low | Explain the ceiling; nDCG@10 is the main metric |
| Python `\w` breaks Devanagari words | Script-aware tokenizer + unit test |
| No GPU in the cloud session | e5-small int8 on 4 CPU cores is fine for about 100k passages; SCD trains on short queries only, so it runs on CPU |
| The cloud container gets reset | Data is re-downloadable by script; each phase ends in a committable state |
| Video over 8 minutes | Script is timed at about 7:30 |

---

## 9. Deliverables checklist (from the PDF)

- [ ] **Repo** + README: setup, how to run, data source, what works and what's planned
- [ ] **Video**, 5–8 min, unlisted, live, **no slides**, every member explains their part, one limitation shown
- [ ] **Report PDF**, ≤ 8 pages + references/appendix: 7 sections, pipeline diagram, work division, AI-use declaration
- [ ] One submission form per team, before the deadline

## 10. Rules check

- [ ] Built inside the 36-hour window (commit history shows it)
- [ ] No code copied from VidhiVault or any online repo
- [ ] No crawling (robots.txt not needed); if added later: obey robots.txt + delays
- [ ] No personal data; every dataset and model credited (`docs/DATA.md`)
- [ ] AI-use declaration is short and truthful (`docs/AI_USE.md`)
- [ ] Nothing faked or hard-coded; every number comes from `results/`
