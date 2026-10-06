# CLAUDE.md: LipiSetu (CSD358 IR Hackathon, Track T5)

Instructions for Claude Code in this repo. Read this file, then `PLAN.md`, before doing anything.

## What this project is
LipiSetu is a **script-invariant Hindi search engine**. A query typed in Devanagari, casual Roman Hindi (Hinglish), code-mixed text or English should return the same results. It is graded under a rubric (PDF in `Hackathon file/`). The largest blocks are **use of IR principles (30)**, **working system (20)** and **evaluation (15)**. Optimise for those, not for UI.

- Master plan, tiers, timeline: `PLAN.md`
- IR concept → code mapping (keep it updated): `docs/IR_CONCEPTS.md`
- Evaluation protocol and metric definitions: `docs/EVALUATION.md`
- Data sources and credits: `docs/DATA.md`
- AI-use log (append every session): `docs/AI_USE.md`

## Hard rules (breaking any of these can cost marks or break academic integrity)
1. **Never fabricate or hard-code results.** Every number in the README, report or video comes from a script in `scripts/` that writes to `results/`. A faked demo scores 0 for "working system".
2. **The core IR engine is written from scratch**: inverted index, postings, tf-idf, BM25, Boolean/phrase, heap top-K, champion lists, zones, Dhvani key. Do **not** use `rank_bm25`, `pyserini`, `whoosh`, Elasticsearch, `sklearn` `TfidfVectorizer` and so on in the main pipeline. They may appear **only in `tests/`** as reference checks.
3. **No test leakage.** MIRACL-hi **dev** queries (and the human query set built from them) are **test only**. All tuning (BM25 k1/b, zone weights, gate threshold, SCD training) uses the **train** split.
4. **Do not copy code** from VidhiVault or any online repo or tutorial. Write it fresh; cite ideas in the report.
5. **Do not touch** `Hackathon file/` (the assignment PDF).
6. **Never commit** `data/`, `models/`, `indexes/`, `.venv/` or anything over ~5 MB. They are in `.gitignore`. Small result CSVs/plots in `results/` and query TSVs in `queries/` **are** committed.
7. **Claude does not push.** Devansh pushes. At the end of a work chunk, suggest a commit message and the `git add` paths; don't run `git push`.
8. **Log AI use.** At the end of each session append a row to `docs/AI_USE.md`: what was generated, which files, what was checked by hand.
9. **Credit everything.** Any new dataset, model or library goes into `docs/DATA.md` (credits + licence) and `requirements.txt`.
10. **Respect tiers.** Finish MUST before SHOULD and SHOULD before STRETCH (`PLAN.md` §7). If asked to start a stretch item while a MUST item is broken, say so first.

## Repository layout (target)
```
CLAUDE.md  PLAN.md  README.md  requirements.txt  .gitignore
src/lipisetu/
  config.py                 # paths, seeds, default params (k1, b, zone weights, corpus size)
  text/normalize.py         # Devanagari + Roman normalisation
  text/tokenize.py          # script-aware tokenizer (see Unicode gotcha below)
  text/stopwords.py         # corpus-df-derived + standard Hindi stop list
  text/stemmer.py           # lightweight Hindi suffix stemmer (Ramanathan & Rao style)
  text/dhvani.py            # cross-script phonetic key (Devanagari + Roman → same code)
  text/romanize.py          # synthetic query variants: F2 standard, F3 casual (seeded noise)
  text/script.py            # script detection: deva / roman / mixed
  index/inverted_index.py   # positional postings, zones {title, body, dhvani}, df, doc lengths
  index/build.py            # build + save/load (pickle or numpy, with version stamp)
  retrieval/boolean.py      # AND/OR/NOT, intersection ordered by increasing df, phrase queries
  retrieval/tfidf.py        # lnc.ltc cosine (VSM)
  retrieval/bm25.py         # BM25 with zone weights, pooled-df option
  retrieval/topk.py         # heap-based top-K; champion lists
  dense/encoder.py          # e5-small ONNX int8 encoder ("query: " / "passage: " prefixes!)
  dense/export_onnx.py      # export + dynamic int8 quantisation
  dense/scd_train.py        # STRETCH: script-consistency distillation
  dense/prune_vocab.py      # STRETCH: vocabulary pruning
  fusion/rrf.py             # reciprocal rank fusion (k = 60)
  cascade/gate.py           # IR-signal features + logistic gate
  eval/metrics.py           # P@k, R@k, nDCG@k, MRR@k, RBO, Script Gap, CSC, worst-script
  eval/run_eval.py          # runs systems × query forms → results/*.csv
  eval/significance.py      # paired randomisation test
  cli.py                    # `python -m lipisetu.cli search "..." --explain`
scripts/                    # download_data.py, build_subsample.py, make_variants.py,
                            # build_index.py, encode_corpus.py, run_all_eval.py, make_plots.py
queries/                    # committed TSVs: synthetic forms + human annotations
results/                    # committed CSVs + PNG plots (small)
tests/                      # pytest; reference checks live here
app/streamlit_app.py        # STRETCH, thin UI only
data/ models/ indexes/      # gitignored
```

