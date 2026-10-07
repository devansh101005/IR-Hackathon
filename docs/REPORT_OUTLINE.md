# Report Outline (PDF, ≤ 8 pages excluding references and appendix)

**The report is already generated:** `docs/report/LipiSetu_report.pdf` (from `docs/report/report.html`).
- Every number and table is filled in from `results/` by `scripts/make_report.py`.
- To change the wording, edit `scripts/report_text.py`, then run `python scripts/make_report.py` and
  `node scripts/print_pdf.js` (or open `report.html` in Chrome → Print → Save as PDF).
- Before submitting: fill in the team names, the video link, and the "what actually happened" work division.
- Current length: main text about 6 pages, then references and a 3-page appendix.

The structure below is what the PDF asks for (kept for reference).

The structure is exactly what the assignment PDF asks for, and the page budget adds up to 8. I'll write it in LaTeX (an IEEE two-column template fits a lot into 8 pages) or Google Docs exported to PDF.
**Every number comes from `results/`. Every figure comes from `scripts/make_plots.py`.**

| § | Section (from the PDF) | Pages | What goes in it |
|---|---|---|---|
| — | Title, team, track, links | 0.2 | "LipiSetu: Script-Invariant Hindi Search", T5, repo URL, unlisted video URL |
| 1 | **Problem and track relevance** | 0.8 | The user need (Roman-script Hindi users get worse search); the Script Gap in one sentence; why it's a T5 theme; **papers referred** (list in `PLAN.md` §1), especially Gupta et al. SIGIR 2014 and FIRE MSIR as the closest prior work |
| 2 | **How I used IR** | 2.0 | **Pipeline diagram**; one paragraph + formula per principle: normalisation and tokenisation (the `\w` vowel-sign pitfall), stop words + idf on Hindi (E3), stemmer (E2), positional index + phrase, skip pointers, Boolean with df ordering, tf-idf lnc.ltc, BM25 with zones, **Dhvani key** (rule table + examples + ablation E5), pooled df (formula), proximity, heap top-K, champion lists, cluster pruning. **Where in the code** (file paths) and **why each was chosen**. Library roles in IR terms (table from `docs/IR_CONCEPTS.md`). |
| 3 | **Beyond IR** | 0.9 | Dense e5-small (int8 ONNX); **SCD** distillation + vocabulary pruning (model size before/after); learning-to-rank (features + learned weights); the gated cascade (query-performance features, logistic gate). How each one **supports** the IR side rather than replacing it. |
| 4 | **Novelty and creativity** | 0.7 | Table "obvious baseline (B2) vs. LipiSetu" (`PLAN.md` §2.1–2.2); N1–N7; the **honest prior-art paragraph** (`PLAN.md` §2.3) |
| 5 | **Evaluation** | 2.0 | Setup (splits, forms, systems, metric formulas incl. RBO); Table A (effectiveness), Table B (invariance), Table C (efficiency); figures: Script Gap bars, budget curve (E10), annotator variation (E12); significance results; the P@10 ceiling note |
| 6 | **Limitations and next steps + roadmap** | 0.7 | Subsampled corpus; unjudged = non-relevant; synthetic romanisation and mixed corpus; Dhvani collisions (with numbers); Hindi only; small human set. **Course-project roadmap:** more languages (MIRACL bn/te), voice queries, an on-device browser demo with ONNX Runtime Web, a bigger human set, a write-up for FIRE |
| 7 | **Work division** | 0.3 | From `docs/WORK_DIVISION.md` ("what actually happened") |
| — | **AI-use declaration** | 0.4 | From `docs/AI_USE.md` |
| — | References | (not counted) | Every paper, dataset and model |
| — | Appendix | (not counted) | Full Dhvani mapping table, extra tables, sample `--explain` output |

## Figures
1. Pipeline diagram (draw.io or TikZ, based on `PLAN.md` §3)
2. Script Gap per system (grouped bars by query form)
3. Budget curve: nDCG@10 vs. % neural calls (gate vs. random vs. extremes)
4. Zipf plot + idf histogram for the Hindi corpus
5. Dhvani rule ablation (bar chart)
6. Annotator variation (how many spellings per word)

## Checklist before submitting
- [ ] Each IR principle names its **file path** and **why** I chose it
- [ ] No "first" or "state of the art" claims; "to my knowledge" where needed
- [ ] Every number matches `results/*.csv`
- [ ] ≤ 8 pages before references
- [ ] Repo and video links open in an incognito window
