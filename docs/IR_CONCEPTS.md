# IR Concepts → Code Map

This is my evidence for **"Use of IR principles" (30 marks)**. It feeds report §2 and the pipeline part of the video.
Paths are relative to `src/lipisetu/` unless they start with `scripts/` or `app/`. Status: ✅ done · 🟡 waiting on the human annotations.

## Lecture: Boolean retrieval
| Concept | Status | File | Why I use it | How I show it |
|---|---|---|---|---|
| Inverted index (dictionary + postings) | ✅ | `index/inverted_index.py` | The core structure: a dictionary (term → id) plus one packed postings file (numpy arrays), like on disk | `--explain` prints real postings with tf and positions |
| AND / OR / NOT queries | ✅ | `retrieval/boolean.py` | Filters like `भारत AND NOT क्रिकेट` | `python -m lipisetu.cli boolean "..."` |
| Postings intersection (linear merge) | ✅ | `retrieval/boolean.py` → `intersect()` | Linear-time AND on sorted postings | Code walkthrough; unit test |
| Query optimisation: process by increasing df | ✅ | `retrieval/boolean.py` → `boolean_search()` | Smaller intermediate lists | The CLI prints the processing order and the number of comparisons |

## Lecture: Term vocabulary and postings
| Concept | Status | File | Why | How I show it |
|---|---|---|---|---|
| What a document is | ✅ | `scripts/build_subsample.py` | One MIRACL passage = one document (labels are per passage); zones title and body | Report §2 |
| Tokenisation for a non-English script | ✅ | `text/tokenize.py` | Python `\w` splits हिन्दी into ह, न, द, so I use explicit Unicode ranges | Unit test `"हिन्दी"` → 1 token |
| Normalisation + case folding | ✅ | `text/normalize.py` | NFC, nukta folding, chandrabindu → anusvara, ZWJ removal, half-nasal → anusvara (हिन्दी = हिंदी), digits | Unit tests |
| Stop words on Hindi | ✅ | `text/stopwords.py`, `scripts/corpus_stats.py` | 35 of the 40 highest-df terms are in my stop list | `results/e3_top_df_terms.csv` |
| Stemming vs no stemming | ✅ | `text/stemmer.py` | लड़का / लड़के / लड़कों → one stem; B1 vs B1N | Table 1 in the report |
| Soundex (lecture version) | ✅ | `text/soundex.py` | Baseline phonetic key (system S0) | S0 vs S1 |
| **Dhvani key** (cross-script phonetic key) | ✅ | `text/dhvani.py` | मौसम / mausam / mosam → `MSM` | Rule ablation `results/e5_dhvani_ablation.csv` |
| Skip pointers | ✅ | `retrieval/boolean.py` → `intersect_with_skips()` | √L skips; fewer comparisons on uneven lists | `results/e11_efficiency.csv`, unit test |
| Positional index + phrase queries | ✅ | `index/inverted_index.py`, `retrieval/boolean.py` → `phrase_search()` | Stop words keep their positions, so "भारत का संविधान" means a gap of 2 | `python -m lipisetu.cli phrase "..."` |
| Precision and recall | ✅ | `eval/metrics.py` | Evaluation | Results tables |

## Lecture: tf-idf and the vector space model
| Concept | Status | File | Why | How I show it |
|---|---|---|---|---|
| log tf, idf, tf-idf | ✅ | `retrieval/tfidf.py` | VSM baseline V1 | `--explain --system V1` prints the ltc weights |
| SMART **lnc.ltc** + length normalisation + cosine | ✅ | `retrieval/tfidf.py`, `index/inverted_index.py` → `compute_lnc_norms()` | Standard VSM from the lectures | Unit test: cosine ≤ 1 |
| Jaccard coefficient | ✅ | `scripts/annotator_agreement.py` | Character-bigram Jaccard between annotators' spellings | 🟡 needs the human sheets |
| Documents and queries as vectors across languages | ✅ | `dense/encoder.py`, `dense/retriever.py` | A shared multilingual vector space | D0 / D1 rows |

## Lecture: Scoring and result assembly
| Concept | Status | File | Why | How I show it |
|---|---|---|---|---|
| Efficient (term-at-a-time) scoring with accumulators | ✅ | `retrieval/bm25.py` → `bm25_zone()` | One score slot per document, add each term's contribution | Code walkthrough |
| Heap-based top-K | ✅ | `retrieval/topk.py` → `top_k()` | O(n log K) over scored documents only | `results/e11_efficiency.csv` |
| Champion lists | ✅ | `retrieval/topk.py` → `ChampionLists` | r = 200 best-tf docs per term, precomputed | Speed vs nDCG in E11 |
| Zone index + zone weights tuned on train | ✅ | `index/build.py`, `search.py` | title / all / Dhvani zones; weights from `scripts/tune_sparse.py` | `results/tuned_params.json` |
| Static quality g(d) and net score | ✅ | `rerank/ltr.py` (`lead_passage` feature) | First passage of an article as a prior | `results/ltr_weights.csv` |
| Query-term proximity | ✅ | `retrieval/proximity.py` | Smallest window over Dhvani positions (works for every script) | `--explain` shows the window |
| Cluster pruning (leaders / followers) | ✅ | `dense/cluster_pruning.py` | √N leaders, score only 8 clusters | E11 overlap and speed |
| Query parser (script detection) | ✅ | `text/script.py`, `query.py` | Mixed-script queries handled token by token | `--explain` |
| A complete search system | ✅ | `search.py`, `cli.py`, `app/server.py` | End-to-end demo | Video |

## Beyond the syllabus (extra points)
| Method | Status | File | Role |
|---|---|---|---|
| BM25 | ✅ | `retrieval/bm25.py` | Main sparse scorer; k1 and b tuned on train |
| Pooled df (Pirkola-style) | ✅ | `retrieval/bm25.py` → `pooled_df_table()` | Fixes inflated idf when a word's df is split across scripts (E6) |
| Dense retrieval (multilingual-e5-small, int8 ONNX) | ✅ | `dense/encoder.py`, `dense/export_onnx.py` | Cross-lingual matching |
| Script-consistency distillation + vocabulary pruning | ✅ | `dense/scd.py`, `dense/prune_vocab.py`, `scripts/train_scd.py` | 448 MB → 37 MB script-aware query encoder |
| Reciprocal Rank Fusion | ✅ | `retrieval/rrf.py` | Combines sparse and dense rankings (H1) |
| Learning to rank | ✅ | `rerank/ltr.py`, `scripts/train_ltr_gate.py` | Logistic regression over IR features (L1) |
| Confidence-gated cascade | ✅ | `cascade/gate.py` | Neural inference only when IR signals say it helps (G1) |

## Libraries and their role in IR terms (the PDF asks for this)
| Library | Role in my pipeline | Not used for |
|---|---|---|
| `indic-transliteration` | Only in baseline B2 (Roman → Devanagari with ITRANS), to represent the "obvious" approach | My own romaniser, indexing or scoring |
| `onnxruntime`, `transformers`, `torch` | Run, export, quantise and fine-tune the neural encoder | Sparse retrieval |
| `numpy` | Packed postings arrays, score accumulators, vector maths | — |
| `scikit-learn` | Logistic regression for learning to rank and the gate | tf-idf (my own code) |
| `rank_bm25` | **Tests only**: reference check for my BM25 ranking | The main pipeline |
| `matplotlib`, `pandas` | Report figures | — |
| `fastapi`, `uvicorn` | Serve the demo page | Any IR logic |
