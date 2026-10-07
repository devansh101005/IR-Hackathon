"""Reciprocal Rank Fusion (Cormack, Clarke and Büttcher, SIGIR 2009).

Combines several ranked lists without having to compare their scores:
    RRF(d) = sum over lists of 1 / (k + rank of d in that list),   k = 60
"""


def rrf(ranked_lists, k=60, top=100):
    """ranked_lists: list of lists of doc numbers (best first). Returns [(doc, score)]."""
    fused = {}
    for ranking in ranked_lists:
        for rank in range(len(ranking)):
            doc = ranking[rank]
            fused[doc] = fused.get(doc, 0.0) + 1.0 / (k + rank + 1)
    items = list(fused.items())
    items.sort(key=lambda item: item[1], reverse=True)
    return items[:top]
