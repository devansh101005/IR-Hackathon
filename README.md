# LipiSetu: Script-Invariant Hindi Search

CSD358 Information Retrieval, Mid-term Hackathon 2026 · Track T5: Multilingual and Indic-language search

**Demo video (7:52):** https://drive.google.com/file/d/1TqHq50ZBkyzUqQHaT9QEZ2kipsKy6S4D/view?usp=sharing
**Report:** [`docs/report/LipiSetu_report.pdf`](docs/report/LipiSetu_report.pdf)

Most of us type Hindi in Roman letters (*kal ka mausam*), but most Hindi text online is in Devanagari (*कल का मौसम*). A normal search engine only matches exact words, so the Roman query finds almost nothing. On 350 judged MIRACL-Hindi queries, BM25 gets nDCG@10 0.533 when the question is typed in Devanagari and 0.004 when the same question is typed in Roman letters. The usual fix, transliterating the query first, only gets to 0.113. We call this loss the **Script Gap**.

LipiSetu ("lipi" = script, "setu" = bridge) closes most of this gap using classic IR that we wrote ourselves:

- **Dhvani key**: a sound-based key for every word that is the same in both scripts (मौसम, mausam and mosam all become `MSM`). It is stored as its own zone in the inverted index.
- **Pooled document frequency**: all spellings of a word share one df, so rare spellings don't get an inflated idf. We also use a title zone and query-term proximity.
- **A small neural encoder** (distilled from 448 MB down to 37 MB) that only runs when a gate, trained on IR signals, predicts it will help.

![pipeline](docs/pipeline.png)

## Results

350 test queries (MIRACL-Hindi dev split), each asked in Devanagari, standard Roman and casual Roman. All tuning was done on the separate train split. Latency was measured on a laptop CPU (Intel i5-12450H, no GPU).

| System | nDCG@10 Devanagari | nDCG@10 Roman | nDCG@10 casual Roman | Script Gap (casual) | Consistency CSC@10 | Median ms |
|---|---|---|---|---|---|---|
| B1 BM25 + stemming | 0.533 | 0.004 | 0.003 | 0.530 | 0.179 | 0.7 |
| B2 transliterate + BM25 (obvious baseline) | 0.531 | 0.113 | 0.095 | 0.436 | 0.244 | 2.8 |
| S0 + classic Soundex zone | 0.518 | 0.344 | 0.320 | 0.198 | 0.534 | 11.3 |
| **S2 + Dhvani zone + pooled df** | 0.533 | 0.487 | 0.490 | **0.043** | **0.794** | 7.0 |
| D0 dense e5-small (int8) | 0.601 | 0.001 | 0.000 | 0.600 | 0.169 | 12.5 |
| D1 our distilled query encoder (37 MB) | 0.598 | 0.167 | 0.151 | 0.447 | 0.299 | 12.5 |
| **L1 learning to rank** | **0.642** | **0.501** | **0.498** | 0.143 | 0.637 | 35.5 |
| **G1 gated cascade** | 0.633 | 0.492 | 0.490 | 0.143 | 0.625 | 18.6 |

A few things stand out:
- With the Dhvani zone and pooled df, Roman queries go from 0.004 to 0.487, and the Script Gap drops from 0.436 (transliteration) to 0.043.
- The plain neural model (D0) is good on Devanagari but scores almost 0 on Roman queries. It matches the script before the meaning. Our distillation fixes part of this; the Dhvani zone fixes more.
- The gate runs the neural stage for only 36% of queries and still scores 0.538 overall, which is better than never running it (0.507) and better than always running it (0.496).
- The gains on Roman queries are statistically significant (paired randomisation test, p < 0.001).

## Human query set

Generated Roman queries can be too clean, so the three of us also typed the same 60 test questions in Roman letters on our own, without any transliteration tool. Each of us also wrote code-mixed and English versions of 20 questions.

