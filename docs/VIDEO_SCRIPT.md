# Demo Video Script (target 7:30; allowed 5–8 minutes)

PDF rules: **no slides**, the system **running live**, **intermediate output** (postings, weights, scores), **evaluation vs. a baseline**, **at least one limitation**, and **every member explains their component**. Upload as **unlisted** YouTube or a Drive link and check it opens in an incognito window.

## Before recording
```bash
source .venv/bin/activate            # Windows: .venv\Scripts\activate
export PYTHONPATH=src                # Windows PowerShell: $env:PYTHONPATH="src"
python app/server.py                 # leave running; open http://127.0.0.1:8000
```
- Terminal font ≥ 18 pt, browser zoom 110–125%.
- Run every command below once before recording (the first search loads the index and models, about 5 s).
- All numbers on screen come from `results/` (the Evidence section of the page reads them directly).

## Script

| Time | Speaker | On screen | What to say (points, not a script to read) | PDF item |
|---|---|---|---|---|
| 0:00–0:50 | Devansh | Web page top: the **mausam / mosam / मौसम → MSM** illustration | The problem: Hindi users type in Roman letters with their own spellings, and Hindi content is in Devanagari. Standard search serves them far worse: the Script Gap. Track T5. | 1 |
| 0:50–1:40 | Devansh | Terminal: `python -m lipisetu.cli compare "bharat ka samvidhan kab lagu hua" --systems B1,B2,S3` | BM25 finds nothing useful, the obvious transliteration baseline (B2) finds the wrong भरत, LipiSetu finds the constitution passages. | 2 |
| 1:40–3:00 | Devansh | `python -m lipisetu.cli search "kal ka mausam kaisa rahega" --system S3 --explain` | Walk down the output: tokens and script → stop words → stems → **Dhvani keys** → df/idf per zone (surface df = 0, Dhvani zone matches) → pooled df → **real postings** with positions → per-zone BM25 + proximity window → ranking. | 3 |
| 3:00–3:40 | Devansh | Editor: `text/dhvani.py` (rules at the top), `retrieval/bm25.py` (`pooled_df_table`) | The rules and why each exists; pooled df = Pirkola applied to spellings. Mention the ablation: dropping vowels is the most important rule. | 3 |
| 3:40–4:20 | Devansh | Web page: search `भारत का संविधान कब लागू हुआ`, point at the strip "Same question in Roman: RBO …" and the trace panel; switch to **G1 cascade** and show the gate meter | Same question, two scripts, nearly the same top 10 for LipiSetu vs almost none for the baseline. The gate decides when the neural stage is worth running. | 2, 3 |
| 4:20–5:20 | Devansh | Evidence section of the page (tiles, nDCG chart, budget curve, ablation table) | Baseline vs LipiSetu (nDCG@10, P@5, Recall@100), Script Gap and consistency, quality vs % neural calls, the 448 MB → 37 MB encoder, significance. | 4 |
| 5:20–6:20 | Anamika Pal | `results/e12_annotator_agreement.json` + `queries/human/` sheets | How differently three people romanised the same 60 questions, and how often the Dhvani keys still agree. | 5 |
| 6:20–7:10 | Abhinav Bachchas | Web page: search `kal ka mausam` and point at the **खेल** results; then `results/fig_ndcg_by_system.png` | **Limitation shown live**: *kal* and *khel* share the key KL (aspiration and vowels are dropped), so sports passages leak in. Also: the base dense model returns Roman-script junk for Roman queries (script bias). | 2, 4, 5 |
| 7:10–7:30 | Devansh | README "What works / planned" | Next steps: more languages, on-device browser demo, bigger human set. | — |

## Checklist
- [ ] Every member speaks about the part they actually did
- [ ] At least one limitation shown live (kal / khel)
- [ ] Baseline comparison shown (B2 vs S3, numbers from `results/`)
- [ ] Total length between 5:00 and 8:00
