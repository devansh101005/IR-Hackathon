"""E10: quality vs compute for the gated cascade, on the DEV queries.

For every dev query (all forms) I run S3 (cheap) and H1 (with the neural
stage) once, and ask the gate for its probability. Then, for many thresholds,
I compute the share of queries that use the neural stage and the nDCG@10.
Baselines on the same curve:
    random gate  - picks the same share of queries at random (average of 20 seeds)
    oracle gate  - uses neural exactly when it helps (an upper bound, not a real system)
Output: results/e10_budget_curve.csv, results/e10_operating_point.json
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np

from lipisetu import config
from lipisetu.search import SearchEngine
from lipisetu.query import parse_query
from lipisetu.data import relevant_docs
from lipisetu.cascade.gate import gate_features, feature_vector
from lipisetu.eval.metrics import ndcg_at_k
from lipisetu.eval.run_eval import load_forms, load_qrels, write_rows

FORMS = ["F1", "F2", "F3"]
RANDOM_SEEDS = 20


def main():
    engine = SearchEngine()
    qrels = load_qrels("dev")
    forms_dict = load_forms("dev", FORMS)
    features = []
    sparse_ndcg = []
    hybrid_ndcg = []
    for form in FORMS:
        for qid in forms_dict[form]:
            relevant = relevant_docs(qrels, qid)
            if len(relevant) == 0:
                continue
            query = parse_query(forms_dict[form][qid])
            sparse = engine.sparse_search(query, "S3", 100)
            hybrid = engine.hybrid_search(query, 100)
            features.append(feature_vector(gate_features(engine, query, sparse)))
            sparse_ndcg.append(ndcg_at_k([engine.index.doc_ids[d] for d, _ in sparse], relevant))
            hybrid_ndcg.append(ndcg_at_k([engine.index.doc_ids[d] for d, _ in hybrid], relevant))
    sparse_ndcg = np.array(sparse_ndcg)
    hybrid_ndcg = np.array(hybrid_ndcg)
    probabilities = engine.gate.probabilities(features)
    n = len(sparse_ndcg)

    rows = []
    for threshold in np.linspace(0.0, 1.0, 51):
        use = probabilities >= threshold
        share = float(np.mean(use))
        gated = float(np.mean(np.where(use, hybrid_ndcg, sparse_ndcg)))
        # random gate with the same budget
        k = int(round(share * n))
        random_values = []
        for seed in range(RANDOM_SEEDS):
            rng = random.Random(seed)
            chosen = set(rng.sample(range(n), k))
            values = [hybrid_ndcg[i] if i in chosen else sparse_ndcg[i] for i in range(n)]
            random_values.append(np.mean(values))
        rows.append({"threshold": round(float(threshold), 2), "neural_share": round(share, 4),
                     "gate_ndcg@10": round(gated, 4), "random_ndcg@10": round(float(np.mean(random_values)), 4)})

    oracle = float(np.mean(np.maximum(sparse_ndcg, hybrid_ndcg)))
    oracle_share = float(np.mean(hybrid_ndcg > sparse_ndcg))
    use = probabilities >= engine.gate.threshold
    point = {
        "queries": n,
        "always_sparse_ndcg@10": round(float(np.mean(sparse_ndcg)), 4),
        "always_neural_ndcg@10": round(float(np.mean(hybrid_ndcg)), 4),
        "gate_threshold_from_train": engine.gate.threshold,
        "gate_neural_share": round(float(np.mean(use)), 4),
        "gate_ndcg@10": round(float(np.mean(np.where(use, hybrid_ndcg, sparse_ndcg))), 4),
        "oracle_ndcg@10": round(oracle, 4),
        "oracle_neural_share": round(oracle_share, 4),
    }
    write_rows(os.path.join(config.RESULTS_DIR, "e10_budget_curve.csv"), rows,
               ["threshold", "neural_share", "gate_ndcg@10", "random_ndcg@10"])
    with open(os.path.join(config.RESULTS_DIR, "e10_operating_point.json"), "w", encoding="utf-8") as f:
        json.dump(point, f, indent=2)
    print(json.dumps(point, indent=2))


if __name__ == "__main__":
    main()
