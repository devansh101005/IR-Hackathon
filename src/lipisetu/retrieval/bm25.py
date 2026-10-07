"""BM25 scoring with zones and pooled document frequency.

(Lecture: Scoring and result assembly - zone index; beyond the syllabus: BM25)

For one zone:
    score(d) = sum over query terms t of
               idf(t) * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(d) / avg_len))
    idf(t)   = log(1 + (N - df + 0.5) / (df + 0.5))      (always positive)

Zones are combined with weights:  final(d) = sum over zones of weight_zone * score_zone(d)

Pooled df (Pirkola, SIGIR 1998, applied to spelling variants):
    In a corpus that mixes scripts, "मौसम" and "mausam" are the same word, but
    each spelling has its own df. Each spelling then looks rarer than the word
    really is, so its idf is too high. With pooled_df=True, a surface term
    uses the df of its Dhvani class (all documents that contain ANY spelling
    of that sound), which is the df of the word itself.
"""
import math

import numpy as np


def bm25_idf(df, num_docs):
    return math.log(1.0 + (num_docs - df + 0.5) / (df + 0.5))


def count_terms(terms):
    """Turn a list of query terms into {term: how many times it appears}."""
    counts = {}
    for term in terms:
        counts[term] = counts.get(term, 0) + 1
    return counts


def bm25_zone(zone, query_terms, scores, weight, k1, b, df_override=None, champions=None, details=None):
    """Add weight * BM25(zone) to the `scores` array (one slot per document).

    df_override: optional dict term -> df to use instead of the zone's own df (pooled df)
    champions:   optional ChampionLists; if given, only champion postings are scored
    details:     optional list; I append (term, df, idf) here for --explain
    """
    counts = count_terms(query_terms)
    for term in counts:
        if champions is not None:
            docs, tfs = champions.postings(term)
        else:
            docs, tfs = zone.postings(term)
        if len(docs) == 0:
            if details is not None:
                details.append({"term": term, "df": 0, "idf": 0.0})
            continue
        df = zone.get_df(term)
        if df_override is not None and term in df_override:
            df = df_override[term]
        idf = bm25_idf(df, zone.num_docs)
        doc_lengths = zone.doc_lengths[docs]
        tfs = tfs.astype(np.float64)
        tf_part = tfs * (k1 + 1.0) / (tfs + k1 * (1.0 - b + b * doc_lengths / zone.avg_length))
        scores[docs] += weight * counts[term] * idf * tf_part
        if details is not None:
            details.append({"term": term, "df": int(df), "idf": round(idf, 3)})
    return scores


def pooled_df_table(surface_terms, term_keys, dhvani_zone, surface_zone):
    """For each surface query term, the df of its Dhvani class (Pirkola-style pooling).

    term_keys: dict surface term -> Dhvani key of the token it came from.
    The pooled df is never smaller than the term's own df.
    """
    table = {}
    for term in surface_terms:
        key = term_keys.get(term, "")
        own_df = surface_zone.get_df(term)
        if key != "" and dhvani_zone.has_term(key):
            table[term] = max(own_df, dhvani_zone.get_df(key))
        else:
            table[term] = own_df
    return table
