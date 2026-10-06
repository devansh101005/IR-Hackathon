# Data, Models and Credits

The PDF says to credit every dataset, obey robots.txt and not collect personal data. I check each licence on its official page before submitting.

## Datasets
| Name | What I use | Size (checked) | Licence | Source |
|---|---|---|---|---|
| MIRACL v1.0, Hindi topics + qrels | dev (test) and train (tuning) queries with relevance labels | dev: 350 queries, 3,494 judgments (752 relevant) · train: 1,169 queries, 11,668 judgments | Apache-2.0 | `huggingface.co/datasets/miracl/miracl` → `miracl-v1.0-hi/` |
| MIRACL corpus v1.0, Hindi | Wikipedia passages (`docid`, `title`, `text`) | 2 gzipped JSONL shards, about 96 MB each | Apache-2.0; text from Wikipedia (CC BY-SA 3.0) | `huggingface.co/datasets/miracl/miracl-corpus` → `miracl-corpus-v1.0-hi/docs-{0,1}.jsonl.gz` |
| LipiSetu human query set (mine) | Romanised / code-mixed / English rewrites of 60 dev queries | 60 × 5 forms | Released with this repo | `queries/human/` |
| LipiSetu synthetic variants (mine) | Romanised dev + train queries; mixed-script corpus for E6 | Generated | Released with this repo | `scripts/make_variants.py` |

Download URLs used by `scripts/download_data.py`:
```
https://huggingface.co/datasets/miracl/miracl/resolve/main/miracl-v1.0-hi/topics/topics.miracl-v1.0-hi-{dev,train}.tsv
https://huggingface.co/datasets/miracl/miracl/resolve/main/miracl-v1.0-hi/qrels/qrels.miracl-v1.0-hi-{dev,train}.tsv
https://huggingface.co/datasets/miracl/miracl-corpus/resolve/main/miracl-corpus-v1.0-hi/docs-{0,1}.jsonl.gz
```
Checked on 2026-10-06: not gated, no login token needed.

## Corpus subsample (what a document is)
- One document = one MIRACL passage (`docid` = `articleid#passageno`), with zones `title` and `body`.
- I keep **every passage judged** for any dev or train query, plus a random sample of the other passages (default 100k, `seed = 13`).
- Every system uses the same subsample, so comparisons are fair. Absolute numbers are **not** comparable to the MIRACL leaderboard (which uses the full corpus); I state this as a limitation.

## Models
| Model | Use | Licence | Source |
|---|---|---|---|
| `intfloat/multilingual-e5-small` | Dense encoder (D0); teacher and starting point for the SCD student | MIT | Hugging Face |
| AI4Bharat IndicXlit (optional, B3) | Neural transliteration baseline | Check the repo | AI4Bharat |

## Libraries (role explained in `docs/IR_CONCEPTS.md`)
`indic-transliteration`, `numpy`, `pandas`, `matplotlib`, `scikit-learn` (learning-to-rank + gate only), `onnxruntime`, `transformers`, `torch` (CPU; export and SCD), `pytest`, `rank_bm25` (tests only), `fastapi` + `uvicorn` (demo page). Versions are pinned in `requirements.txt`.

## Ethics
- **No crawling**, so robots.txt doesn't apply. If I add a crawl later: obey robots.txt, wait at least 1 second between requests to the same host, and set a clear user agent.
- **No personal data.** The human query set only rewrites public MIRACL questions.
- Wikipedia text is CC BY-SA. I don't redistribute the corpus; `scripts/download_data.py` downloads it from the source.
