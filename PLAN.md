# LipiSetu: Script-Invariant Hindi Search

> **लिपि (lipi)** = script, **सेतु (setu)** = bridge.
> **Track:** T5, Multilingual and Indic-language search
> **One line:** Someone who types *"kal ka mausam"* in Roman letters should get the same search results as someone who types *"कल का मौसम"*. Today they don't. We **measure** that gap, **close** it with classic IR, and **use neural inference only when IR signals say it is needed**.

This is the master plan. Read it fully before writing any code. Every section maps to a mark in the rubric (`Hackathon file/CSD358 IR Mid-term Assignment 2026.pdf`).

---

## 0. TL;DR

| Item | Decision |
|---|---|
| Problem | Hindi users mostly type in Roman script, with inconsistent spellings (*mausam / mosam / mousam*). Search systems built on Devanagari text give them worse results. We call this loss the **Script Gap**. |
| Core system | A BM25 + tf-idf engine written from scratch, with Hindi normalisation, a stemmer, a positional inverted index and zones |
| Key idea 1 (IR) | **Dhvani key** (ध्वनि = sound): a phonetic key that maps Devanagari *and* Roman spellings of a word to the same code. It is indexed as its own **zone**, with **pooled document frequency** across spelling variants. |
| Key idea 2 (evaluation) | A new axis to evaluate: **script invariance**. We report the Script Gap, **Cross-Script Consistency (RBO between rankings)** and the **worst-script nDCG**, not just the average. |
| Key idea 3 (data) | A **human-written Hinglish query set**: 3 teammates each romanise the same queries independently, which captures natural spelling variation. |
| Key idea 4 (inference) | A **confidence-gated cascade**. A small neural encoder runs only when IR signals (score gap, NQC, Dhvani-only matches) predict that sparse retrieval failed. We report quality vs. % of queries that needed neural inference. |
| Key idea 5 (stretch) | **Script-Consistency Distillation (SCD)**: fine-tune a small query encoder so that romanised queries map to the same embedding as the Devanagari query. Then prune its vocabulary and quantise it to int8 ONNX for on-device use. |
| Data | MIRACL-Hindi (Wikipedia passages with human relevance labels): 350 dev queries for testing, 1,169 train queries for tuning and training |
| Interface | A command-line tool with an `--explain` mode that prints postings, idf, Dhvani keys and per-stage scores. Optional thin Streamlit page. **The UI is not graded.** |

---

## 1. Problem and track relevance (report §1, track marks 5)

**User need.** Most Hindi speakers type Hindi on phones in **Roman script** (Hinglish), and they spell the same word in many ways. Most Hindi content (Wikipedia, news, government pages) is in **Devanagari**. A standard index matches exact terms, so *"mosam"* finds nothing about *"मौसम"*. Those users silently get worse results.

**Why it is a T5 research problem.** It is exactly the track's theme: code-mixed text, transliteration and a low-resource language. Our design touches **every IR hook listed for T5**:

| T5 hook in the PDF | Where we address it |
|---|---|
| Tokenisation and normalisation for non-English scripts | Devanagari normaliser (nukta, chandrabindu/anusvara, ZWJ/ZWNJ, Devanagari digits) + a script-aware tokenizer |
| Stemmers for Indic languages, compared with no stemming | Lightweight Hindi suffix stemmer; ablation with stemming on and off |
| Soundex-style phonetic matching for transliterated spellings | **Dhvani key**, a cross-script phonetic key used as an index zone |
| How stop words and idf behave on a Hindi corpus | Corpus analysis: Zipf plot, highest-df terms, idf distribution, stop-list derived from df vs. a standard list |
| Cross-lingual ranking with the vector space model | tf-idf VSM for same-language matching; multilingual embedding space (cosine) for English and code-mixed queries |