## Commands (keep these working; the README mirrors them)
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                                       # if pyproject exists; else set PYTHONPATH=src
python scripts/download_data.py                        # MIRACL-hi topics, qrels, corpus shards → data/
python scripts/build_subsample.py --size 100000 --seed 13
python scripts/make_variants.py                        # F2/F3 synthetic forms → queries/
python scripts/build_index.py                          # → indexes/
python -m lipisetu.cli search "kal ka mausam" --system S2 --explain
python scripts/run_all_eval.py                         # → results/*.csv
python scripts/make_plots.py                           # → results/*.png
pytest -q
```

## Conventions
- Python 3.11, type hints, small pure functions; numpy for vectors. No heavy frameworks in the core engine.
- Every module docstring starts with the **IR concept and lecture topic** it implements, e.g. `"""Heap-based top-K selection (Scoring & result assembly)."""`. This feeds the report and video.
- Fix seeds (`config.SEED = 13`). Every results CSV includes `system`, `query_form`, `metric`, `value`, `n_queries`, `config_hash`, `git_commit`.
- Read and write files with `encoding="utf-8"` explicitly (Windows default encodings corrupt Devanagari).
- `--explain` output must show real intermediate values: tokens → normalised → stems → Dhvani keys → df/idf → postings excerpt → per-zone scores → gate decision → final rank.
- When a component is done: tests pass, `docs/IR_CONCEPTS.md` row updated (status + file path), README "What works" updated honestly.

## Gotchas (read before writing text-processing code)
- **Python `re` `\w` does NOT match Devanagari vowel signs (matras, virama).** `re.findall(r"\w+", "हिन्दी")` splits the word. Tokenise with explicit ranges (`[ऀ-ॿ]+` for Devanagari, `[a-z0-9]+` for Roman) or the `regex` module with `[\p{L}\p{M}\p{N}]+`. Unit test: `"हिन्दी"` → one token.
- Normalisation order: Unicode **NFC first**, then nukta folding (क़→क, ज़→ज, फ़→फ, ड़/ढ़ handled consistently), chandrabindu (ँ) → anusvara (ं), strip ZWJ/ZWNJ (U+200D/U+200C), Devanagari digits ०-९ → 0-9, danda (। ॥) as punctuation.
- Roman normalisation: lowercase, collapse runs of 3+ identical letters ("bahuuut" → "bahut"), strip punctuation. Keep digits.
- MIRACL ids: doc ids look like `69380#11` (article#passage). Qrels are TREC format `qid Q0 docid rel`, rel ∈ {0, 1}. **Unjudged = non-relevant.**
- MIRACL-hi dev has about 2.1 relevant passages per query, so P@10 ≤ ~0.2. Primary metric is nDCG@10.
- e5 models need prefixes: `"query: ..."` for queries and `"passage: ..."` for passages, or quality drops sharply.
- Dhvani key: do **not** truncate to 4 characters like English Soundex (Hindi words are short; truncation over-merges). Collapse adjacent duplicate classes; keep the first sound.
- Pooled df: in the surface zone, a term's idf may use the df of its Dhvani class (Pirkola-style). Keep it behind a flag (`pooled_df=True`) so S1 vs. S2 is a clean ablation.
- Champion lists trade quality for speed; always report both.
- Gate training labels come from **train** queries only; compare against a random gate at the same neural-call budget.

## Definition of done for the hackathon
See the checklists in `PLAN.md` §10–11. The README must reproduce the system from a fresh clone. The last task before submitting is a clean-folder reproduction test.
