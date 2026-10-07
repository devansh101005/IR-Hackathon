"""E13: Why does tf-idf (lnc.ltc) score lower than BM25? Length bias.

Full cosine length normalisation favours very short passages. I compare the
length of the top-1 passage chosen by V1 (lnc.ltc) and by B1 (BM25) for every
dev query in Devanagari.
Output: results/e13_length_bias.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np

from lipisetu import config
from lipisetu.search import SearchEngine
from lipisetu.eval.run_eval import load_forms


def main():
    engine = SearchEngine(load_neural=False)
    queries = load_forms("dev", ["F1"])["F1"]
    lengths = engine.index.zones["all"].doc_lengths
    result = {"corpus_median_length": float(np.median(lengths))}
    for system in ["V1", "B1"]:
        top_lengths = []
        for qid in queries:
            ranked = engine.search(queries[qid], system, 1)
            if len(ranked) > 0:
                top_lengths.append(int(lengths[ranked[0][0]]))
        result[system + "_median_top1_length"] = float(np.median(top_lengths))
    with open(os.path.join(config.RESULTS_DIR, "e13_length_bias.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(result)


if __name__ == "__main__":
    main()