**Papers to cite (verify each before the final report):**
- Zhang et al., *MIRACL: A Multilingual Retrieval Dataset Covering 18 Diverse Languages*, TACL 2023. Our dataset.
- Gupta, Bali, Banchs, Choudhury, Rosso, *Query Expansion for Mixed-Script Information Retrieval*, SIGIR 2014. **Closest prior work**; we must cite it and explain how we differ.
- Sequiera et al., *Overview of FIRE-2015 Shared Task on Mixed Script Information Retrieval*. Shows the problem is recognised.
- Pirkola, *The effects of query structure and dictionary setups in dictionary-based cross-language IR*, SIGIR 1998. The basis for pooled df.
- Webber, Moffat, Zobel, *A Similarity Measure for Indefinite Rankings* (RBO), ACM TOIS 2010. Our consistency metric.
- Robertson & Zaragoza, *The Probabilistic Relevance Framework: BM25 and Beyond*, 2009.
- Cormack, Clarke, Büttcher, *Reciprocal Rank Fusion…*, SIGIR 2009.
- Shtok, Kurland, Carmel et al., query performance prediction with NQC (*Predicting Query Performance by Query-Drift Estimation*). Used for the gate features.
- Wang, Lin, Metzler, *A Cascade Ranking Model for Efficient Ranked Retrieval*, SIGIR 2011.
- Reimers & Gurevych, *Making Monolingual Sentence Embeddings Multilingual using Knowledge Distillation*, EMNLP 2020. **The basis for SCD**; we apply it to *script variants*.
- Abdaoui et al., *Load What You Need: Smaller Versions of Multilingual BERT*, 2020. Vocabulary pruning.
- Ramanathan & Rao, *A Lightweight Stemmer for Hindi*, 2003.
- Wang et al., *Multilingual E5 Text Embeddings: A Technical Report*, 2024.
- Manning, Raghavan, Schütze, *Introduction to Information Retrieval*. The course textbook.

---

## 2. Novelty (10 marks, and the reason we stand out)

### 2.1 What most other teams will build (and why that scores low)
Many teams in T5 will paste the PDF into an AI coding assistant. The obvious result is the PDF's own sample idea:

> "Hinglish query engine: transliterate Roman to Devanagari, BM25 or tf-idf, maybe add a multilingual embedding model plus a hybrid, report P@k with and without stemming."

The PDF itself says *"building one exactly as written will score low on novelty."* That pipeline is our **baseline (B2/B3)**, not our system.

### 2.2 What we do that is different

| # | Contribution | Why it's different from the obvious build | Tier |
|---|---|---|---|
| N1 | **Script invariance as an evaluation target.** Metrics: **Script Gap** (nDCG on Devanagari minus nDCG on each other script), **CSC@10** (mean pairwise Rank-Biased Overlap of top-10 lists across scripts for the same query) and **worst-script nDCG@10** | Others report *average* effectiveness. We report whether the *same information need* gets the *same answer* in every script, a fairness-style view of search. | MUST |
| N2 | **Dhvani key**: a phonetic key designed for Hindi that maps Devanagari and Roman spellings to one code. It collapses aspiration, nukta, retroflex/dental, w/v, z/j and vowel length, and handles inherent-vowel (schwa) deletion naturally. It is indexed as a **separate zone with its own weight**. | Not plain English Soundex, not a transliteration model, and no network calls. It's a classic IR structure (a phonetic dictionary in the inverted index) that is explainable and tiny. | MUST |
| N3 | **Pooled-df idf across spelling and script variants**, i.e. Pirkola-style structured queries applied to *spelling variants*, not dictionary translations | We point out a specific failure: when a corpus mixes scripts, a word's df is **split** across its spellings, so each spelling looks rare and its idf is inflated. We show this and fix it. | SHOULD |
| N4 | **Human multi-annotator Hinglish query set.** 3 people romanise the same 60 queries **independently**, plus code-mixed and English versions | Real, natural spelling variation rather than synthetic transliteration. We can *quantify* how inconsistent real romanisation is (annotator edit distance), which motivates the whole project. | MUST |
| N5 | **Confidence-gated neural cascade.** A small logistic model uses IR signals (top-1 vs. top-10 score gap, NQC, fraction of terms matched only through Dhvani, out-of-vocabulary rate, max idf) to decide per query whether to run the neural encoder. It is compared against a **random gate with the same budget**. | Others either always run the neural model or never do. We present compute as a trade-off: *"X% of the hybrid's quality at Y% of the neural calls"*. This matches your inference background. | SHOULD |
| N6 | **Script-Consistency Distillation (SCD) + vocabulary pruning + int8 ONNX.** The student query encoder learns student(romanised query) ≈ teacher(Devanagari query). Its 250k-token vocabulary is pruned to the tokens our corpus actually uses. | Uses Reimers & Gurevych's idea for a new kind of variation (script and spelling, not language), with a LightDep-style focus on model size. | STRETCH |

