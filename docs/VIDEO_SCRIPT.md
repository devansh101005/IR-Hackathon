# Demo Video Script (target 7:00; allowed 5–8 minutes)

PDF rules: **no slides**, show the system **running live**, show **intermediate output** (postings, weights, scores), show **evaluation vs. a baseline**, show **at least one limitation**, and **each member explains their component**. Upload as **unlisted** YouTube or a Drive link (check that it opens in incognito).

Recording setup: screen recording (OBS / Loom / Zoom) of the terminal + editor, with a face camera optional. Use a large terminal font (≥ 18 pt). Build the index **before** recording; no live waiting.

| Time | Speaker | On screen | What to say (points, not a script to read) | PDF item |
|---|---|---|---|---|
| 0:00–0:50 | Teammate A | A terminal showing `queries/human/` with 3 people's romanisations of the same query | The problem: Hindi users type in Roman script, and everyone spells differently (show *mausam / mosam / mousam*). Standard search serves them worse; we call this the Script Gap. Track T5. | 1 |
| 0:50–2:30 | Devansh | `python -m lipisetu.cli search "kal ka mausam" --explain`, then the same query in Devanagari, then a code-mixed one | End to end: script detection → normalise → stem → **Dhvani keys** → postings → df/idf → per-zone BM25 → gate decision → ranking. Show the same top results across scripts. | 2, 3 |
| 2:30–3:30 | Devansh | Editor: `text/dhvani.py`, `retrieval/bm25.py` (pooled df), `retrieval/topk.py` | The code behind it: Dhvani mapping table, pooled-df formula, heap top-K, zone weights tuned on train. | 3 |
| 3:30–4:00 | Devansh | A Boolean query + a phrase query live | AND/NOT with df ordering; positional phrase match. | 2, 3 |
| 4:00–5:40 | Teammate B | `python scripts/run_all_eval.py` output (small run, or show the CSV), then the plots | Evaluation: baseline B2 vs. ours on nDCG@10, P@5, Recall@100; Script Gap and CSC tables; budget curve (quality vs. % neural calls); significance. | 4 |
| 5:40–6:20 | Teammate B | A live query that fails (e.g. a Dhvani collision or an English query the sparse path misses) | **A limitation, shown live**, and why it happens. | 2 |
| 6:20–7:00 | Teammate A, then Devansh | `results/` annotator-variation table | Teammate A: what the human set showed. Devansh: next steps (more languages, on-device ONNX Web demo). | 5 |

## Before recording
- [ ] Index built; all commands tested once in the recording terminal
- [ ] Every number on screen comes from `results/`
- [ ] Each member has rehearsed their part once (≤ 2 minutes each)
- [ ] Total length checked: between 5:00 and 8:00
