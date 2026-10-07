"""E5: Which Dhvani rules matter? Switch off one rule at a time and measure.

For every rule variant I rebuild the Dhvani zone with that variant's keys and
run S1 (surface BM25 + Dhvani zone) on the dev queries in all three forms.
I also measure how much each variant merges: the average number of different
surface words that share one key (a higher number = more collisions).
Outputs: results/e5_dhvani_ablation.csv
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np

from lipisetu import config
from lipisetu.index.inverted_index import Zone
from lipisetu.search import SearchEngine
from lipisetu.query import parse_query
from lipisetu.retrieval.bm25 import bm25_zone
from lipisetu.retrieval.topk import top_k
from lipisetu.text.tokenize import tokenize
from lipisetu.text.stopwords import is_stop_word
from lipisetu.text.dhvani import dhvani_key, DEFAULT_RULES, rules_without
from lipisetu.eval.run_eval import load_forms, load_qrels, per_query_metrics, average_metrics, invariance_metrics, write_rows

FORMS = ["F1", "F2", "F3"]


def corpus_tokens():
    """Tokenise every document once (title + body) and keep the token lists."""
    all_tokens = []
    with open(config.CORPUS_FILE, encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            all_tokens.append(tokenize(doc["title"]) + [""] + tokenize(doc["text"]))
    return all_tokens


def build_variant_zone(all_tokens, rules, num_docs):
    cache = {}
    zone = Zone("dhvani_variant", num_docs, keep_positions=False)
    key_types = {}
    for doc_number in range(num_docs):
        terms = []
        tokens = all_tokens[doc_number]
        for position in range(len(tokens)):
            token = tokens[position]
            if token == "" or is_stop_word(token):
                continue
            if token not in cache:
                cache[token] = dhvani_key(token, rules)
            key = cache[token]
            if key != "":
                terms.append((key, position))
                if key not in key_types:
                    key_types[key] = set()
                key_types[key].add(token)
        zone.add_document(doc_number, terms)
    zone.finish()
    sizes = [len(types) for types in key_types.values()]
    return zone, len(key_types), float(np.mean(sizes))


def query_keys(query, rules):
    keys = []
    for record in query["records"]:
        if record["stop"]:
            continue
        key = dhvani_key(record["token"], rules)
        if key != "":
            keys.append(key)
    return keys


def run_variant(engine, zone, rules, forms_dict):
    p = engine.params
    runs_by_form = {}
    for form in forms_dict:
        runs = {}
        for qid in forms_dict[form]:
            query = parse_query(forms_dict[form][qid])
            scores = np.zeros(engine.num_docs)
            bm25_zone(engine.index.zones["all"], query["surface_terms"], scores, 1.0, p["k1"], p["b"])
            bm25_zone(zone, query_keys(query, rules), scores, p["w_dhvani"], p["k1"], p["b"])
            runs[qid] = [engine.index.doc_ids[doc] for doc, _ in top_k(scores, 100)]
        runs_by_form[form] = runs
    return runs_by_form


def main():
    engine = SearchEngine(load_neural=False)
    qrels = load_qrels("dev")
    forms_dict = load_forms("dev", FORMS)
    print("tokenising corpus once...")
    all_tokens = corpus_tokens()
    variants = [("all rules (Dhvani)", DEFAULT_RULES)]
    for rule in DEFAULT_RULES:
        variants.append(("without " + rule, rules_without(rule)))
    rows = []
    for name, rules in variants:
        zone, num_keys, types_per_key = build_variant_zone(all_tokens, rules, engine.num_docs)
        runs_by_form = run_variant(engine, zone, rules, forms_dict)
        tables = {}
        row = {"variant": name, "distinct_keys": num_keys, "surface_words_per_key": round(types_per_key, 3)}
        for form in FORMS:
            tables[form] = per_query_metrics(runs_by_form[form], qrels)
            row["ndcg@10_" + form] = round(average_metrics(tables[form])["ndcg@10"], 4)
        inv = invariance_metrics(runs_by_form, tables, "F1")
        row["csc@10"] = round(inv["csc@10"], 4)
        row["worst_ndcg@10"] = round(inv["worst_ndcg@10"], 4)
        rows.append(row)
        print(row, flush=True)
    write_rows(os.path.join(config.RESULTS_DIR, "e5_dhvani_ablation.csv"), rows,
               ["variant", "distinct_keys", "surface_words_per_key", "ndcg@10_F1", "ndcg@10_F2", "ndcg@10_F3",
                "csc@10", "worst_ndcg@10"])


if __name__ == "__main__":
    main()
