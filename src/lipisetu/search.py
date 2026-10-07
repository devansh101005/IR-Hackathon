"""The search engine: puts all the pieces together (Lecture: a complete search system).

Systems (see docs/EVALUATION.md):
    B0  BM25 on raw whitespace tokens (no normalisation)        naive baseline
    B1  BM25 + normalisation + stop words + stemming             classic baseline
    B1N B1 without stemming                                      stemming experiment
    B2  B1 + Roman->Devanagari transliteration of the query      the "obvious" baseline
    V1  tf-idf lnc.ltc cosine                                    vector space model
    S0  B1 + classic Soundex zone                                comparison for Dhvani
    S1  B1 + Dhvani zone                                         mine
    S2  S1 + pooled df                                           mine
    S3  S2 + title zone + proximity                              mine (best sparse)
    D0  dense e5-small (int8 ONNX)                               neural reference
    D1  SCD student query encoder                                mine
    H1  RRF(S3, D1)                                              hybrid
    L1  learning-to-rank over S3 + D1 features                   mine
    G1  gated cascade: S3, and H1 only when the gate says so     mine
"""
import json
import os
import time

import numpy as np

from lipisetu import config
from lipisetu.index.build import load_index, load_docstore
from lipisetu.query import parse_query, transliterated_surface_terms
from lipisetu.retrieval.bm25 import bm25_zone, pooled_df_table
from lipisetu.retrieval.tfidf import tfidf_cosine
from lipisetu.retrieval.topk import top_k
from lipisetu.retrieval.proximity import proximity_score
from lipisetu.retrieval.rrf import rrf

SPARSE_SYSTEMS = ["B0", "B1", "B1N", "B2", "V1", "S0", "S1", "S2", "S3"]
NEURAL_SYSTEMS = ["D0", "D1", "H1", "L1", "G1"]

DEFAULT_PARAMS = {
    "k1": config.BM25_K1,
    "b": config.BM25_B,
    "w_dhvani": 0.3,
    "w_soundex": 0.3,
    "w_title": 0.5,
    "lambda_prox": 1.0,
}

PARAMS_FILE = os.path.join(config.RESULTS_DIR, "tuned_params.json")


def load_params():
    """Use the parameters tuned on the train split if they exist."""
    params = dict(DEFAULT_PARAMS)
    if os.path.exists(PARAMS_FILE):
        with open(PARAMS_FILE, encoding="utf-8") as f:
            params.update(json.load(f))
    return params


