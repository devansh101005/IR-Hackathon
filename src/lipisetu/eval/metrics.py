"""Evaluation metrics (Lecture: precision and recall; plus nDCG, MRR and my script-invariance metrics).

All functions take a ranked list of doc ids (best first) and a set of relevant doc ids.
Formulas are in docs/EVALUATION.md.
"""
import math


def precision_at_k(ranking, relevant, k):
    hits = 0
    for doc in ranking[:k]:
        if doc in relevant:
            hits += 1
    return hits / float(k)


def recall_at_k(ranking, relevant, k):
    if len(relevant) == 0:
        return 0.0
    hits = 0
    for doc in ranking[:k]:
        if doc in relevant:
            hits += 1
    return hits / float(len(relevant))


def mrr_at_k(ranking, relevant, k=10):
    for rank in range(min(k, len(ranking))):
        if ranking[rank] in relevant:
            return 1.0 / (rank + 1)
    return 0.0


def ndcg_at_k(ranking, relevant, k=10):
    """Binary-relevance nDCG: DCG = sum rel_i / log2(i + 1)."""
    dcg = 0.0
    for i in range(min(k, len(ranking))):
        if ranking[i] in relevant:
            dcg += 1.0 / math.log2(i + 2)
    ideal = 0.0
    for i in range(min(k, len(relevant))):
        ideal += 1.0 / math.log2(i + 2)
    if ideal == 0.0:
        return 0.0
    return dcg / ideal


def rbo(list1, list2, p=0.9, k=10):
    """Rank-Biased Overlap, extrapolated form (Webber, Moffat and Zobel 2010).

    How similar two rankings are, with more weight on the top ranks.
    1.0 = identical top-k lists, 0.0 = nothing in common.
    """
    list1 = list1[:k]
    list2 = list2[:k]
    depth = min(len(list1), len(list2))
    if depth == 0:
        return 0.0
    seen1 = set()
    seen2 = set()
    overlap = 0
    total = 0.0
    for d in range(1, depth + 1):
        a = list1[d - 1]
        b = list2[d - 1]
        if a == b:
            overlap += 1
        else:
            if a in seen2:
                overlap += 1
            if b in seen1:
                overlap += 1
        seen1.add(a)
        seen2.add(b)
        total += (overlap / float(d)) * (p ** d)
    return (overlap / float(depth)) * (p ** depth) + ((1.0 - p) / p) * total


def all_metrics(ranking, relevant):
    """The standard metrics for one query, as a dict."""
    return {
        "ndcg@10": ndcg_at_k(ranking, relevant, 10),
        "p@5": precision_at_k(ranking, relevant, 5),
        "p@10": precision_at_k(ranking, relevant, 10),
        "recall@100": recall_at_k(ranking, relevant, 100),
        "mrr@10": mrr_at_k(ranking, relevant, 10),
    }


def cross_script_consistency(rankings_by_form, k=10, p=0.9):
    """CSC@k for one query: average pairwise RBO between the rankings of its forms."""
    forms = list(rankings_by_form.keys())
    values = []
    for i in range(len(forms)):
        for j in range(i + 1, len(forms)):
            values.append(rbo(rankings_by_form[forms[i]], rankings_by_form[forms[j]], p, k))
    if len(values) == 0:
        return 1.0
    return sum(values) / len(values)


def mean(values):
    if len(values) == 0:
        return 0.0
    return sum(values) / float(len(values))
