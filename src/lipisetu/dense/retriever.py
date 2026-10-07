"""Dense retrievers D0 (base e5-small) and D1 (my script-consistency student).

Both use the SAME passage vectors (made once by scripts/encode_corpus.py).
Only the query encoder is different: D1's encoder was trained so that a
Roman-script query lands where its Devanagari version lands.
"""
import os

import numpy as np

from lipisetu import config
from lipisetu.dense.encoder import OnnxEncoder
from lipisetu.dense.cluster_pruning import ClusterPruning

_passage_vectors = None
_cluster_index = None


def passage_vectors():
    """Load the passage vectors once and share them between D0 and D1."""
    global _passage_vectors
    if _passage_vectors is None:
        path = os.path.join(config.INDEX_DIR, "dense", "passages.npy")
        if not os.path.exists(path):
            return None
        _passage_vectors = np.load(path).astype(np.float32)
    return _passage_vectors


def cluster_index():
    global _cluster_index
    if _cluster_index is None and passage_vectors() is not None:
        _cluster_index = ClusterPruning(passage_vectors(), seed=config.SEED)
    return _cluster_index


class DenseRetriever:
    def __init__(self, name, encoder):
        self.name = name
        self.encoder = encoder
        self.vectors = passage_vectors()

    def search(self, text, k=100, use_cluster_pruning=False):
        """Return [(doc number, cosine score)] best first."""
        query_vector = self.encoder.encode_query(text)
        return self.search_vector(query_vector, k, use_cluster_pruning)

    def search_vector(self, query_vector, k=100, use_cluster_pruning=False):
        if use_cluster_pruning:
            results, _ = cluster_index().search(query_vector, self.vectors, k)
            return results
        scores = self.vectors @ query_vector
        # argpartition finds the k best without sorting all N scores
        top = np.argpartition(-scores, k)[:k]
        top = top[np.argsort(-scores[top])]
        results = []
        for doc in top:
            results.append((int(doc), float(scores[doc])))
        return results


def model_paths(name):
    """Where the query encoder for each system lives."""
    if name == "D0":
        folder = os.path.join(config.MODEL_DIR, "e5-small-onnx")
        return os.path.join(folder, "model_int8.onnx"), folder, None
    if name == "D1":
        folder = os.path.join(config.MODEL_DIR, "scd-student-onnx")
        return os.path.join(folder, "model_pruned_int8.onnx"), folder, os.path.join(folder, "id_map.npy")
    if name == "D1-unpruned":
        folder = os.path.join(config.MODEL_DIR, "scd-student-onnx")
        return os.path.join(folder, "model_int8.onnx"), folder, None
    return None, None, None


def load_dense_retriever(name):
    """Load D0 or D1 if its files exist, else return None."""
    onnx_path, folder, id_map_path = model_paths(name)
    if onnx_path is None or not os.path.exists(onnx_path) or passage_vectors() is None:
        return None
    id_map = None
    if id_map_path is not None and os.path.exists(id_map_path):
        id_map = np.load(id_map_path)
    encoder = OnnxEncoder(onnx_path, folder, id_map=id_map)
    return DenseRetriever(name, encoder)