class SearchEngine:
    def __init__(self, index_folder=None, load_neural=True):
        if index_folder is None:
            index_folder = os.path.join(config.INDEX_DIR, "main")
        print("loading index from", index_folder)
        self.index = load_index(index_folder)
        self.titles, self.texts = load_docstore(index_folder)
        self.params = load_params()
        self.num_docs = self.index.num_docs
        self.dense = {}       # name -> DenseRetriever (D0, D1)
        self.ltr = None
        self.gate = None
        if load_neural:
            self.load_neural_parts()

    # ---------------- optional neural parts ----------------
    def load_neural_parts(self):
        """Load the dense retrievers, the learning-to-rank model and the gate if they were built."""
        try:
            from lipisetu.dense.retriever import load_dense_retriever
            for name in ["D0", "D1"]:
                retriever = load_dense_retriever(name)
                if retriever is not None:
                    self.dense[name] = retriever
        except ImportError as error:
            print("dense retrieval not available:", error)
        try:
            from lipisetu.rerank.ltr import load_ltr
            self.ltr = load_ltr()
        except ImportError as error:
            print("learning-to-rank not available:", error)
        try:
            from lipisetu.cascade.gate import load_gate
            self.gate = load_gate()
        except ImportError as error:
            print("gate not available:", error)

    # ---------------- sparse scoring ----------------
    def run_bm25(self, zone_name, terms, weight, result, details, use_champions, df_override=None):
        """BM25 for one zone; stores the weighted score array in result[zone_name]."""
        champions = None
        if use_champions and zone_name in self.index.champions:
            champions = self.index.champions[zone_name]
        scores = np.zeros(self.num_docs, dtype=np.float64)
        info = []
        bm25_zone(self.index.zones[zone_name], terms, scores, weight, self.params["k1"], self.params["b"],
                  df_override=df_override, champions=champions, details=info)
        result[zone_name] = scores
        if details is not None:
            details[zone_name] = info

    def zone_scores(self, query, system, use_champions=False, details=None):
        """Return {zone name: weighted score array} for a sparse system."""
        p = self.params
        zones = self.index.zones
        result = {}
        if system == "B0":
            self.run_bm25("raw", query["text"].split(), 1.0, result, details, use_champions)
        elif system == "B1N":
            self.run_bm25("nostem", query["nostem_terms"], 1.0, result, details, use_champions)
        elif system == "V1":
            info = []
            result["all"] = tfidf_cosine(zones["all"], query["surface_terms"], details=info)
            if details is not None:
                details["all"] = info
        else:
            surface = query["surface_terms"]
            if system == "B2":
                surface = transliterated_surface_terms(query)
            df_override = None
            if system in ["S2", "S3"]:
                df_override = pooled_df_table(surface, query["term_keys"], zones["dhvani"], zones["all"])
                if details is not None:
                    details["pooled_df"] = df_override
            self.run_bm25("all", surface, 1.0, result, details, use_champions, df_override)
            if system == "S0":
                self.run_bm25("soundex", query["soundex_codes"], p["w_soundex"], result, details, use_champions)
            if system in ["S1", "S2", "S3"]:
                self.run_bm25("dhvani", query["dhvani_keys"], p["w_dhvani"], result, details, use_champions)
            if system == "S3":
                self.run_bm25("title", surface, p["w_title"], result, details, use_champions, df_override)
        return result

    def sparse_search(self, query, system, k=100, use_champions=False, details=None):
        """Rank with a sparse system. Returns [(doc number, score)] best first."""
        by_zone = self.zone_scores(query, system, use_champions, details)
        total = np.zeros(self.num_docs, dtype=np.float64)
        for name in by_zone:
            total += by_zone[name]
        ranked = top_k(total, k)
        if system == "S3":
            ranked = self.add_proximity(query, ranked, details)
        if details is not None:
            details["zone_scores"] = by_zone
        return ranked

    def add_proximity(self, query, ranked, details=None):
        """Re-rank the top documents: score + lambda * proximity."""
        lam = self.params["lambda_prox"]
        new_ranked = []
        windows = {}
        for doc, score in ranked:
            prox, window = proximity_score(self.index.zones["dhvani"], query["dhvani_keys"], doc)
            new_ranked.append((doc, score + lam * prox))
            windows[doc] = (round(prox, 3), window)
        new_ranked.sort(key=lambda item: item[1], reverse=True)
        if details is not None:
            details["proximity"] = windows
        return new_ranked

    # ---------------- full search ----------------
    def search(self, text, system="S3", k=100, use_champions=False, details=None):
        """Search with any system. Returns [(doc number, score)] best first."""
        query = parse_query(text)
        if details is not None:
            details["query"] = query
        if system in SPARSE_SYSTEMS:
            return self.sparse_search(query, system, k, use_champions, details)
        if system in ["D0", "D1"]:
            return self.dense[system].search(text, k)
        if system == "H1":
            return self.hybrid_search(query, k, details)
        if system == "L1":
            return self.ltr_search(query, k, details)
        if system == "G1":
            return self.gated_search(query, k, details)
        raise ValueError("unknown system " + system)

    def hybrid_search(self, query, k=100, details=None):
        sparse = self.sparse_search(query, "S3", 100, details=details)
        dense = self.dense["D1"].search(query["text"], 100)
        sparse_docs = [doc for doc, _ in sparse]
        dense_docs = [doc for doc, _ in dense]
        if details is not None:
            details["dense_top"] = dense[:10]
        return rrf([sparse_docs, dense_docs], k=config.RRF_K, top=k)

    def ltr_search(self, query, k=100, details=None):
        from lipisetu.rerank.ltr import rerank
        return rerank(self, query, k, details)

    def gated_search(self, query, k=100, details=None):
        """Cascade: run the cheap sparse system, ask the gate, run neural only if needed."""
        from lipisetu.cascade.gate import gate_features
        sparse = self.sparse_search(query, "S3", 100, details=details)
        features = gate_features(self, query, sparse)
        use_neural = self.gate.decide(features)
        if details is not None:
            details["gate"] = {"features": features, "use_neural": use_neural,
                               "probability": self.gate.probability(features),
                               "threshold": self.gate.threshold}
        if not use_neural:
            return sparse[:k]
        return self.hybrid_search(query, k, None)

    # ---------------- helpers for display ----------------
    def doc_info(self, doc_number, snippet_length=220):
        text = self.texts[doc_number]
        snippet = text if len(text) <= snippet_length else text[:snippet_length] + "…"
        return {
            "doc_number": int(doc_number),
            "docid": self.index.doc_ids[doc_number],
            "title": self.titles[doc_number],
            "snippet": snippet,
        }

    def timed_search(self, text, system, k=100):
        start = time.perf_counter()
        ranked = self.search(text, system, k)
        return ranked, (time.perf_counter() - start) * 1000.0