### 2.3 Honest prior-art statement (put this in the report)
- Mixed-script IR is **not new** (Gupta et al. 2014; FIRE MSIR 2015/2016). We do **not** claim to be the first.
- Indic Soundex variants exist (e.g. the libindic Soundex library). We do **not** claim to have invented phonetic keys for Indic text.
- **Our claim:** (a) we evaluate script invariance explicitly with RBO, worst-script nDCG and the Script Gap on human romanisations; (b) a cross-script phonetic zone **with pooled df**, inside a classic BM25/VSM engine; (c) neural inference gated by IR signals and measured on a quality-vs-compute curve. To our knowledge this *combination and evaluation framing* has not been done for Hindi on MIRACL. Say "to our knowledge", never "first ever".

### 2.4 Claims we must NEVER make
- "State of the art on MIRACL." We use a subsampled corpus, so our numbers are not comparable to the leaderboard.
- Any number that is not produced by a script in `scripts/` and saved in `results/`.
- "Works for all Indian languages." It is Hindi only; other languages go in the roadmap.

---

## 3. System design

```
                    ┌──────────────────────── OFFLINE (index time) ────────────────────────┐
 MIRACL-hi passages │ normalise → tokenise → stop-list → stem ──► positional inverted index │
 (subsample ~100k)  │                    └──► Dhvani key ──────► Dhvani zone postings       │
                    │ title zone / body zone / dhvani zone · df, idf, doc lengths          │
                    │ [SHOULD] dense passage embeddings (multilingual-e5-small, int8 ONNX)  │
                    └───────────────────────────────────────────────────────────────────────┘

 query (any script) ─► script detector (Devanagari / Roman / mixed)
                     ─► normalise + tokenise + stem      ─► surface-zone terms
                     ─► Dhvani key per token             ─► Dhvani-zone terms (pooled df)
                     ─► SPARSE SCORER: BM25 (main) / tf-idf lnc.ltc cosine (VSM comparison)
                        zone-weighted sum · heap top-K · champion lists (efficiency)
                     ─► GATE (logistic regression on IR signals) ──no──► results
                                     │ yes
                                     ▼
                        DENSE: query encoder (e5-small int8, or SCD student) · cosine top-K
                     ─► RRF fusion (sparse ⊕ dense) ─► results
 --explain prints: tokens, normalised forms, Dhvani keys, postings excerpts, df/idf,
                   per-zone scores, gate features + decision, dense scores, fused rank
```

**Corpus decision ("what is a document").** One MIRACL passage = one document, keyed by its id (`<article_id>#<passage_no>`), with zones **title** and **body**. Passages rather than whole articles, because MIRACL relevance labels are per passage and passages keep length normalisation meaningful.

**Corpus size.** All passages judged for dev and train queries, plus about 100k random passages from the 2 MIRACL-hi shards (seed fixed). That is big enough that ranking matters, and small enough for a laptop. Every system is compared on the same subsample, so comparisons are fair. The subsampling is stated as a limitation.

---

## 4. Use of IR principles (30 marks, the largest block)

