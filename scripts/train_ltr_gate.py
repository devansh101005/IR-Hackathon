"""Train the learning-to-rank model (L1) and the confidence gate (G1) on the TRAIN split.

Usage: python scripts/train_ltr_gate.py   (needs the dense vectors and the SCD student)
Outputs: models/ltr.pkl, models/gate.pkl,
         results/ltr_weights.csv, results/gate_weights.csv, results/gate_train_curve.csv
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from lipisetu import config
from lipisetu.search import SearchEngine
from lipisetu.query import parse_query
from lipisetu.data import relevant_docs
from lipisetu.rerank.ltr import candidate_features, LTRModel, save_ltr, FEATURE_NAMES
from lipisetu.cascade.gate import gate_features, feature_vector, Gate, save_gate, GATE_FEATURES
from lipisetu.eval.metrics import ndcg_at_k
from lipisetu.eval.run_eval import load_forms, load_qrels, write_rows

FORMS = ["F1", "F2", "F3"]
LTR_QUERIES = 500
GATE_QUERIES = 600
QUALITY_TARGET = 0.99


def sample_qids(forms_dict, how_many, seed):
    qids = sorted(forms_dict["F1"].keys())
    rng = random.Random(seed)
    return sorted(rng.sample(qids, min(how_many, len(qids))))


def train_ltr(engine, forms_dict, qrels):
    rows = []
    labels = []
    qids = sample_qids(forms_dict, LTR_QUERIES, config.SEED)
    for form in FORMS:
        for qid in qids:
            relevant = relevant_docs(qrels, qid)
            if len(relevant) == 0 or qid not in forms_dict[form]:
                continue
            candidates, features = candidate_features(engine, parse_query(forms_dict[form][qid]))
            for i in range(len(candidates)):
                rows.append(features[i])
                labels.append(1 if engine.index.doc_ids[candidates[i]] in relevant else 0)
        print("  LTR features done for", form, flush=True)
    x = np.array(rows)
    y = np.array(labels)
    scaler = StandardScaler().fit(x)
    classifier = LogisticRegression(max_iter=2000, C=1.0, class_weight="balanced")
    classifier.fit(scaler.transform(x), y)
    model = LTRModel(scaler, classifier)
    save_ltr(model)
    weights = model.weights()
    write_rows(os.path.join(config.RESULTS_DIR, "ltr_weights.csv"),
               [{"feature": name, "weight": round(weights[name], 4)} for name in FEATURE_NAMES],
               ["feature", "weight"])
    print("LTR trained on", len(y), "candidates,", int(y.sum()), "relevant. weights:", weights)


def train_gate(engine, forms_dict, qrels):
    features = []
    sparse_ndcg = []
    hybrid_ndcg = []
    qids = sample_qids(forms_dict, GATE_QUERIES, config.SEED + 7)
    for form in FORMS:
        for qid in qids:
            relevant = relevant_docs(qrels, qid)
            if len(relevant) == 0 or qid not in forms_dict[form]:
                continue
            query = parse_query(forms_dict[form][qid])
            sparse = engine.sparse_search(query, "S3", 100)
            hybrid = engine.hybrid_search(query, 100)
            features.append(feature_vector(gate_features(engine, query, sparse)))
            sparse_ndcg.append(ndcg_at_k([engine.index.doc_ids[d] for d, _ in sparse], relevant))
            hybrid_ndcg.append(ndcg_at_k([engine.index.doc_ids[d] for d, _ in hybrid], relevant))
        print("  gate data done for", form, flush=True)
    x = np.array(features)
    sparse_ndcg = np.array(sparse_ndcg)
    hybrid_ndcg = np.array(hybrid_ndcg)
    y = (hybrid_ndcg > sparse_ndcg).astype(int)
    scaler = StandardScaler().fit(x)
    classifier = LogisticRegression(max_iter=2000, C=1.0)
    classifier.fit(scaler.transform(x), y)
    probabilities = classifier.predict_proba(scaler.transform(x))[:, 1]

    # Choose the threshold on TRAIN: fewest neural calls that keep 99% of always-neural quality
    always_neural = float(np.mean(hybrid_ndcg))
    curve = []
    chosen = 0.0
    for threshold in np.linspace(0.0, 1.0, 101):
        use = probabilities >= threshold
        quality = float(np.mean(np.where(use, hybrid_ndcg, sparse_ndcg)))
        curve.append({"threshold": round(float(threshold), 2), "neural_share": round(float(np.mean(use)), 4),
                      "ndcg@10": round(quality, 4)})
        if quality >= QUALITY_TARGET * always_neural:
            chosen = float(threshold)
    gate = Gate(scaler, classifier, chosen)
    save_gate(gate)
    write_rows(os.path.join(config.RESULTS_DIR, "gate_train_curve.csv"), curve,
               ["threshold", "neural_share", "ndcg@10"])
    write_rows(os.path.join(config.RESULTS_DIR, "gate_weights.csv"),
               [{"feature": GATE_FEATURES[i], "weight": round(float(classifier.coef_[0][i]), 4)}
                for i in range(len(GATE_FEATURES))], ["feature", "weight"])
    print("gate: %d train examples, %.1f%% where neural helps, threshold %.2f" % (
        len(y), 100.0 * y.mean(), chosen))


def main():
    engine = SearchEngine()
    if "D1" not in engine.dense:
        print("D1 is missing: run scripts/encode_corpus.py and scripts/train_scd.py first")
        return
    engine.ltr = None
    engine.gate = None
    qrels = load_qrels("train")
    forms_dict = load_forms("train", FORMS)
    train_ltr(engine, forms_dict, qrels)
    train_gate(engine, forms_dict, qrels)


if __name__ == "__main__":
    main()
