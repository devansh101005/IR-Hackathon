"""tf-idf weighting and cosine similarity with SMART lnc.ltc (Lecture: tf-idf and the vector space model).

Document side "lnc":  l = 1 + log(tf),  n = no idf,  c = cosine (length) normalisation
Query side    "ltc":  l = 1 + log(tf),  t = idf = log10(N / df),  c = cosine normalisation
score(q, d) = sum over shared terms of  w(t, q) * w(t, d)   (= cosine of the two vectors)

Scoring is done "term at a time" with one accumulator slot per document
(Lecture: efficient cosine scoring).
"""
import math

import numpy as np

from lipisetu.retrieval.bm25 import count_terms


def ltc_query_weights(zone, query_terms):
    """Return {term: normalised ltc weight} for the query."""
    counts = count_terms(query_terms)
    weights = {}
    for term in counts:
        idf = zone.idf(term)
        if idf == 0.0:
            continue
        weights[term] = (1.0 + math.log10(counts[term])) * idf
    length = math.sqrt(sum(w * w for w in weights.values()))
    if length > 0:
        for term in weights:
            weights[term] = weights[term] / length
    return weights


def tfidf_cosine(zone, query_terms, details=None):
    """Return an array of cosine scores (one per document) for the zone."""
    scores = np.zeros(zone.num_docs, dtype=np.float64)
    query_weights = ltc_query_weights(zone, query_terms)
    for term in query_weights:
        docs, tfs = zone.postings(term)
        doc_weights = (1.0 + np.log10(tfs.astype(np.float64))) / zone.lnc_norms[docs]
        scores[docs] += query_weights[term] * doc_weights
        if details is not None:
            details.append({"term": term, "query_weight": round(query_weights[term], 3),
                            "df": zone.get_df(term)})
    return scores
