"""E11: Efficiency structures - what they save and what they cost.

1. Heap top-K vs sorting all scores
2. Champion lists (r = 200) vs full postings, on S1
3. Skip pointers vs plain merge, for AND queries made from the dev queries
4. Cluster pruning vs exact dense search (needs the dense vectors)
Outputs: results/e11_efficiency.csv
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np

from lipisetu import config
from lipisetu.search import SearchEngine
from lipisetu.query import parse_query
from lipisetu.retrieval.topk import top_k
from lipisetu.retrieval.boolean import intersect, intersect_with_skips
from lipisetu.eval.run_eval import load_forms, load_qrels, per_query_metrics, average_metrics, write_rows
from lipisetu.eval.metrics import mean, ndcg_at_k
from lipisetu.data import relevant_docs

FORMS = ["F1", "F2", "F3"]


def time_it(function, repeat=1):
    start = time.perf_counter()
    for _ in range(repeat):
        result = function()
    return result, (time.perf_counter() - start) * 1000.0 / repeat


def heap_vs_sort(engine, queries):
    heap_times = []
    sort_times = []
    for qid in list(queries.keys())[:100]:
        query = parse_query(queries[qid])
        by_zone = engine.zone_scores(query, "S1")
        total = by_zone["all"] + by_zone["dhvani"]
        _, t1 = time_it(lambda: top_k(total, 100), 3)
        _, t2 = time_it(lambda: np.argsort(-total)[:100], 3)
        heap_times.append(t1)
        sort_times.append(t2)
    return [{"experiment": "top-K selection", "variant": "heap over scored docs (mine)",
             "median_ms": round(float(np.median(heap_times)), 3)},
            {"experiment": "top-K selection", "variant": "full sort of all N scores",
             "median_ms": round(float(np.median(sort_times)), 3)}]


def champions(engine, forms_dict, qrels):
    rows = []
    for use_champions in [False, True]:
        ndcgs = []
        times = []
        for form in forms_dict:
            runs = {}
            for qid in forms_dict[form]:
                query = parse_query(forms_dict[form][qid])
                ranked, took = time_it(lambda: engine.sparse_search(query, "S1", 100, use_champions))
                times.append(took)
                runs[qid] = [engine.index.doc_ids[doc] for doc, _ in ranked]
            ndcgs.append(average_metrics(per_query_metrics(runs, qrels))["ndcg@10"])
        rows.append({"experiment": "champion lists (S1, r=200)",
                     "variant": "champion lists" if use_champions else "full postings",
                     "median_ms": round(float(np.median(times)), 3), "ndcg@10": round(mean(ndcgs), 4)})
    return rows


def skip_pointers(engine, queries):
    zone = engine.index.zones["all"]
    plain_counts = []
    skip_counts = []
    for qid in queries:
        terms = sorted(set(parse_query(queries[qid])["surface_terms"]))
        lists = []
        for term in terms:
            docs = zone.postings(term)[0].tolist()
            if len(docs) > 0:
                lists.append(docs)
        if len(lists) < 2:
            continue
        lists.sort(key=len)
        for other in lists[1:]:
            c1 = [0]
            c2 = [0]
            a = intersect(lists[0], other, c1)
            b = intersect_with_skips(lists[0], other, c2)
            assert a == b
            plain_counts.append(c1[0])
            skip_counts.append(c2[0])
    return [{"experiment": "AND merge (pairs of dev query terms)", "variant": "plain merge",
             "comparisons": int(np.mean(plain_counts))},
            {"experiment": "AND merge (pairs of dev query terms)", "variant": "skip pointers (sqrt L)",
             "comparisons": int(np.mean(skip_counts))}]


def cluster_pruning(engine, forms_dict, qrels):
    if "D0" not in engine.dense:
        return []
    from lipisetu.dense.retriever import cluster_index
    dense = engine.dense["D0"]
    index = cluster_index()
    rows = []
    exact_ndcg = []
    pruned_ndcg = []
    overlaps = []
    exact_times = []
    pruned_times = []
    scored = []
    for form in forms_dict:
        for qid in forms_dict[form]:
            relevant = relevant_docs(qrels, qid)
            if len(relevant) == 0:
                continue
            vector = dense.encoder.encode_query(forms_dict[form][qid])
            exact, t1 = time_it(lambda: dense.search_vector(vector, 100), 3)
            (pruned, count), t2 = time_it(lambda: index.search(vector, dense.vectors, 100), 3)
            exact_ids = [engine.index.doc_ids[d] for d, _ in exact]
            pruned_ids = [engine.index.doc_ids[d] for d, _ in pruned]
            exact_ndcg.append(ndcg_at_k(exact_ids, relevant))
            pruned_ndcg.append(ndcg_at_k(pruned_ids, relevant))
            overlaps.append(len(set(exact_ids) & set(pruned_ids)) / 100.0)
            exact_times.append(t1)
            pruned_times.append(t2)
            scored.append(count)
    rows.append({"experiment": "dense search (D0)", "variant": "exact (all N vectors)",
                 "median_ms": round(float(np.median(exact_times)), 3), "ndcg@10": round(mean(exact_ndcg), 4),
                 "docs_scored": engine.num_docs})
    rows.append({"experiment": "dense search (D0)", "variant": "cluster pruning (sqrt N leaders, 8 clusters)",
                 "median_ms": round(float(np.median(pruned_times)), 3), "ndcg@10": round(mean(pruned_ndcg), 4),
                 "docs_scored": int(np.mean(scored)), "overlap@100_with_exact": round(mean(overlaps), 4)})
    return rows


def main():
    engine = SearchEngine()
    qrels = load_qrels("dev")
    forms_dict = load_forms("dev", FORMS)
    rows = []
    rows += heap_vs_sort(engine, forms_dict["F1"])
    rows += champions(engine, forms_dict, qrels)
    rows += skip_pointers(engine, forms_dict["F1"])
    rows += cluster_pruning(engine, forms_dict, qrels)
    for row in rows:
        print(row)
    write_rows(os.path.join(config.RESULTS_DIR, "e11_efficiency.csv"), rows,
               ["experiment", "variant", "median_ms", "ndcg@10", "comparisons", "docs_scored",
                "overlap@100_with_exact"])


if __name__ == "__main__":
    main()
