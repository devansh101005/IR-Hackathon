"""Run systems on query sets and compute all metrics.

Used by scripts/tune_sparse.py (train split) and scripts/run_all_eval.py (dev split).
"""
import csv
import os

from lipisetu import config
from lipisetu.data import read_qrels, read_query_tsv, relevant_docs
from lipisetu.eval.metrics import all_metrics, cross_script_consistency, mean

METRIC_NAMES = ["ndcg@10", "p@5", "p@10", "recall@100", "mrr@10"]


def load_forms(split, forms):
    """Load query files queries/<split>_<form>.tsv. Returns {form: {qid: text}}."""
    result = {}
    for form in forms:
        path = os.path.join(config.QUERY_DIR, split + "_" + form + ".tsv")
        result[form] = read_query_tsv(path)
    return result


def load_qrels(split):
    if split == "dev":
        return read_qrels(config.QRELS_DEV)
    return read_qrels(config.QRELS_TRAIN)


def run_system(engine, queries, system, k=100):
    """Search every query. Returns {qid: [doc ids, best first]}."""
    runs = {}
    for qid in queries:
        ranked = engine.search(queries[qid], system, k)
        doc_ids = []
        for doc_number, _ in ranked:
            doc_ids.append(engine.index.doc_ids[doc_number])
        runs[qid] = doc_ids
    return runs


def per_query_metrics(runs, qrels):
    """Returns {qid: {metric: value}} for the queries that have at least one relevant passage."""
    table = {}
    for qid in runs:
        relevant = relevant_docs(qrels, qid)
        if len(relevant) == 0:
            continue
        table[qid] = all_metrics(runs[qid], relevant)
    return table


def average_metrics(table):
    averages = {}
    for name in METRIC_NAMES:
        values = []
        for qid in table:
            values.append(table[qid][name])
        averages[name] = mean(values)
    return averages


def invariance_metrics(runs_by_form, table_by_form, reference_form="F1"):
    """Script Gap per form, CSC@10 and worst-script nDCG@10 over the queries all forms share."""
    forms = list(runs_by_form.keys())
    shared = None
    for form in forms:
        qids = set(table_by_form[form].keys())
        shared = qids if shared is None else shared & qids
    shared = sorted(shared)
    result = {"n_queries": len(shared)}
    if len(shared) == 0:
        return result
    # Script Gap: nDCG of the reference form minus nDCG of each other form
    reference = mean([table_by_form[reference_form][q]["ndcg@10"] for q in shared])
    for form in forms:
        if form == reference_form:
            continue
        other = mean([table_by_form[form][q]["ndcg@10"] for q in shared])
        result["gap_" + form] = reference - other
    # CSC@10 and worst-script nDCG@10
    csc_values = []
    worst_values = []
    for qid in shared:
        rankings = {}
        scores = []
        for form in forms:
            rankings[form] = runs_by_form[form][qid]
            scores.append(table_by_form[form][qid]["ndcg@10"])
        csc_values.append(cross_script_consistency(rankings))
        worst_values.append(min(scores))
    result["csc@10"] = mean(csc_values)
    result["worst_ndcg@10"] = mean(worst_values)
    return result


def write_rows(path, rows, columns):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
