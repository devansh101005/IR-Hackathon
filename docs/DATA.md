# Data, Models and Credits

The PDF requires every dataset to be credited, robots.txt to be obeyed and no personal data to be collected. **Check each licence on its official page before submitting.**

## Datasets
| Name | What we use | Size (checked) | Licence | Source |
|---|---|---|---|---|
| MIRACL v1.0, Hindi topics + qrels | dev (test) and train (tuning) queries with relevance judgments | dev: 350 queries, 3,494 judgments (752 relevant) · train: 1,169 queries, 11,668 judgments | Apache-2.0 (dataset card) | `huggingface.co/datasets/miracl/miracl` → `miracl-v1.0-hi/` |
| MIRACL corpus v1.0, Hindi | Wikipedia passages (`docid`, `title`, `text`) | 2 gzipped JSONL shards, about 96 MB each | Apache-2.0; passage text from Wikipedia (CC BY-SA 3.0) | `huggingface.co/datasets/miracl/miracl-corpus` → `miracl-corpus-v1.0-hi/docs-{0,1}.jsonl.gz` |
| LipiSetu human query set (ours) | Romanised / code-mixed / English rewrites of 60 dev queries | 60 × 5 forms | Ours; released with the repo | `queries/human/` |
| LipiSetu synthetic variants (ours) | F2/F3 romanisations of dev + train queries; mixed-script corpus variant for E5 | Generated | Ours | `scripts/make_variants.py` |

Download URLs (used by `scripts/download_data.py`):
```
https://huggingface.co/datasets/miracl/miracl/resolve/main/miracl-v1.0-hi/topics/topics.miracl-v1.0-hi-{dev,train}.tsv
https://huggingface.co/datasets/miracl/miracl/resolve/main/miracl-v1.0-hi/qrels/qrels.miracl-v1.0-hi-{dev,train}.tsv
https://huggingface.co/datasets/miracl/miracl-corpus/resolve/main/miracl-corpus-v1.0-hi/docs-{0,1}.jsonl.gz
```
These files were checked on 2026-10-06: not gated, no token needed.

## Corpus subsample (what is a document)
- One document = one MIRACL passage (`docid` = `articleid#passageno`), with zones `title` and `body`.
- Kept: **every passage judged** for any dev or train query, plus a uniform random sample from the remaining passages (default 100k, `seed = 13`).
- The same subsample is used for every system, so comparisons are fair. Absolute numbers are **not** comparable to the MIRACL leaderboard (full corpus); stated as a limitation.

## Models
| Model | Use | Licence | Source |
|---|---|---|---|
| `intfloat/multilingual-e5-small` | Dense encoder (D0), teacher/student for SCD | MIT | Hugging Face |
| `intfloat/multilingual-e5-base` (optional) | Optional stronger teacher | Check the model card | Hugging Face |
| AI4Bharat IndicXlit (optional, B3) | Neural transliteration baseline | Check the repo | AI4Bharat |

## Libraries (role explained in `docs/IR_CONCEPTS.md`)
`indic-transliteration`, `numpy`, `pandas`, `matplotlib`, `scikit-learn` (gate only), `onnxruntime`, `transformers`, `optimum`/`torch` (export and SCD), `regex`, `pytest`, `rank_bm25` (tests only), `streamlit` (optional UI). Pin versions in `requirements.txt`.

## Ethics
- **No crawling** in the current plan, so robots.txt does not apply. If a crawl is added: obey robots.txt, add a delay of at least 1 s per host, and identify the user agent.
- **No personal data.** The human query set contains only rewrites of public MIRACL questions; annotators are not identified beyond their team role.
- Wikipedia text is CC BY-SA. We don't redistribute the corpus; `scripts/download_data.py` fetches it from the source.
