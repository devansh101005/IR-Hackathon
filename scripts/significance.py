"""Paired randomisation test for the headline comparisons (nDCG@10, dev queries).

For two systems A and B evaluated on the same queries, the null hypothesis is
"A and B are equally good". I randomly swap A's and B's score for each query
(10,000 times) and count how often the mean difference is at least as big as
the real one. That fraction is the p-value (two-sided).
Output: results/significance.csv
"""
import csv
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from lipisetu import config
from lipisetu.eval.run_eval import write_rows

PAIRS = [("S1", "B1"), ("S1", "S0"), ("S3", "B2"), ("S2", "S1"), ("S3", "S2"), ("D1", "D0"),
         ("H1", "S3"), ("L1", "H1"), ("G1", "H1"), ("B1", "B1N")]
PERMUTATIONS = 10000


def load_scores():
    """{(set, system, form): {qid: ndcg}} from data/eval/per_query.csv."""
    scores = {}
    path = os.path.join(config.DATA_DIR, "eval", "per_query.csv")
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["metric"] != "ndcg@10":
                continue
            key = (row["set"], row["system"], row["query_form"])
            if key not in scores:
                scores[key] = {}
            scores[key][row["qid"]] = float(row["value"])
    return scores


def randomisation_test(a_values, b_values, seed=13):
    differences = [a_values[i] - b_values[i] for i in range(len(a_values))]
    observed = abs(sum(differences) / len(differences))
    rng = random.Random(seed)
    at_least = 0
    for _ in range(PERMUTATIONS):
        total = 0.0
        for d in differences:
            total += d if rng.random() < 0.5 else -d
        if abs(total / len(differences)) >= observed - 1e-12:
            at_least += 1
    return (at_least + 1) / float(PERMUTATIONS + 1)


def main():
    scores = load_scores()
    rows = []
    for set_name in ["dev", "human"]:
        forms = sorted(set(key[2] for key in scores if key[0] == set_name))
        for a, b in PAIRS:
            for form in forms:
                key_a = (set_name, a, form)
                key_b = (set_name, b, form)
                if key_a not in scores or key_b not in scores:
                    continue
                qids = sorted(set(scores[key_a]) & set(scores[key_b]))
                a_values = [scores[key_a][q] for q in qids]
                b_values = [scores[key_b][q] for q in qids]
                p = randomisation_test(a_values, b_values)
                mean_a = sum(a_values) / len(a_values)
                mean_b = sum(b_values) / len(b_values)
                rows.append({"set": set_name, "form": form, "system_a": a, "system_b": b,
                             "ndcg_a": round(mean_a, 4), "ndcg_b": round(mean_b, 4),
                             "difference": round(mean_a - mean_b, 4), "p_value": round(p, 4),
                             "significant": p < 0.05, "n_queries": len(qids)})
                print(rows[-1])
    write_rows(os.path.join(config.RESULTS_DIR, "significance.csv"), rows,
               ["set", "form", "system_a", "system_b", "ndcg_a", "ndcg_b", "difference", "p_value",
                "significant", "n_queries"])


if __name__ == "__main__":
    main()
