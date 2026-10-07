"""Tune the sparse parameters on the TRAIN split (never on dev, which is the test set).

Objective: the average nDCG@10 over the three query forms (Devanagari, standard
Roman, casual Roman). So the parameters are chosen to work well for every
script, not just for Devanagari.

Steps (each grid keeps the best value found so far):
    1. BM25 k1, b          on B1 with Devanagari queries
    2. Dhvani zone weight   on S1
    3. Soundex zone weight  on S0 (so the comparison system is tuned fairly too)
    4. title weight, proximity weight  on S3

Output: results/tuned_params.json and results/tuning_log.csv
"""
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from lipisetu import config
from lipisetu.search import SearchEngine, PARAMS_FILE, DEFAULT_PARAMS
from lipisetu.eval.run_eval import load_forms, load_qrels, run_system, per_query_metrics, average_metrics, write_rows

TRAIN_SAMPLE = 400
FORMS = ["F1", "F2", "F3"]


def sample_queries(forms_dict):
    """Use the same random 400 train queries for every grid point (fixed seed)."""
    qids = sorted(forms_dict["F1"].keys())
    rng = random.Random(config.SEED)
    chosen = sorted(rng.sample(qids, TRAIN_SAMPLE))
    sampled = {}
    for form in forms_dict:
        sampled[form] = {}
        for qid in chosen:
            if qid in forms_dict[form]:
                sampled[form][qid] = forms_dict[form][qid]
    return sampled


def score(engine, queries_by_form, qrels, system, forms):
    """Average nDCG@10 over the given forms."""
    total = 0.0
    for form in forms:
        runs = run_system(engine, queries_by_form[form], system, 100)
        total += average_metrics(per_query_metrics(runs, qrels))["ndcg@10"]
    return total / len(forms)


def grid(engine, queries_by_form, qrels, system, forms, names, values_list, log):
    """Try every combination of values for the named parameters; keep the best."""
    best_value = None
    best_combo = None
    combos = [[]]
    for values in values_list:
        new_combos = []
        for combo in combos:
            for value in values:
                new_combos.append(combo + [value])
        combos = new_combos
    for combo in combos:
        for i in range(len(names)):
            engine.params[names[i]] = combo[i]
        value = score(engine, queries_by_form, qrels, system, forms)
        row = {"system": system, "forms": "+".join(forms), "ndcg@10": round(value, 4)}
        for i in range(len(names)):
            row[names[i]] = combo[i]
        log.append(row)
        print("  ", system, dict(zip(names, combo)), "-> %.4f" % value)
        if best_value is None or value > best_value:
            best_value = value
            best_combo = combo
    for i in range(len(names)):
        engine.params[names[i]] = best_combo[i]
    print("best", dict(zip(names, best_combo)), "%.4f" % best_value)


def main():
    start = time.time()
    if os.path.exists(PARAMS_FILE):
        os.remove(PARAMS_FILE)       # start from the defaults
    engine = SearchEngine(load_neural=False)
    engine.params = dict(DEFAULT_PARAMS)
    qrels = load_qrels("train")
    queries_by_form = sample_queries(load_forms("train", FORMS))
    log = []

    print("1. BM25 k1 and b (B1, Devanagari)")
    grid(engine, queries_by_form, qrels, "B1", ["F1"], ["k1", "b"],
         [[0.6, 0.9, 1.2, 1.5, 1.8], [0.3, 0.5, 0.75, 0.9]], log)
    print("2. Dhvani zone weight (S1, all forms)")
    grid(engine, queries_by_form, qrels, "S1", FORMS, ["w_dhvani"],
         [[0.5, 1.0, 1.5, 2.0, 3.0, 4.0]], log)
    print("3. Soundex zone weight (S0, all forms)")
    grid(engine, queries_by_form, qrels, "S0", FORMS, ["w_soundex"],
         [[0.5, 1.0, 1.5, 2.0, 3.0, 4.0]], log)
    print("4. title weight and proximity weight (S3, all forms)")
    grid(engine, queries_by_form, qrels, "S3", FORMS, ["w_title", "lambda_prox"],
         [[0.0, 0.5, 1.0, 1.5, 2.0, 3.0], [0.0, 1.0, 2.0, 4.0]], log)

    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    with open(PARAMS_FILE, "w", encoding="utf-8") as f:
        json.dump(engine.params, f, indent=2)
    columns = ["system", "forms", "ndcg@10", "k1", "b", "w_dhvani", "w_soundex", "w_title", "lambda_prox"]
    write_rows(os.path.join(config.RESULTS_DIR, "tuning_log.csv"), log, columns)
    print("saved", PARAMS_FILE, engine.params)
    print("took %.0fs" % (time.time() - start))


if __name__ == "__main__":
    main()