| System | Devanagari | Our 3 romanisations | Code-mixed | English |
|---|---|---|---|---|
| B1 BM25 + stemming | 0.571 | 0.013–0.020 | 0.033 | 0.015 |
| B2 transliterate + BM25 | 0.571 | 0.112–0.140 | 0.054 | 0.039 |
| **S3 LipiSetu (sparse)** | 0.616 | 0.435–0.448 | 0.204 | 0.119 |
| D1 distilled dense encoder | 0.595 | 0.179–0.208 | 0.316 | 0.413 |
| **L1 learning to rank** | 0.706 | 0.491–0.507 | 0.383 | 0.369 |
| G1 gated cascade | 0.691 | 0.434–0.454 | 0.260 | 0.258 |

- We spelled the same word the same way only 78% of the time, but our Dhvani keys matched 91% of the time.
- On our real typing, S3 beats transliteration for each of the three annotators (p ≤ 0.0002), so the results on generated queries hold.
- **Limitation:** code-mixed and English questions need meaning, not sound (*leader* doesn't sound like नेता). The sparse engine is weak on them, the dense encoder helps, and the gate (which never saw such questions in training) calls the dense stage too rarely.

All result files are in `results/`, and the full discussion is in the report.

## What works and what is planned

| Component | Status | Where |
|---|---|---|
| Data download and corpus subsample (MIRACL-hi, 110,855 passages) | Done | `scripts/download_data.py`, `scripts/build_subsample.py` |
| Normalisation, script-aware tokenizer, stop words, Hindi stemmer | Done | `src/lipisetu/text/` |
| Classic Soundex and the Dhvani key | Done | `text/soundex.py`, `text/dhvani.py` |
| Positional inverted index with zones, champion lists | Done | `src/lipisetu/index/` |
| Boolean search (df-ordered, skip pointers), phrase queries, tf-idf, BM25, proximity, heap top-K | Done | `src/lipisetu/retrieval/` |
| Pooled df across spellings | Done | `retrieval/bm25.py` |
| Generated query variants (standard and casual romanisation) | Done | `text/romanize.py`, `queries/` |
| Evaluation: nDCG, P@k, Recall, MRR, Script Gap, CSC (RBO), worst-script nDCG, significance tests | Done | `src/lipisetu/eval/`, `scripts/` |
| Dense retrieval (int8 ONNX), cluster pruning, RRF | Done | `src/lipisetu/dense/` |
| Distilled query encoder with vocabulary pruning (448 MB → 37 MB) | Done | `dense/scd.py`, `scripts/train_scd.py` |
| Learning to rank, gated cascade | Done | `rerank/ltr.py`, `cascade/gate.py` |
| Command-line tool with `--explain`, web demo | Done | `src/lipisetu/cli.py`, `app/` |
| Human query set (3 annotators, 60 queries) and annotator agreement | Done | `queries/human/`, `scripts/annotator_agreement.py` |
| Neural transliteration baseline (IndicXlit), more Indian languages, in-browser demo | Planned | roadmap in the report |

## Setup

You need Python 3.10–3.13 and about 3 GB of free disk. No GPU is needed.

```bash
git clone https://github.com/devansh101005/IR-Hackathon.git
cd IR-Hackathon
python -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu    # small CPU-only torch
pip install -r requirements.txt
export PYTHONPATH=src                      # Windows PowerShell: $env:PYTHONPATH="src"
```

**On Windows:** also run `$env:PYTHONUTF8="1"` so Hindi text prints properly. If Windows 11 *Smart App Control* blocks a scikit-learn file ("An Application Control policy has blocked this file"), install an older version that Windows already trusts: `pip install "scikit-learn==1.7.2"`. We tested this.

## Run

**Quick path: the sparse engine only (about 5 minutes)**
```bash
python scripts/download_data.py                        # MIRACL-hi topics, judgments and passages -> data/raw/
python scripts/build_subsample.py --size 100000 --seed 13
python scripts/make_variants.py                        # Roman query forms, mixed-script corpus
python scripts/build_index.py                          # builds indexes/main/ (about 2 min)
python -m lipisetu.cli search "kal ka mausam kaisa rahega" --explain
python -m lipisetu.cli compare "bharat ka samvidhan kab lagu hua" --systems B1,B2,S3
python -m lipisetu.cli boolean "भारत AND संविधान AND NOT नेपाल"
python -m lipisetu.cli phrase "भारत का संविधान"
```
The tuned parameters (`results/tuned_params.json`, tuned on the train split) are already in the repo, so you don't need to re-tune.

**Full path: neural parts and web demo (about 1.5–2 hours on a laptop CPU)**
```bash
python scripts/build_index.py --mixed                  # index for the mixed-script experiment
python scripts/tune_sparse.py                          # optional: re-tune on train (~8 min)
python scripts/export_dense.py                         # e5-small -> ONNX fp32 + int8
python scripts/encode_corpus.py                        # passage vectors (~45-50 min, can resume)
python scripts/train_scd.py                            # distillation + pruning (~15-25 min)
python scripts/train_ltr_gate.py                       # learning to rank + gate (~5 min)
python app/server.py                                   # web demo at http://127.0.0.1:8000
```

## Reproduce every number

```bash
python scripts/run_all_eval.py           # main tables + human query set
python scripts/annotator_agreement.py    # how differently the three annotators spelled words
python scripts/gate_budget_curve.py      # gate vs random gate at the same budget
python scripts/efficiency_experiments.py # skip pointers, champion lists, cluster pruning, heap top-K
python scripts/pooled_df_experiment.py   # pooled df on the mixed-script corpus
python scripts/ablation_dhvani.py        # switching off one Dhvani rule at a time
python scripts/corpus_stats.py           # Zipf, top df terms, idf histogram
python scripts/length_bias.py            # why tf-idf prefers short passages
python scripts/significance.py           # paired randomisation tests
python scripts/make_plots.py
python scripts/make_report.py            # docs/report/report.html (print it to PDF from Chrome)
pytest -q                                # 31 tests
```

## Data

- **MIRACL (Hindi):** Wikipedia passages with human relevance judgments. Apache-2.0, text from Wikipedia (CC BY-SA). The dev split (350 queries) is used only for testing; tuning and training use the train split (1,169 queries).
- **Model:** `intfloat/multilingual-e5-small` (MIT).
- **Human query set:** romanised, code-mixed and English versions of 60 dev queries, typed by the three of us (`queries/human/`).
- Full credits and licences are in [`docs/DATA.md`](docs/DATA.md). We did no web crawling and used no personal data.

## Project documents

- [`PLAN.md`](PLAN.md): plan, novelty and how it maps to the rubric
- [`docs/IR_CONCEPTS.md`](docs/IR_CONCEPTS.md): where each IR concept lives in the code
- [`docs/EVALUATION.md`](docs/EVALUATION.md): evaluation protocol and metrics
- [`docs/VIDEO_SCRIPT.md`](docs/VIDEO_SCRIPT.md), [`docs/REPORT_OUTLINE.md`](docs/REPORT_OUTLINE.md)
- [`docs/WORK_DIVISION.md`](docs/WORK_DIVISION.md), [`docs/AI_USE.md`](docs/AI_USE.md), [`docs/QUERY_ANNOTATION_GUIDE.md`](docs/QUERY_ANNOTATION_GUIDE.md)

## Team

| Member | Roll no. | Worked on |
|---|---|---|
| Devansh Pandey | 2310110461 | Idea and design; IR engine; Dhvani key and pooled df; dense retrieval, distillation and pruning; learning to rank; gated cascade; evaluation; demo; report; one of the annotators |
| Anamika Pal | 2310110037 | Human query annotation; annotator-agreement analysis |
| Abhinav Bachchas | 2310110383 | Human query annotation; reviewed the final results and plots; proofread the report |

## AI use

We used Claude Code while building this project. The details are in [`docs/AI_USE.md`](docs/AI_USE.md) and in the report.
