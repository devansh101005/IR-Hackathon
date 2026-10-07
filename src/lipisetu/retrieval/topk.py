"""Heap-based top-K selection and champion lists (Lecture: Scoring and result assembly)."""
import heapq

import numpy as np


def top_k(scores, k):
    """Return the k best (doc number, score) pairs, best first.

    Sorting all N documents costs O(N log N). A heap of size k only costs
    O(N log k), and I only look at documents that got a score at all.
    """
    candidates = np.nonzero(scores)[0]
    heap = []
    for doc_number in candidates:
        score = float(scores[doc_number])
        if len(heap) < k:
            heapq.heappush(heap, (score, -int(doc_number)))
        elif score > heap[0][0]:
            heapq.heapreplace(heap, (score, -int(doc_number)))
    # The heap keeps the smallest on top, so sort the k winners at the end
    heap.sort(reverse=True)
    results = []
    for score, negative_doc in heap:
        results.append((-negative_doc, score))
    return results


class ChampionLists:
    """For each term, only the r documents with the highest tf (precomputed at index time).

    At query time I score only these "champions", which is much faster for
    common terms. The cost: some relevant documents can be missed.
    """

    def __init__(self, zone, r):
        self.r = r
        self.term_ids = zone.term_ids
        term_start = [0]
        doc_list = []
        tf_list = []
        for term_id in range(len(zone.terms)):
            start = zone.term_start[term_id]
            end = zone.term_start[term_id + 1]
            docs = zone.doc_array[start:end]
            tfs = zone.tf_array[start:end]
            if len(docs) > r:
                # indices of the r largest tf values, then put back in doc order
                best = np.argsort(-tfs, kind="stable")[:r]
                best = np.sort(best)
                docs = docs[best]
                tfs = tfs[best]
            doc_list.append(docs)
            tf_list.append(tfs)
            term_start.append(term_start[-1] + len(docs))
        self.term_start = np.array(term_start, dtype=np.int64)
        self.doc_array = np.concatenate(doc_list).astype(np.int32)
        self.tf_array = np.concatenate(tf_list).astype(np.int32)

    def postings(self, term):
        if term not in self.term_ids:
            empty = np.zeros(0, dtype=np.int32)
            return empty, empty
        term_id = self.term_ids[term]
        start = self.term_start[term_id]
        end = self.term_start[term_id + 1]
        return self.doc_array[start:end], self.tf_array[start:end]
