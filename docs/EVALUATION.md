# Evaluation Protocol

Covers the **"Evaluation metrics" (15 marks)** criterion and report §5. Every number in the report must come from `scripts/run_all_eval.py` → `results/*.csv`.

## 1. Data splits (no leakage)
| Split | Size | Use |
|---|---|---|
| MIRACL-hi **train** topics + qrels | 1,169 queries, 11,668 judgments | Tune BM25 k1/b and zone weights, train the gate, train SCD. **Never report as the test set.** |
| MIRACL-hi **dev** topics + qrels | 350 queries, 3,494 judgments (752 relevant, ≈2.1 per query) | **Test set** for all reported numbers |
| Human set | 60 dev queries (stratified random, seed 13) | Realistic test of Hinglish and code-mixed input. Test only. |

Relevance labels are binary (0/1). **Unjudged passages count as non-relevant** (standard TREC practice). This is stated as a limitation.

## 2. Query forms
| Code | Form | How it's produced | Queries |
|---|---|---|---|
| F1 | Devanagari (original) | MIRACL | 350 |
| F2 | Standard romanisation | `romanize.py`: ITRANS-style transliteration → lowercased Hinglish conventions (word-final schwa removed, `aa`→`a` etc.), deterministic | 350 |
| F3 | Casual romanisation | F2 + seeded spelling noise (vowel-length swaps, `w/v`, `z/j`, `ee/i`, `oo/u`, dropped `h` in aspirates) with noise level p = 0.3 | 350 |
| H-R1, H-R2, H-R3 | Human romanisation by 3 annotators, independently | `docs/QUERY_ANNOTATION_GUIDE.md` | 60 each |
| H-CM | Human code-mixed (Hindi + English words in Roman script) | Annotators | 60 |
| H-EN | Human English | Annotators | 60 |

## 3. Systems
| ID | System | Role |
|---|---|---|
| B0 | BM25, raw whitespace tokens, no normalisation | Naive baseline |
| B1 | BM25 + normalisation + stop words + stemming | Classic baseline (also run with stemming **off** for the T5 ablation) |
| B2 | B1 + rule-based Roman→Devanagari transliteration of the query | **The obvious baseline** most teams will build |
| B3 | B1 + neural transliteration (AI4Bharat IndicXlit) | Stretch; stronger baseline if it installs quickly |
| V1 | tf-idf lnc.ltc cosine with the B1 preprocessing | VSM comparison |
| S1 | B1 + Dhvani zone (zone weights tuned on train) | Ours |
| S2 | S1 + pooled df | Ours |
| D0 | Dense multilingual-e5-small (int8 ONNX) | Neural reference |
| H1 | RRF(S2, D0), k = 60 | Hybrid |
| G1 | Gated cascade: S2, then H1 only when the gate fires | Ours (inference-aware) |
| D1 / H2 | SCD student query encoder / RRF(S2, D1) | Stretch |

## 4. Metrics (definitions to copy into the report)
Binary relevance, ranked list `r_1..r_n`, `R` = set of relevant passages for the query.

- **P@k** = |{relevant in top k}| / k
- **Recall@k** = |{relevant in top k}| / |R|
- **MRR@10** = 1 / rank of the first relevant passage (0 if none in the top 10)
- **nDCG@10** = DCG@10 / IDCG@10, with DCG@10 = Σ_{i=1..10} rel_i / log2(i + 1). **Primary metric.**
- **Script Gap(f)** = nDCG@10(F1) − nDCG@10(f), averaged over queries; also reported as a % of F1. *How much worse a user of script f is served.*
- **CSC@10 (Cross-Script Consistency)**: for each query, the mean pairwise **RBO** between the top-10 lists of its forms. With p = 0.9 we use the extrapolated form
  `RBO_ext(S, T) = (X_k / k)·p^k + ((1 − p) / p)·Σ_{d=1..k} (X_d / d)·p^d`, where X_d = |S[:d] ∩ T[:d]| and k = 10.
  The system's CSC@10 is the mean over queries. It is 1.0 when every script gets the same ranking.
- **Worst-script nDCG@10** = mean over queries of min over forms of nDCG@10. *How badly the worst-served script does.*
- **Annotator variation**: mean normalised Levenshtein distance and character-bigram **Jaccard** between H-R1/2/3 for the same query; % of tokens spelled identically by all 3.
- **Efficiency**: p50/p95 query latency on a laptop CPU (warm, 3 runs), index size MB, model size MB, % of queries that called the neural encoder.

**About P@10:** with about 2.1 relevant passages per query, the maximum possible P@10 is about 0.2. That's why nDCG@10 is primary. Explain this in the report.

## 5. Statistical testing
Paired randomisation test over queries (10,000 permutations, two-sided) for the headline comparisons:
S2 vs. B2, H1 vs. S2 and G1 vs. H1. Report p-values; call a difference significant only if p < 0.05. Don't run dozens of tests and cherry-pick.

## 6. Experiments
| ID | Question | Systems × forms | Output |
|---|---|---|---|
| E1 | How big is the Script Gap for standard systems? | B0, B1, B2 × F1–F3, human set | `results/e1_script_gap.csv`, bar chart |
| E2 | Does stemming help Hindi? (T5 hook) | B1 stemming on/off × F1 | P/R/nDCG table |
| E3 | How do stop words and idf behave on Hindi? (T5 hook) | Corpus statistics | Zipf plot, highest-df terms, idf histogram |
| E4 | Does the Dhvani zone close the gap? | B2 vs. S1 × all forms | Script Gap, CSC, worst-script |
| E5 | Does pooled df fix idf inflation? | S1 vs. S2 on the mixed-script corpus variant (30% of passages romanised, seed 13) | idf of variant spellings before/after + nDCG |
| E6 | How much do dense models and fusion add? | D0, H1 vs. S2 × all forms (including H-CM, H-EN) | Table |
| E7 | Quality vs. compute | G1 at threshold sweep vs. random gate (20 seeds) vs. always-sparse vs. always-hybrid | Budget curve plot |
| E8 | Champion lists: speed vs. quality | S2 with/without champion lists | Table |
| E9 (stretch) | Does SCD give a small script-invariant encoder? | D0 vs. D1 (fp32/int8, pruned) | nDCG, CSC, model MB, latency |
| E10 | How inconsistent is real romanisation? | Human set only | Annotator variation table |

The **mixed-script corpus variant** for E5 is synthetic (romanised with the same `romanize.py`). Say so clearly. It simulates real Indian web content where Hindi often appears in Roman script.

## 7. Result table templates (filled only from `results/`)
**Table A, effectiveness (dev, nDCG@10 / P@5 / Recall@100 / MRR@10):** rows = systems, columns = F1, F2, F3, H-R (mean of 3), H-CM, H-EN.
**Table B, invariance:** rows = systems, columns = Script Gap F2, F3, H-R · CSC@10 · worst-script nDCG@10.
**Table C, efficiency:** rows = systems, columns = p50 ms, p95 ms, index MB, model MB, % neural calls.

## 8. Sanity checks (run before trusting any number)
- Our BM25 matches `rank_bm25` on a toy corpus (test).
- F1 nDCG@10 for B1 is roughly in the range published for BM25 on MIRACL-hi. It won't be identical because our corpus is a subsample; mention it but don't claim it as a benchmark result.
- A random ranker gives near-zero nDCG; an oracle (qrels first) gives 1.0.
- `--explain` scores for one query match the scores in the eval CSV.