Full mapping (concept → code location → why → how it's shown in the video) lives in `docs/IR_CONCEPTS.md`. Summary:

| Lecture topic | Concepts we implement **from scratch** |
|---|---|
| Boolean retrieval | Inverted index (dictionary + postings), AND/OR/NOT with postings intersection, processing terms in order of increasing df |
| Term vocabulary and postings | Defining the document, tokenisation, Devanagari normalisation, case folding (Roman), stop words, Hindi stemmer, **Soundex-style Dhvani key**, positional index + phrase queries, precision and recall |
| tf-idf and VSM | log tf, idf, **lnc.ltc** SMART weighting, length normalisation, cosine; Jaccard on Dhvani keys for spelling-variant analysis |
| Scoring and result assembly | Heap-based top-K, **champion lists** (with measured speed vs. quality loss), **zone index** with learned zone weights, putting together a complete search system |
| Beyond syllabus (extra points) | **BM25**, **dense retrieval**, **RRF fusion**, **gated cascade (learned)**, **distillation** |

**Rule:** the core engine (index, tf-idf, BM25, Boolean, phrase, top-K, champion lists, Dhvani) is our own code. Libraries are used only for data loading, transliteration of *synthetic* queries, the neural encoder, ONNX, plotting and a **reference check** in tests (e.g. comparing our BM25 with `rank_bm25` on a toy corpus). Each library's role is explained in IR terms in the report, as the PDF requires.

---

## 5. Evaluation (15 marks)

Full protocol: `docs/EVALUATION.md`. Summary:

- **Test queries:** MIRACL-hi **dev** (350 queries, 3,494 judgments, 752 relevant). These are **never** used for tuning.
- **Tuning and training queries:** MIRACL-hi **train** (1,169 queries). Used for zone weights, BM25 k1/b, gate training and SCD.
- **Query forms:** F1 Devanagari (original), F2 standard romanisation, F3 casual romanisation (seeded noise), plus the **human set** for 60 dev queries: 3 independent romanisations (H-R1..3), code-mixed (H-CM) and English (H-EN).
- **Systems:** B0 naive BM25 → B1 BM25 + normalisation + stemming → B2 B1 + rule-based Roman→Devanagari transliteration (*the obvious baseline*) → S1 + Dhvani zone → S2 + pooled df → D0 dense → H1 RRF(S2, D0) → G1 gated cascade → (stretch) D1/H2 with the SCD student.
- **Metrics:** nDCG@10 (primary), P@5, P@10, Recall@100, MRR@10, plus **Script Gap**, **CSC@10 (RBO, p = 0.9)**, **worst-script nDCG@10**. Efficiency: p50/p95 latency, index MB, model MB, % of queries that used neural inference.
- **Statistics:** paired randomisation test (or bootstrap) over queries for the headline comparisons.
- **Note:** MIRACL-hi dev has about 2.1 relevant passages per query, so P@10 can never exceed about 0.2. That's why nDCG@10 is the primary metric. Explain this in the report so P@10 doesn't look "low".

---

## 6. Rubric → plan mapping (100 marks)

| Criterion (marks) | What earns full marks | Our plan |
|---|---|---|
| Use of IR principles (30) | Correct, explained, integrated | §4 + `docs/IR_CONCEPTS.md`; `--explain` shows postings, idf and per-zone scores live; every module's docstring names the lecture concept |
| Working system (20) | Runs live on real input; README reproduces it | Command-line tool on the real MIRACL corpus; `scripts/` reproduce index → eval from a fresh clone; tests; **no hard-coded outputs** |
| Evaluation (15) | Judged queries, P/R/P@k, vs. a baseline | 350 judged dev queries × 3 forms + 60 human × 5 forms; 4 baselines; significance; plots |
| Novelty (10) | New compared with the baseline and existing tools | N1–N6, honest prior-art statement (§2.3) |
| Track relevance (5) | Directly addresses T5 | Every T5 hook covered (§1 table) |
| Report (10) | Explains IR, why it matters, novelty, next steps | `docs/REPORT_OUTLINE.md` with a page budget |
| Video (10) | Clear demo + explanation | `docs/VIDEO_SCRIPT.md`, timed to 7 minutes and mapped to the PDF's 5 required items |

---

## 7. Scope tiers and cut lines

**MUST (minimum version that can be submitted; finished by Checkpoint B/C):**
normaliser, tokenizer, stemmer, stop-list · positional inverted index with zones · BM25 + tf-idf lnc.ltc · heap top-K · Boolean + phrase · Dhvani zone · synthetic romaniser (F2, F3) · eval harness with all metrics including Script Gap / CSC / worst-script · baselines B0–B2 · command-line tool with `--explain` · human query set (teammates).

**SHOULD:** pooled-df (N3) on a mixed-script corpus variant · champion lists + timing · dense e5-small int8 ONNX + RRF hybrid · gated cascade (N5) vs. random gate · significance tests · corpus idf / stop-word analysis plots.

**STRETCH:** SCD student + vocabulary pruning + int8 ONNX (N6) · neural transliteration baseline B3 (AI4Bharat IndicXlit) only if it installs in under 30 minutes · Streamlit page.

**Cut order when behind schedule:** Streamlit → B3 → SCD → cascade → dense. **Never cut** evaluation, the README or the `--explain` output.

---

## 8. 36-hour timeline (H0 = when you start building inside the official window)

Devansh builds; teammates run in parallel on separate tasks (see `docs/WORK_DIVISION.md`).

| Hours | Devansh (build) | Teammates (parallel) | Checkpoint |
|---|---|---|---|
| H0–1 | venv, `requirements.txt`, `scripts/download_data.py`, `scripts/build_subsample.py` | Read `docs/QUERY_ANNOTATION_GUIDE.md`; receive their 60-query sheet | Data on disk |
| H1–4 | `text/normalize.py`, `tokenize.py`, `stopwords.py`, `stemmer.py` + tests | Annotating (romanisations, independently) | |
| H4–7 | `index/` positional inverted index, zones, save/load; `retrieval/` BM25, tf-idf lnc.ltc, heap top-K, Boolean, phrase; command-line tool | Annotating | **A: Devanagari search works from the command line** |
| H7–9 | `text/romanize.py` (F2/F3), `eval/metrics.py` (P@k, R@k, nDCG, MRR, RBO, Script Gap, CSC, worst-script), run B0/B1/B2 | Annotation done by H9; teammate B sets up plotting notebook | **B: first real numbers in `results/`. This is a valid submission.** |
| H9–12 | `text/dhvani.py` + Dhvani zone (S1), pooled df on mixed corpus (S2), stemming ablation, corpus idf analysis | Teammate A checks annotations; computes annotator edit distance | **C: novelty core works.** Commit + push. |
| H12–13 | Update README "what works" honestly; push | | |
| H13–19 | **SLEEP.** Before sleeping, start dense passage encoding (`scripts/encode_corpus.py`) in the background (laptop or Colab/Kaggle) | Teammate B drafts report §1 and §5 template | |
| H19–22 | Dense D0 (int8 ONNX), RRF hybrid H1, run on human set | | |
| H22–25 | Gate features + logistic gate trained on **train** queries, threshold sweep, random-gate baseline, latency measurement | Teammate B: plots from `results/*.csv` | **D: FEATURE FREEZE for MUST + SHOULD** |
| H25–29 | STRETCH: SCD fine-tune (≈2–3 h, runs even on CPU) + vocab prune + int8 ONNX. **Only if D was reached by H25.** | Report drafting | |
| H29–31 | Final evaluation of every system, significance tests, final plots, `--explain` polish | | All numbers final |
| H31–34 | Report: fill `docs/REPORT_OUTLINE.md` → PDF (≤ 8 pages), pipeline diagram, AI-use, work division | Teammates write their sections; rehearse their video parts | Report PDF |
| H34–35.5 | Record the video following `docs/VIDEO_SCRIPT.md`; upload as **unlisted** | Record their segments | Video link |
| H35.5–36 | **Fresh-clone reproduction test** of the README on a clean folder; submit the form | | **Submitted** |

---

## 9. Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Laptop too slow to encode 100k passages | Medium | Use Colab/Kaggle GPU for `encode_corpus.py`, or drop the corpus to 50k (config flag) and state it |
| Dhvani over-merges words (collisions hurt precision) | Medium | Separate zone with a **tuned lower weight**; measure collision rate (surface types per key); show it as a limitation |
| Synthetic romanisation is unrealistic | High | The human set (N4) is the realistic test; synthetic forms are a controlled stress test with a noise level |
| Test leakage (tuning on dev) | Medium | Hard rule in `CLAUDE.md`: tune and train on **train** only |
| P@10 looks low | Certain | Explain the ceiling (about 2.1 relevant per query); nDCG@10 is primary |
| `regex \w` breaks Devanagari words at vowel signs | High if ignored | Tokenizer uses explicit Unicode ranges / `regex` `\p{M}`; unit test with "हिन्दी" |
| Neural transliteration library (IndicXlit) install hell | High | It's STRETCH; skip after 30 minutes and say so |
| Running out of time | Medium | Tiers + cut order (§7); Checkpoint B already gives a valid submission |
| Video over 8 minutes | Medium | Script is timed at about 7 minutes; rehearse once |

---

## 10. Deliverables checklist (from the PDF)

- [ ] **Repo** with a README covering setup, how to run, data source, what works vs. what's planned → `README.md`
- [ ] **Video**, 5–8 min, unlisted, live run, **no slides**, each member explains their component, one limitation shown → `docs/VIDEO_SCRIPT.md`
- [ ] **Report PDF**, ≤ 8 pages (excluding references and appendix), 7 sections + pipeline diagram + work division + AI-use declaration → `docs/REPORT_OUTLINE.md`
- [ ] One submission form per team, before the deadline

## 11. Rules compliance

- [ ] Built inside the 36-hour window (commit history shows it; commit often)
- [ ] No code copied from VidhiVault or any online repo; ideas cited, code written fresh
- [ ] No crawling planned → robots.txt not applicable; if a crawl is added later, obey robots.txt and add delays
- [ ] No personal data; every dataset and model credited (`docs/DATA.md`)
- [ ] AI-use declared everywhere it was used (`docs/AI_USE.md`)
- [ ] Nothing faked, hard-coded or screenshot-only; every number comes from `results/`
