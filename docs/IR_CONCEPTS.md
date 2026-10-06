# IR Concepts → Code Map

This file is the evidence for the **"Use of IR principles" (30 marks)** criterion. It feeds report §2 and video part 3.
**Update the Status and File columns as each item is built.** Status: ⏳ planned · 🟡 partial · ✅ done.

## Lecture: Boolean retrieval
| Concept | Status | File | Why we use it | Shown in video / report as |
|---|---|---|---|---|
| Inverted index (dictionary + postings) | ⏳ | `index/inverted_index.py` | Core data structure; every scorer reads from it | `--explain` prints the postings for a query term |
| AND / OR / NOT query processing | ⏳ | `retrieval/boolean.py` | Filters such as `मौसम AND NOT क्रिकेट`; used to check that Dhvani matches are correct | A live Boolean query in the demo |
| Postings intersection (merge) | ⏳ | `retrieval/boolean.py` | Linear-time AND | Code excerpt in the report |
| Query optimisation: process terms by increasing df | ⏳ | `retrieval/boolean.py` | Smaller intermediate lists → faster | The order is printed in `--explain` |

## Lecture: Term vocabulary and postings
| Concept | Status | File | Why | Evidence |
|---|---|---|---|---|
| Deciding what a document is | ⏳ | `scripts/build_subsample.py` | One MIRACL passage = one document (labels are per passage); zones = title, body | Report §2 explains the choice |
| Tokenisation for a non-English script | ⏳ | `text/tokenize.py` | `\w` breaks Devanagari at vowel signs, so we use a script-aware tokenizer | Unit test `"हिन्दी"` → 1 token |
| Normalisation (nukta, chandrabindu, ZWJ, digits) + case folding for Roman | ⏳ | `text/normalize.py` | The same word can be encoded with different Unicode sequences | Before/after table in the report |
| Stop words (Hindi) | ⏳ | `text/stopwords.py` | Compare a stop-list derived from corpus df with a standard list; study idf on Hindi | Plot of the highest-df terms + idf histogram |
| Stemming (light Hindi suffix stripper) vs. no stemming | ⏳ | `text/stemmer.py` | Hindi inflections (लड़का/लड़के/लड़कों); a T5 IR hook | Ablation table B1 with stemming on/off |
| **Soundex-style phonetic matching → Dhvani key** | ⏳ | `text/dhvani.py` | Cross-script spelling variants (mausam/mosam/मौसम → same key) | `--explain` shows the keys; collision-rate analysis |
| Positional index + phrase queries | ⏳ | `index/inverted_index.py`, `retrieval/boolean.py` | Exact phrases such as `"भारत का संविधान"` | Phrase query live in the demo |
| Precision and recall | ⏳ | `eval/metrics.py` | Evaluation | Results tables |

## Lecture: tf-idf and the vector space model
| Concept | Status | File | Why | Evidence |
|---|---|---|---|---|
| Log-frequency tf, idf, tf-idf | ⏳ | `retrieval/tfidf.py` | VSM baseline and comparison with BM25 | `--explain` prints the weights |
| SMART **lnc.ltc** + length normalisation + cosine | ⏳ | `retrieval/tfidf.py` | Standard VSM from the lectures | Formula + code excerpt in the report |
| Jaccard coefficient | ⏳ | `eval/annotator_agreement.py`, `text/dhvani.py` analysis | Character-bigram Jaccard between annotators' romanisations; variant analysis | Agreement table |
| Documents and queries as vectors (cross-lingual) | ⏳ | `dense/encoder.py` | Multilingual embedding space for English/code-mixed queries | Dense results table |

## Lecture: Scoring and result assembly
| Concept | Status | File | Why | Evidence |
|---|---|---|---|---|
| Heap-based top-K | ⏳ | `retrieval/topk.py` | O(N log K) instead of a full sort | Timing comparison |
| Champion lists | ⏳ | `retrieval/topk.py` | Faster scoring; we measure the quality loss | Speed vs. nDCG table |
| Zone index (title, body, Dhvani) + zone weights tuned on train | ⏳ | `index/inverted_index.py`, `retrieval/bm25.py` | The Dhvani zone must count less than an exact surface match | Learned weights shown in the report |
| Query parser (script detection → per-script processing) | ⏳ | `text/script.py`, `cli.py` | Mixed-script queries are processed token by token | `--explain` |
| Putting together a complete search system | ⏳ | `cli.py` | End-to-end demo | Video part 2 |

## Beyond the syllabus (extra points)
| Method | Status | File | Role |
|---|---|---|---|
| BM25 | ⏳ | `retrieval/bm25.py` | Main sparse scorer; k1, b tuned on train |
| Pooled df (Pirkola-style structured query over spelling variants) | ⏳ | `retrieval/bm25.py` | Fixes idf inflation when a term's df is split across scripts |
| Dense retrieval (multilingual-e5-small, int8 ONNX) | ⏳ | `dense/encoder.py` | Cross-lingual and code-mixed matching |
| Reciprocal Rank Fusion | ⏳ | `fusion/rrf.py` | Combines the sparse and dense rankings |
| Confidence-gated cascade (learned gate, query-performance-prediction features) | ⏳ | `cascade/gate.py` | Neural inference only when needed |
| Script-consistency distillation + vocabulary pruning (stretch) | ⏳ | `dense/scd_train.py`, `dense/prune_vocab.py` | Small script-invariant query encoder |

## Libraries and their role in IR terms (the PDF requires this explanation)
| Library | Role in our pipeline | Not used for |
|---|---|---|
| `indic-transliteration` | Creates **synthetic** romanised query variants (F2) from Devanagari queries; used in baseline B2 | Indexing or scoring |
| `onnxruntime`, `transformers`, `optimum` / `torch` | Run and export the neural encoder | Sparse retrieval |
| `numpy` | Vector maths for the cosine computation | — |
| `scikit-learn` | Logistic regression for the gate only | tf-idf (we write our own) |
| `rank_bm25` | **Tests only**: a reference check that our BM25 matches | The main pipeline |
| `matplotlib`, `pandas` | Plots and result tables | — |
