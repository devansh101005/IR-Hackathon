# CLAUDE.md: LipiSetu (my CSD358 IR Hackathon project, Track T5)

I'm Devansh. This file tells Claude Code how to work in my repo. Read it, then `PLAN.md`, before doing anything.

## What I'm building
LipiSetu is a **script-invariant Hindi search engine**. A query typed in Devanagari, casual Roman Hindi (Hinglish), code-mixed text or English should return the same results. It's graded with the rubric in `Hackathon file/`. The biggest blocks are **use of IR principles (30)**, **working system (20)** and **evaluation (15)**, so I care about those far more than UI.

- Master plan and build phases: `PLAN.md`
- IR concept → code map (keep it updated): `docs/IR_CONCEPTS.md`
- Evaluation protocol and metric definitions: `docs/EVALUATION.md`
- Data sources and credits: `docs/DATA.md`

## Hard rules
1. **Never fabricate or hard-code results.** Every number in the README, report or video must come from a script in `scripts/` that writes to `results/`. A faked demo gets 0 for "working system".
2. **I write the core IR engine myself**: inverted index, postings, skip pointers, tf-idf, BM25, Boolean/phrase, proximity, heap top-K, champion lists, zones, Soundex, Dhvani key, cluster pruning, RRF. Don't use `rank_bm25`, `pyserini`, `whoosh`, Elasticsearch, `faiss`, sklearn's `TfidfVectorizer` and so on in the main pipeline. They may appear **only in `tests/`** as reference checks.
3. **No test leakage.** MIRACL-hi **dev** queries (and the human query set made from them) are **test only**. All tuning and training (BM25 k1/b, zone weights, learning-to-rank, gate, SCD) uses the **train** split.
4. **Don't copy code** from my VidhiVault project or any online repo or tutorial. Write it fresh; cite ideas in the report.
5. **Don't touch** `Hackathon file/` (the assignment PDF).
6. **Never commit** `data/`, `models/`, `indexes/`, `.venv/` or any file over ~5 MB. Small CSVs/PNGs in `results/` and TSVs in `queries/` **are** committed.
7. **Never push to `main`.** I push my own code. Only push to a working branch if I explicitly ask in that session. At the end of each phase, tell me what changed and suggest a commit message.
8. **Credit everything.** Any new dataset, model or library goes into `docs/DATA.md` and `requirements.txt`.
9. **Follow the phase order** in `PLAN.md` §7. If I ask for a later phase while an earlier one is broken, tell me first.
10. Don't create extra log or notes files about our conversations. Keep the repo to the code and the docs listed here. `docs/AI_USE.md` stays a short, truthful declaration.

## How I want the code written (very important)
I want code that looks like a normal student wrote it: simple, readable Python that I can explain line by line in my video and viva-style questions.

- Use **plain functions**, `for` loops, `if/else`, lists, dicts and sets. A simple class is fine where it's natural (e.g. `InvertedIndex`).
- **Clear variable names**: `doc_id`, `term_freq`, `postings_list`, `query_terms`. No single letters except `i`/`j` in short loops.
- Comments in plain English that explain the **IR idea** before each block, e.g. `# idf = log(N / df): rare terms get higher weight`.
- Every file starts with a short docstring naming the IR concept and lecture topic, e.g. `"""Heap-based top-K selection (Lecture: Scoring and result assembly)."""`
- **Avoid fancy Python**: no decorators (apart from what a library requires), no metaclasses, no `dataclass`, no generators with `yield` unless reading a huge file, no walrus `:=`, no `functools`/`itertools` tricks, no nested or multi-line comprehensions, no `lambda` except a simple sort key, no async, no complex type hints (simple ones like `str`, `int`, `list`, `dict` are OK but optional).
- Keep functions short (roughly under 40 lines). Prefer several small, clearly named functions over one clever one.
- Scripts use `argparse` and an `if __name__ == "__main__":` block.
- Save things with `pickle`, `json` or `numpy.save`. Read and write text with `encoding="utf-8"`.
- Print progress with simple `print()` statements.
- Tests use plain `pytest` functions with simple `assert`s.

