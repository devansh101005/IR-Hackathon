"""Learning-to-rank over IR features (beyond the syllabus: learning to rank; Liu 2009).

Instead of guessing how much each signal should count, I learn it from the
TRAIN relevance judgments. For each query I take the candidates from the
sparse system (S3) and the dense system (D1) and describe every candidate
passage with a few features:

    bm25_all     surface BM25 (pooled df)          bm25_dhvani  Dhvani-zone BM25
    bm25_title   title-zone BM25                    proximity    smallest-window score
    tfidf        lnc.ltc cosine                     dense        cosine with the query vector
    sparse_rr    1 / rank in S3                     dense_rr     1 / rank in D1
    lead_passage static quality g(d): 1 if it is the first passage of its article
    log_length   log of the passage length          roman_query  1 if the query has Roman words

A logistic regression (pointwise LTR) predicts P(relevant | features), and the
candidates are sorted by that probability. The learned weights also show
which signals matter, which goes in the report.
"""
import math
import os
import pickle

import numpy as np

from lipisetu import config
from lipisetu.retrieval.tfidf import tfidf_cosine
from lipisetu.retrieval.proximity import proximity_score

FEATURE_NAMES = ["bm25_all", "bm25_dhvani", "bm25_title", "proximity", "tfidf", "dense",
                 "sparse_rr", "dense_rr", "lead_passage", "log_length", "roman_query"]
MODEL_FILE = os.path.join(config.MODEL_DIR, "ltr.pkl")


def candidate_features(engine, query, sparse_k=100, dense_k=100):
    """Return (candidate doc numbers, feature matrix) for one query."""
    by_zone = engine.zone_scores(query, "S3")
    sparse_ranked = engine.sparse_search(query, "S3", sparse_k)
    dense = engine.dense["D1"]
    query_vector = dense.encoder.encode_query(query["text"])
    dense_ranked = dense.search_vector(query_vector, dense_k)

    sparse_rank = {}
    for rank in range(len(sparse_ranked)):
        sparse_rank[sparse_ranked[rank][0]] = rank + 1
    dense_rank = {}
    for rank in range(len(dense_ranked)):
        dense_rank[dense_ranked[rank][0]] = rank + 1
    candidates = sorted(set(sparse_rank.keys()) | set(dense_rank.keys()))

    tfidf_scores = tfidf_cosine(engine.index.zones["all"], query["surface_terms"])
    dense_scores = dense.vectors[candidates] @ query_vector
    lengths = engine.index.zones["all"].doc_lengths
    is_roman = 1.0 if query["script"] in ["roman", "mixed"] else 0.0
    dhvani_zone = engine.index.zones["dhvani"]

    rows = []
    for i in range(len(candidates)):
        doc = candidates[i]
        prox, _ = proximity_score(dhvani_zone, query["dhvani_keys"], doc)
        lead = 1.0 if engine.index.doc_ids[doc].endswith("#0") else 0.0
        rows.append([
            by_zone["all"][doc], by_zone["dhvani"][doc], by_zone["title"][doc], prox,
            tfidf_scores[doc], float(dense_scores[i]),
            1.0 / sparse_rank[doc] if doc in sparse_rank else 0.0,
            1.0 / dense_rank[doc] if doc in dense_rank else 0.0,
            lead, math.log(1 + lengths[doc]), is_roman,
        ])
    return candidates, np.array(rows, dtype=np.float64)


class LTRModel:
    def __init__(self, scaler, classifier):
        self.scaler = scaler
        self.classifier = classifier

    def predict(self, features):
        return self.classifier.predict_proba(self.scaler.transform(features))[:, 1]

    def weights(self):
        """Learned weight per feature (on standardised features)."""
        result = {}
        for i in range(len(FEATURE_NAMES)):
            result[FEATURE_NAMES[i]] = float(self.classifier.coef_[0][i])
        return result


def save_ltr(model):
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model, f)


def load_ltr():
    if not os.path.exists(MODEL_FILE):
        return None
    with open(MODEL_FILE, "rb") as f:
        return pickle.load(f)


def rerank(engine, query, k=100, details=None):
    """Score all candidates with the LTR model and sort them."""
    candidates, features = candidate_features(engine, query)
    probabilities = engine.ltr.predict(features)
    order = np.argsort(-probabilities)
    results = []
    for i in order[:k]:
        results.append((candidates[i], float(probabilities[i])))
    if details is not None:
        details["ltr_weights"] = engine.ltr.weights()
    return results
