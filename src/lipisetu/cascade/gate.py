"""Confidence gate: should this query also run the neural stage?

(Ideas from query performance prediction - Shtok, Kurland et al., NQC - and
cascade ranking - Wang, Lin and Metzler, SIGIR 2011.)

Running the neural encoder for every query costs time and battery on a phone.
But for many queries the cheap sparse engine is already good. The gate looks
at signals the sparse engine gives me for free, and predicts whether the
neural stage will improve the ranking:

    top_score       BM25 score of the best document
    score_gap       (top1 - top10) / top1    a clear winner means a confident answer
    nqc             std of the top-100 scores / top1   (normalised query commitment)
    dhvani_only     share of query words that matched ONLY through the Dhvani zone
    unmatched       share of query words that matched nothing at all
    max_idf         idf of the rarest matched word
    query_length    number of content words
    roman_query     1 if the query has Roman words

Labels come from the TRAIN split: 1 if the hybrid (H1) beat S3 on nDCG@10.
The threshold is chosen on TRAIN too: the fewest neural calls that still keep
99% of the always-neural quality.
"""
import os
import pickle

import numpy as np

from lipisetu import config
from lipisetu.retrieval.bm25 import bm25_idf

GATE_FEATURES = ["top_score", "score_gap", "nqc", "dhvani_only", "unmatched",
                 "max_idf", "query_length", "roman_query"]
GATE_FILE = os.path.join(config.MODEL_DIR, "gate.pkl")


def gate_features(engine, query, sparse_ranked):
    """Compute the gate's input features from the query and the sparse results."""
    scores = []
    for _, score in sparse_ranked:
        scores.append(score)
    top = scores[0] if len(scores) > 0 else 0.0
    tenth = scores[9] if len(scores) >= 10 else 0.0
    all_zone = engine.index.zones["all"]
    dhvani_zone = engine.index.zones["dhvani"]
    content = [r for r in query["records"] if not r["stop"]]
    dhvani_only = 0
    unmatched = 0
    max_idf = 0.0
    for record in content:
        surface_df = all_zone.get_df(record["stem"])
        key_df = dhvani_zone.get_df(record["dhvani"]) if record["dhvani"] != "" else 0
        if surface_df == 0 and key_df > 0:
            dhvani_only += 1
        if surface_df == 0 and key_df == 0:
            unmatched += 1
        best_df = surface_df if surface_df > 0 else key_df
        if best_df > 0:
            max_idf = max(max_idf, bm25_idf(best_df, engine.num_docs))
    n = max(len(content), 1)
    return {
        "top_score": top,
        "score_gap": (top - tenth) / top if top > 0 else 0.0,
        "nqc": float(np.std(scores)) / top if top > 0 else 0.0,
        "dhvani_only": dhvani_only / float(n),
        "unmatched": unmatched / float(n),
        "max_idf": max_idf,
        "query_length": float(len(content)),
        "roman_query": 1.0 if query["script"] in ["roman", "mixed"] else 0.0,
    }


def feature_vector(features):
    row = []
    for name in GATE_FEATURES:
        row.append(features[name])
    return row


class Gate:
    def __init__(self, scaler, classifier, threshold):
        self.scaler = scaler
        self.classifier = classifier
        self.threshold = threshold

    def probability(self, features):
        x = self.scaler.transform(np.array([feature_vector(features)]))
        return float(self.classifier.predict_proba(x)[0, 1])

    def probabilities(self, rows):
        return self.classifier.predict_proba(self.scaler.transform(np.array(rows)))[:, 1]

    def decide(self, features):
        return self.probability(features) >= self.threshold


def save_gate(gate):
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    with open(GATE_FILE, "wb") as f:
        pickle.dump(gate, f)


def load_gate():
    if not os.path.exists(GATE_FILE):
        return None
    with open(GATE_FILE, "rb") as f:
        return pickle.load(f)
