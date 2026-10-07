# Evaluation Protocol

This covers the **"Evaluation metrics" (15 marks)** criterion and report §5. Every number in my report comes from `scripts/run_all_eval.py` → `results/*.csv`.

## 1. Data splits (no leakage)
| Split | Size | What I use it for |
|---|---|---|
| MIRACL-hi **train** topics + qrels | 1,169 queries, 11,668 judgments | Tuning BM25 k1/b and zone weights, training learning-to-rank, the gate and SCD. **Never reported as the test set.** |
| MIRACL-hi **dev** topics + qrels | 350 queries, 3,494 judgments (752 relevant, ≈2.1 per query) | **Test set** for every reported number |
| Human set | 60 dev queries (random, seed 13) | Realistic Hinglish and code-mixed test. Test only. |

Labels are binary (0/1). **Unjudged passages count as non-relevant** (standard TREC practice). I list this as a limitation.

## 2. Query forms
| Code | Form | How it's made | Queries |
|---|---|---|---|
| F1 | Devanagari (original) | MIRACL | 350 |
| F2 | Standard romanisation | `romanize.py`: ITRANS-style transliteration → Hinglish conventions (drop the silent final "a", `aa`→`a`, etc.), deterministic | 350 |
| F3 | Casual romanisation | F2 + seeded spelling noise (vowel length, `w/v`, `z/j`, `ee/i`, `oo/u`, dropped `h` in aspirates) at noise level 0.3 | 350 |
| H-R1, H-R2, H-R3 | Human romanisation by 3 annotators, independently | `docs/QUERY_ANNOTATION_GUIDE.md` | 60 each |
| H-CM | Human code-mixed (Hindi + English words, Roman script) | Annotators | 60 |
| H-EN | Human English | Annotators | 60 |

## 3. Systems
| ID | System | Role |
|---|---|---|
| B0 | BM25, raw whitespace tokens, no normalisation | Naive baseline |
| B1 | BM25 + normalisation + stop words + stemming | Classic baseline |
| B1N | B1 without stemming | Stemming experiment (E2) |
| B2 | B1 + rule-based Roman→Devanagari transliteration of the query | **The obvious baseline** |
| B3 | B1 + neural transliteration (AI4Bharat IndicXlit) | Optional stronger baseline; **not built** (listed in the roadmap) |
| V1 | tf-idf lnc.ltc cosine with B1 preprocessing | VSM comparison |
| S0 | B1 + a classic Soundex zone | Shows why a Hindi-specific key is needed |
| S1 | B1 + Dhvani zone (zone weights tuned on train) | Mine |
| S2 | S1 + pooled df | Mine |
| S3 | S2 + proximity | Mine (best sparse) |
| D0 | Dense multilingual-e5-small (int8 ONNX) | Neural reference |
| D1 | SCD student query encoder (pruned, int8) | Mine |
| H1 | RRF(S3, D1), k = 60 | Hybrid |
| L1 | Learning-to-rank over S3 top-100 with IR + dense features | Mine |
| G1 | Gated cascade: S3, then the neural stage only when the gate fires | Mine (inference-aware) |

## 4. Metrics (definitions to copy into the report)
Binary relevance, ranked list `r_1..r_n`, `R` = the set of relevant passages for the query.

- **P@k** = (number of relevant passages in the top k) / k
- **Recall@k** = (number of relevant passages in the top k) / |R|
- **MRR@10** = 1 / rank of the first relevant passage (0 if none is in the top 10)
- **nDCG@10** = DCG@10 / IDCG@10, with DCG@10 = Σ_{i=1..10} rel_i / log2(i + 1). **Main metric.**
- **Script Gap(f)** = nDCG@10(F1) − nDCG@10(f), averaged over queries; also given as a % of F1. *How much worse a user of script f is served.*
- **CSC@10 (Cross-Script Consistency):** for each query, the average pairwise **RBO** between the top-10 lists of its different forms. With p = 0.9:
  `RBO_ext(S, T) = (X_k / k)·p^k + ((1 − p) / p)·Σ_{d=1..k} (X_d / d)·p^d`, where X_d = |S[:d] ∩ T[:d]| and k = 10.
  Average over queries. 1.0 means every script gets the same ranking.
- **Worst-script nDCG@10** = average over queries of the lowest nDCG@10 among that query's forms.
- **Annotator variation:** average normalised edit distance and character-bigram **Jaccard** between H-R1/2/3; % of words all 3 annotators spelled the same.
- **Efficiency:** median and 95th-percentile query latency on CPU (warm, 3 runs), index size MB, model size MB, % of queries that called the neural encoder. For skip pointers: comparisons per AND query. For cluster pruning: recall@100 vs. exact search, plus speed.

