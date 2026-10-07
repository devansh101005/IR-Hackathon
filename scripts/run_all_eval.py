"""Run every system on every query form of the DEV split and write the result tables.

Usage: python scripts/run_all_eval.py [--systems B1,S3,...]
Outputs (committed):
    results/main_metrics.csv     system, query_form, metric, value, n_queries
    results/invariance.csv       Script Gap, CSC@10, worst-script nDCG@10 per system
    results/efficiency.csv       median / p95 latency per system
    results/human_*.csv          the same on the human query set, if the sheets are filled
Outputs (not committed, used by significance.py):
    data/eval/per_query.csv, data/eval/runs/<system>_<form>.json
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np

from lipisetu import config
from lipisetu.search import SearchEngine, SPARSE_SYSTEMS
from lipisetu.human import load_human_forms
from lipisetu.eval.run_eval import (load_forms, load_qrels, per_query_metrics, average_metrics,
                                    invariance_metrics, write_rows, METRIC_NAMES)

DEV_FORMS = ["F1", "F2", "F3"]
EVAL_DIR = os.path.join(config.DATA_DIR, "eval")


def available_systems(engine):
    systems = list(SPARSE_SYSTEMS)
    if "D0" in engine.dense:
        systems.append("D0")
    if "D1" in engine.dense:
        systems.append("D1")
        systems.append("H1")
        if engine.ltr is not None:
            systems.append("L1")
        if engine.gate is not None:
            systems.append("G1")
    return systems


def run_and_time(engine, queries, system):
    runs = {}
    times = []
    for qid in queries:
        start = time.perf_counter()
        ranked = engine.search(queries[qid], system, 100)
        times.append((time.perf_counter() - start) * 1000.0)
        runs[qid] = [engine.index.doc_ids[doc] for doc, _ in ranked]
    return runs, times


def evaluate_set(engine, systems, forms_dict, qrels, prefix):
    """Evaluate systems on one set of query forms. Returns rows for the three tables."""
    metric_rows = []
    invariance_rows = []
    efficiency_rows = []
    per_query_rows = []
    os.makedirs(os.path.join(EVAL_DIR, "runs"), exist_ok=True)
    for system in systems:
        runs_by_form = {}
        table_by_form = {}
        all_times = []
        for form in forms_dict:
            runs, times = run_and_time(engine, forms_dict[form], system)
            all_times.extend(times)
            table = per_query_metrics(runs, qrels)
            runs_by_form[form] = runs
            table_by_form[form] = table
            averages = average_metrics(table)
            for name in METRIC_NAMES:
                metric_rows.append({"system": system, "query_form": form, "metric": name,
                                    "value": round(averages[name], 4), "n_queries": len(table)})
            for qid in table:
                for name in METRIC_NAMES:
                    per_query_rows.append({"set": prefix, "system": system, "query_form": form,
                                           "qid": qid, "metric": name, "value": table[qid][name]})
            with open(os.path.join(EVAL_DIR, "runs", prefix + "_" + system + "_" + form + ".json"), "w",
                      encoding="utf-8") as f:
                json.dump(runs, f)
            print("  %-4s %-5s nDCG@10 %.4f  P@5 %.4f  R@100 %.4f" % (
                system, form, averages["ndcg@10"], averages["p@5"], averages["recall@100"]), flush=True)
        reference = "F1" if "F1" in forms_dict else list(forms_dict.keys())[0]
        inv = invariance_metrics(runs_by_form, table_by_form, reference)
        row = {"system": system}
        for key in inv:
            row[key] = round(inv[key], 4) if isinstance(inv[key], float) else inv[key]
        invariance_rows.append(row)
        efficiency_rows.append({"system": system,
                                "median_ms": round(float(np.median(all_times)), 2),
                                "p95_ms": round(float(np.percentile(all_times, 95)), 2),
                                "n_searches": len(all_times)})
    return metric_rows, invariance_rows, efficiency_rows, per_query_rows


def write_invariance(path, rows):
    columns = ["system"]
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    write_rows(path, rows, columns)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--systems", default="")
    args = parser.parse_args()
    engine = SearchEngine()
    systems = args.systems.split(",") if args.systems else available_systems(engine)
    print("systems:", systems)
    qrels = load_qrels("dev")

    # 1. Synthetic forms on all 350 dev queries
    forms_dict = load_forms("dev", DEV_FORMS)
    metric_rows, inv_rows, eff_rows, pq_rows = evaluate_set(engine, systems, forms_dict, qrels, "dev")
    write_rows(os.path.join(config.RESULTS_DIR, "main_metrics.csv"), metric_rows,
               ["system", "query_form", "metric", "value", "n_queries"])
    write_invariance(os.path.join(config.RESULTS_DIR, "invariance.csv"), inv_rows)
    write_rows(os.path.join(config.RESULTS_DIR, "efficiency.csv"), eff_rows,
               ["system", "median_ms", "p95_ms", "n_searches"])
    all_pq = pq_rows

    # 2. Human query set (only if the annotation sheets have been filled in)
    human_forms = load_human_forms()
    if len(human_forms) > 1:
        print("human query set forms:", list(human_forms.keys()))
        metric_rows, inv_rows, _, pq_rows = evaluate_set(engine, systems, human_forms, qrels, "human")
        write_rows(os.path.join(config.RESULTS_DIR, "human_metrics.csv"), metric_rows,
                   ["system", "query_form", "metric", "value", "n_queries"])
        write_invariance(os.path.join(config.RESULTS_DIR, "human_invariance.csv"), inv_rows)
        all_pq = all_pq + pq_rows
    else:
        print("human query set not filled in yet - skipped")

    write_rows(os.path.join(EVAL_DIR, "per_query.csv"), all_pq,
               ["set", "system", "query_form", "qid", "metric", "value"])
    print("done")


if __name__ == "__main__":
    main()
