"""E6: Does pooled df fix inflated idf in a mixed-script corpus?

The mixed corpus has 30% of its passages written in Roman script (made with
my romaniser, seed 13 - this is a SYNTHETIC simulation of mixed-script web
content). In it, a word like "भारत" / "bharat" has its df split between two
spellings, so each spelling looks rarer than the word really is.

1. Systems B1, B2, S1, S2, S3 on dev queries in all forms, on the mixed index.
2. A table of example words: df of each spelling, the pooled df, and the idf.
Outputs: results/e6_mixed_metrics.csv, results/e6_mixed_invariance.csv, results/e6_idf_examples.csv
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from lipisetu import config
from lipisetu.search import SearchEngine
from lipisetu.query import parse_query
from lipisetu.retrieval.bm25 import bm25_idf
from lipisetu.text.romanize import romanize_word
from lipisetu.text.analyzer import process_token
from lipisetu.text.tokenize import tokenize
from lipisetu.eval.run_eval import (load_forms, load_qrels, run_system, per_query_metrics, average_metrics,
                                    invariance_metrics, write_rows, METRIC_NAMES)

SYSTEMS = ["B1", "B2", "S1", "S2", "S3"]
FORMS = ["F1", "F2", "F3"]


def starts_with_sign(token):
    """True if the word starts with a vowel sign / anusvara instead of a letter."""
    first = ord(token[0])
    return 0x0900 <= first <= 0x0903 or 0x093A <= first <= 0x094F


def idf_examples(engine, forms_dict, how_many=15):
    """For content words of dev queries: df of the Devanagari and Roman spellings vs pooled df."""
    all_zone = engine.index.zones["all"]
    dhvani_zone = engine.index.zones["dhvani"]
    seen = set()
    rows = []
    for qid in sorted(forms_dict["F1"].keys()):
        query = parse_query(forms_dict["F1"][qid])
        for record in query["records"]:
            if record["stop"] or record["script"] != "deva" or record["token"] in seen:
                continue
            if starts_with_sign(record["token"]):
                continue    # a few MIRACL queries are damaged and start with a vowel sign
            seen.add(record["token"])
            roman_tokens = tokenize(romanize_word(record["token"]))
            if len(roman_tokens) != 1 or record["dhvani"] == "":
                continue
            deva_df = all_zone.get_df(record["stem"])
            roman_df = all_zone.get_df(process_token(roman_tokens[0])[0])
            pooled = dhvani_zone.get_df(record["dhvani"])
            if deva_df < 200 or roman_df < 50:
                continue
            rows.append({
                "word": record["token"], "roman": roman_tokens[0], "dhvani_key": record["dhvani"],
                "df_devanagari": deva_df, "df_roman": roman_df, "df_pooled": pooled,
                "idf_devanagari": round(bm25_idf(deva_df, engine.num_docs), 3),
                "idf_roman": round(bm25_idf(roman_df, engine.num_docs), 3),
                "idf_pooled": round(bm25_idf(pooled, engine.num_docs), 3),
            })
            if len(rows) >= how_many:
                return rows
    return rows


def main():
    engine = SearchEngine(index_folder=os.path.join(config.INDEX_DIR, "mixed"), load_neural=False)
    qrels = load_qrels("dev")
    forms_dict = load_forms("dev", FORMS)
    metric_rows = []
    inv_rows = []
    for system in SYSTEMS:
        runs_by_form = {}
        tables = {}
        for form in FORMS:
            runs_by_form[form] = run_system(engine, forms_dict[form], system, 100)
            tables[form] = per_query_metrics(runs_by_form[form], qrels)
            averages = average_metrics(tables[form])
            for name in METRIC_NAMES:
                metric_rows.append({"system": system, "query_form": form, "metric": name,
                                    "value": round(averages[name], 4), "n_queries": len(tables[form])})
            print("  mixed %-3s %-3s nDCG@10 %.4f" % (system, form, averages["ndcg@10"]), flush=True)
        inv = invariance_metrics(runs_by_form, tables, "F1")
        row = {"system": system}
        for key in inv:
            row[key] = round(inv[key], 4) if isinstance(inv[key], float) else inv[key]
        inv_rows.append(row)
    write_rows(os.path.join(config.RESULTS_DIR, "e6_mixed_metrics.csv"), metric_rows,
               ["system", "query_form", "metric", "value", "n_queries"])
    write_rows(os.path.join(config.RESULTS_DIR, "e6_mixed_invariance.csv"), inv_rows,
               ["system", "n_queries", "gap_F2", "gap_F3", "csc@10", "worst_ndcg@10"])
    examples = idf_examples(engine, forms_dict)
    write_rows(os.path.join(config.RESULTS_DIR, "e6_idf_examples.csv"), examples,
               ["word", "roman", "dhvani_key", "df_devanagari", "df_roman", "df_pooled",
                "idf_devanagari", "idf_roman", "idf_pooled"])
    for row in examples[:8]:
        print(row)


if __name__ == "__main__":
    main()