## Repository layout
```
CLAUDE.md  PLAN.md  README.md  requirements.txt  .gitignore
src/lipisetu/
  config.py                 # paths, seed, default parameters
  data.py                   # read MIRACL topics, qrels, corpus, query TSVs
  query.py                  # query parsing + the B2 transliteration baseline
  search.py                 # SearchEngine: every system (B0..S3, D0, D1, H1, L1, G1)
  human.py                  # loads the human annotation sheets
  cli.py                    # python -m lipisetu.cli search "..." --explain
  text/normalize.py         # Devanagari + Roman normalisation
  text/tokenize.py          # script-aware tokenizer (see Unicode gotcha)
  text/stopwords.py         # Hindi, Hinglish and English stop words
  text/stemmer.py           # light Hindi suffix stemmer
  text/soundex.py           # classic Soundex (lecture version), used as a comparison
  text/dhvani.py            # cross-script phonetic key (Devanagari + Roman -> same code)
  text/romanize.py          # synthetic query variants: standard and casual romanisation
  text/script.py            # script detection: deva / roman / mixed
  text/analyzer.py          # the shared pipeline: text -> (term, position) per zone
  index/inverted_index.py   # dictionary + postings file, zones, positions, lnc norms
  index/build.py            # build + save/load
  retrieval/boolean.py      # AND/OR/NOT, df-ordered merge, skip pointers, phrase queries
  retrieval/tfidf.py        # lnc.ltc cosine
  retrieval/bm25.py         # BM25 with zone weights, pooled-df option
  retrieval/proximity.py    # smallest window containing the query terms
  retrieval/topk.py         # heap top-K, champion lists
  retrieval/rrf.py          # reciprocal rank fusion (k = 60)
  dense/encoder.py          # ONNX encoder ("query: " / "passage: " prefixes!)
  dense/export_onnx.py      # export + int8 quantisation
  dense/retriever.py        # D0 / D1 dense retrievers over the passage vectors
  dense/cluster_pruning.py  # leaders/followers approximate search
  dense/scd.py              # script-consistency distillation helpers
  dense/prune_vocab.py      # vocabulary pruning
  rerank/ltr.py             # learning-to-rank over IR features
  cascade/gate.py           # IR-signal features + logistic gate
  eval/metrics.py           # P@k, R@k, nDCG@k, MRR, RBO, CSC
  eval/run_eval.py          # run systems x query forms, Script Gap, worst-script
scripts/                    # one script per step / experiment (see README)
queries/                    # committed TSVs: synthetic forms + human annotation sheets
results/                    # committed CSVs, JSON and PNG figures (small)
docs/                       # plan docs, pipeline diagram, report
tests/                      # pytest; reference checks live here
app/server.py, app/static/  # FastAPI backend + one hand-written HTML/CSS/JS page
data/ models/ indexes/      # gitignored, rebuilt by the scripts
```

## Commands (keep these working; the README mirrors them)
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export PYTHONPATH=src                                  # Windows PowerShell: $env:PYTHONPATH="src"
python scripts/download_data.py
python scripts/build_subsample.py --size 100000 --seed 13
python scripts/make_variants.py
python scripts/build_index.py && python scripts/build_index.py --mixed
python scripts/tune_sparse.py
python scripts/export_dense.py && python scripts/encode_corpus.py
python scripts/train_scd.py
python scripts/train_ltr_gate.py
python scripts/run_all_eval.py
python -m lipisetu.cli search "kal ka mausam" --system S3 --explain
python app/server.py                                   # http://127.0.0.1:8000
pytest -q
```

## Environment notes
- Python 3.10-3.13. The cloud session has Python 3.13, 4 CPU cores, about 15 GB RAM and **no GPU**. Keep everything CPU-friendly (int8 ONNX, small batches, SCD trains on short queries only).
- The cloud container can be reset. Everything in `data/`, `models/` and `indexes/` must be rebuildable from scripts.
- Fix the random seed everywhere (`SEED = 13` in `config.py`). Every results CSV has the columns `system`, `query_form`, `metric`, `value`, `n_queries`.

## Gotchas (read before writing text-processing code)
- **Python `re` `\w` does NOT match Devanagari vowel signs.** `re.findall(r"\w+", "हिन्दी")` gives `['ह', 'न', 'द']`. Tokenise with explicit ranges (`[ऀ-ॿ]+` for Devanagari, `[a-z0-9]+` for Roman). Unit test: `"हिन्दी"` → one token.
- Normalisation order: Unicode **NFC first**, then nukta folding (क़→क, ज़→ज, फ़→फ, ड़/ढ़ handled consistently), chandrabindu (ँ) → anusvara (ं), strip ZWJ/ZWNJ (U+200D/U+200C), Devanagari digits ०-९ → 0-9, danda (। ॥) as punctuation.
- Roman normalisation: lowercase, collapse 3+ repeated letters ("bahuuut" → "bahut"), strip punctuation, keep digits.
- MIRACL doc ids look like `69380#11` (article#passage). Qrels are TREC format `qid Q0 docid rel` with rel 0 or 1. **Unjudged = non-relevant.**
- MIRACL-hi dev has about 2.1 relevant passages per query, so P@10 ≤ ~0.2. The main metric is nDCG@10.
- e5 models need prefixes: `"query: ..."` and `"passage: ..."`, or quality drops a lot.
- Dhvani key: **don't** cut it to 4 characters like English Soundex (Hindi words are short). Collapse adjacent duplicate sound classes; keep the first sound.
- Pooled df: in the surface zone a term's idf can use the df of its Dhvani class. Keep it behind a flag (`pooled_df=True`) so S1 vs. S2 is a clean comparison.
- Champion lists and cluster pruning trade quality for speed; always report both.
- The gate and learning-to-rank labels come from **train** queries only. Compare the gate against a random gate with the same budget.

## Definition of done
The checklists in `PLAN.md` §9–10. The README must rebuild the system from a fresh clone; the last step before submitting is a clean-folder reproduction test.