**About P@10:** with about 2.1 relevant passages per query, P@10 can't go above about 0.2. That's why nDCG@10 is the main metric. I explain this in the report.

## 5. Statistical testing
Paired randomisation test over queries (10,000 permutations, two-sided) for the headline comparisons: S3 vs. B2, H1 vs. S3, L1 vs. H1, G1 vs. H1. I call a difference significant only when p < 0.05. I don't run dozens of tests and pick the good ones.

## 6. Experiments
| ID | Question | Output |
|---|---|---|
| E1 | How big is the Script Gap for standard systems? (B0, B1, B2 × all forms) | `results/e1_script_gap.csv`, bar chart |
| E2 | Does stemming help Hindi? (B1 stem on/off) | P/R/nDCG table |
| E3 | How do stop words and idf behave on Hindi? | Zipf plot, highest-df terms, idf histogram |
| E4 | Does the Dhvani zone close the gap? (B2 vs. S0 vs. S1) | Script Gap, CSC, worst-script |
| E5 | Which Dhvani rules matter? (drop one rule at a time) | Ablation table + collision rate per variant |
| E6 | Does pooled df fix inflated idf? (S1 vs. S2 on the mixed-script corpus) | idf of spelling variants before/after + nDCG |
| E7 | Does proximity help? (S2 vs. S3) | Table |
| E8 | What do dense and SCD add? (D0 vs. D1, fp32 vs. int8, pruned vs. not) | nDCG, CSC, model MB, latency |
| E9 | Hybrid and learning-to-rank (H1 vs. L1, feature weights) | Table + feature-weight chart |
| E10 | Quality vs. compute (G1 threshold sweep vs. random gate over 20 seeds vs. always-sparse vs. always-neural) | Budget curve |
| E11 | Efficiency structures: skip pointers, champion lists, cluster pruning | Speed vs. quality tables |
| E12 | How inconsistent is real romanisation? (human set) | Annotator variation table |
| E13 | Why is tf-idf (lnc.ltc) below BM25? | Median length of the top-1 passage, `results/e13_length_bias.json` |

The **mixed-script corpus** for E6 is synthetic: 30% of passages romanised with the same `romanize.py`, seed 13. I say this clearly in the report. It simulates Indian web content where Hindi is often written in Roman script.

## 7. Result tables (filled only from `results/`)
- **Table A, effectiveness:** rows = systems; columns = F1, F2, F3, H-R (average of 3), H-CM, H-EN; cells = nDCG@10 (P@5, Recall@100 and MRR@10 in the appendix).
- **Table B, invariance:** rows = systems; columns = Script Gap F2 / F3 / H-R · CSC@10 · worst-script nDCG@10.
- **Table C, efficiency:** rows = systems; columns = median ms, p95 ms, index MB, model MB, % neural calls.

## 8. Where each result lives
| Experiment | Script | Output |
|---|---|---|
| Main tables (E1, E2, E4, E7–E9) | `scripts/run_all_eval.py` | `results/main_metrics.csv`, `invariance.csv`, `efficiency.csv` |
| E3 corpus statistics | `scripts/corpus_stats.py` | `results/e3_*.csv`, `e3_corpus_stats.json` |
| E5 Dhvani ablation | `scripts/ablation_dhvani.py` | `results/e5_dhvani_ablation.csv` |
| E6 pooled df (mixed corpus) | `scripts/pooled_df_experiment.py` | `results/e6_*.csv` |
| E8 SCD training | `scripts/train_scd.py` | `results/scd_training.json` |
| E10 budget curve | `scripts/gate_budget_curve.py` | `results/e10_budget_curve.csv`, `e10_operating_point.json` |
| E11 efficiency structures | `scripts/efficiency_experiments.py` | `results/e11_efficiency.csv` |
| E12 annotator agreement | `scripts/annotator_agreement.py` | `results/e12_*.json/csv` (after the sheets are filled) |
| E13 length bias | `scripts/length_bias.py` | `results/e13_length_bias.json` |
| Significance | `scripts/significance.py` | `results/significance.csv` |
| Figures | `scripts/make_plots.py` | `results/fig_*.png` |

## 9. Sanity checks (before I trust any number)
- My BM25 gives the same scores as `rank_bm25` on a toy corpus (test).
- B1 on F1 lands roughly in the range published for BM25 on MIRACL-hi. It won't be identical because my corpus is a subsample; I mention it but don't claim it as a benchmark result.
- A random ranker gives near-zero nDCG; an oracle ranker gives 1.0.
- The `--explain` scores for one query match the scores in the eval CSV.
