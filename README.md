# LipiSetu: Script-Invariant Hindi Search

**CSD358 IR Hackathon · Track T5: Multilingual and Indic-language search**

Someone who types *"kal ka mausam"* should get the same results as someone who types *"कल का मौसम"*. LipiSetu measures the **Script Gap** that Roman-script Hindi users face in search, and closes it with classic IR: a from-scratch BM25/VSM engine, a cross-script phonetic index zone (**Dhvani key**) and pooled document frequency. It runs a small neural encoder **only when IR signals predict that sparse retrieval failed**.

> Status legend: ✅ works · 🟡 partial · ⏳ planned. **This table is updated honestly as work progresses.**

## What works and what is planned

| Component | Status | Where |
|---|---|---|
| Data download + corpus subsample (MIRACL-hi) | ⏳ | `scripts/download_data.py`, `scripts/build_subsample.py` |
| Devanagari/Roman normalisation, tokenizer, stop words, Hindi stemmer | ⏳ | `src/lipisetu/text/` |
| Positional inverted index with zones (title, body, Dhvani) | ⏳ | `src/lipisetu/index/` |
| BM25, tf-idf (lnc.ltc) cosine, Boolean + phrase queries, heap top-K | ⏳ | `src/lipisetu/retrieval/` |
| Dhvani key (cross-script phonetic key) | ⏳ | `src/lipisetu/text/dhvani.py` |
| Pooled-df idf across script variants | ⏳ | `src/lipisetu/retrieval/bm25.py` |
| Synthetic query variants (standard and casual romanisation) | ⏳ | `src/lipisetu/text/romanize.py` |
| Human Hinglish query set (3 annotators) | ⏳ | `queries/human/` |
| Evaluation: nDCG, P@k, Recall, MRR, Script Gap, cross-script consistency (RBO), worst-script nDCG | ⏳ | `src/lipisetu/eval/` |
| Dense retrieval (multilingual-e5-small, int8 ONNX) + RRF hybrid | ⏳ | `src/lipisetu/dense/`, `src/lipisetu/fusion/` |
| Confidence-gated cascade | ⏳ | `src/lipisetu/cascade/` |
| Script-consistency distillation + vocabulary pruning (stretch) | ⏳ | `src/lipisetu/dense/scd_train.py` |
| Command-line tool with `--explain` | ⏳ | `src/lipisetu/cli.py` |

## Setup

Requires Python 3.11 and about 2 GB of free disk space for data and indexes.

```bash
git clone https://github.com/devansh101005/IR-Hackathon.git
cd IR-Hackathon
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python scripts/download_data.py                      # MIRACL-hi topics, qrels, corpus → data/
python scripts/build_subsample.py --size 100000 --seed 13
python scripts/make_variants.py                      # synthetic query forms → queries/
python scripts/build_index.py                        # → indexes/
python -m lipisetu.cli search "kal ka mausam" --explain
```

`--explain` prints the intermediate values: tokens, normalised forms, stems, Dhvani keys, df/idf, postings, per-zone scores, the gate decision and the final ranking.

## Reproduce the evaluation

```bash
python scripts/run_all_eval.py     # writes results/*.csv
python scripts/make_plots.py       # writes results/*.png
pytest -q
```

## Data

- **MIRACL (Hindi)**: Wikipedia passages with human relevance judgments. Apache-2.0; passage text from Wikipedia (CC BY-SA). We use the dev split (350 queries) for testing and the train split (1,169 queries) for tuning only. The corpus is subsampled to about 100k passages plus every judged passage (seed 13).
- **Human query set**: romanised, code-mixed and English versions of 60 dev queries, written by the team.
- Full credits and licences: [`docs/DATA.md`](docs/DATA.md).

No web crawling is done and no personal data is collected.

## Results

_To be filled in from `results/` once the evaluation runs. No number will appear here unless a script produced it._

## Project documents

- [`PLAN.md`](PLAN.md): plan, novelty, rubric mapping, timeline
- [`docs/IR_CONCEPTS.md`](docs/IR_CONCEPTS.md): which IR principle lives where in the code, and why
- [`docs/EVALUATION.md`](docs/EVALUATION.md): evaluation protocol and metric definitions
- [`docs/DATA.md`](docs/DATA.md): datasets, models, licences, credits
- [`docs/WORK_DIVISION.md`](docs/WORK_DIVISION.md) · [`docs/AI_USE.md`](docs/AI_USE.md)
- [`docs/REPORT_OUTLINE.md`](docs/REPORT_OUTLINE.md) · [`docs/VIDEO_SCRIPT.md`](docs/VIDEO_SCRIPT.md)
- [`docs/QUERY_ANNOTATION_GUIDE.md`](docs/QUERY_ANNOTATION_GUIDE.md): instructions for the human query set

## Team

| Member | Owns |
|---|---|
| Devansh Pandey | System architecture, IR engine, Dhvani key, dense retrieval, gated cascade, evaluation harness |
| _Teammate A_ | Human query set, annotator-agreement analysis |
| _Teammate B_ | Evaluation runs, plots, report evaluation section |

## AI use

AI coding assistants (Claude Code) were used. Every use is declared in [`docs/AI_USE.md`](docs/AI_USE.md).
