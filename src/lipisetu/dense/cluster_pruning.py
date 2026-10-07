"""Cluster pruning for fast approximate dense search (Lecture: Scoring - cluster pruning).

Index time:
    pick sqrt(N) random documents as LEADERS;
    attach every other document (a FOLLOWER) to its nearest leader.
Query time:
    compare the query with the leaders only (sqrt(N) dot products),
    then score only the followers of the best b leaders.
So instead of N dot products I do about sqrt(N) + b * sqrt(N).
The price: a relevant document attached to a different leader can be missed.
"""
import math

import numpy as np


class ClusterPruning:
    def __init__(self, vectors, seed=13):
        num_docs = len(vectors)
        num_leaders = int(math.sqrt(num_docs))
        rng = np.random.RandomState(seed)
        self.leaders = rng.choice(num_docs, num_leaders, replace=False)
        self.leader_vectors = vectors[self.leaders].astype(np.float32)
        # Attach every document to its nearest leader (in chunks to save memory)
        assignment = np.zeros(num_docs, dtype=np.int32)
        for start in range(0, num_docs, 20000):
            block = vectors[start:start + 20000].astype(np.float32)
            similarities = block @ self.leader_vectors.T
            assignment[start:start + 20000] = np.argmax(similarities, axis=1)
        # followers[l] = all documents attached to leader l
        self.followers = []
        order = np.argsort(assignment, kind="stable")
        counts = np.bincount(assignment, minlength=num_leaders)
        start = 0
        for leader in range(num_leaders):
            self.followers.append(order[start:start + counts[leader]])
            start += counts[leader]

    def search(self, query_vector, vectors, k=100, num_clusters=8):
        """Score only the followers of the `num_clusters` nearest leaders."""
        leader_scores = self.leader_vectors @ query_vector
        best_leaders = np.argsort(-leader_scores)[:num_clusters]
        candidates = np.concatenate([self.followers[l] for l in best_leaders])
        scores = vectors[candidates].astype(np.float32) @ query_vector
        keep = min(k, len(candidates))
        top = np.argsort(-scores)[:keep]
        results = []
        for i in top:
            results.append((int(candidates[i]), float(scores[i])))
        return results, len(candidates)
