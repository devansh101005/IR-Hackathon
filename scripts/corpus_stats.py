"""E3: How do stop words and idf behave on a Hindi corpus? (T5 IR hook)

Counts document frequency over the normalised corpus WITH stop words, then:
  - top 40 terms by df, and how many of them are in my stop list
  - Zipf data (collection frequency by rank)
  - idf histogram of the vocabulary
  - how much of the corpus is written in Roman script (real mixed-script text)
Outputs: results/e3_corpus_stats.json, e3_top_df_terms.csv, e3_zipf.csv, e3_idf_hist.csv
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np

from lipisetu import config
from lipisetu.text.tokenize import tokenize
from lipisetu.text.script import token_script
from lipisetu.text.stopwords import is_stop_word
from lipisetu.eval.run_eval import write_rows


def main():
    df = {}
    cf = {}
    num_docs = 0
    total_tokens = 0
    script_counts = {"deva": 0, "roman": 0, "digit": 0}
    docs_with_roman = 0
    with open(config.CORPUS_FILE, encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            tokens = tokenize(doc["title"] + " " + doc["text"])
            num_docs += 1
            total_tokens += len(tokens)
            has_roman = False
            for token in tokens:
                cf[token] = cf.get(token, 0) + 1
                script = token_script(token)
                script_counts[script] += 1
                if script == "roman":
                    has_roman = True
            if has_roman:
                docs_with_roman += 1
            for token in set(tokens):
                df[token] = df.get(token, 0) + 1

    by_df = sorted(df.items(), key=lambda item: item[1], reverse=True)
    top_rows = []
    stop_hits = 0
    for rank in range(40):
        term, value = by_df[rank]
        in_list = is_stop_word(term)
        if in_list:
            stop_hits += 1
        top_rows.append({"rank": rank + 1, "term": term, "df": value,
                         "idf": round(math.log10(num_docs / value), 3), "in_my_stop_list": in_list})
    write_rows(os.path.join(config.RESULTS_DIR, "e3_top_df_terms.csv"), top_rows,
               ["rank", "term", "df", "idf", "in_my_stop_list"])

    by_cf = sorted(cf.values(), reverse=True)
    zipf_rows = []
    rank = 1
    while rank <= len(by_cf):
        zipf_rows.append({"rank": rank, "collection_frequency": by_cf[rank - 1]})
        rank = rank + 1 if rank < 100 else int(rank * 1.1) + 1
    write_rows(os.path.join(config.RESULTS_DIR, "e3_zipf.csv"), zipf_rows, ["rank", "collection_frequency"])

    idfs = []
    for term in df:
        idfs.append(math.log10(num_docs / df[term]))
    counts, edges = np.histogram(idfs, bins=25)
    hist_rows = []
    for i in range(len(counts)):
        hist_rows.append({"idf_from": round(float(edges[i]), 3), "idf_to": round(float(edges[i + 1]), 3),
                          "terms": int(counts[i])})
    write_rows(os.path.join(config.RESULTS_DIR, "e3_idf_hist.csv"), hist_rows, ["idf_from", "idf_to", "terms"])

    stats = {
        "documents": num_docs,
        "tokens": total_tokens,
        "vocabulary": len(df),
        "terms_seen_once": sum(1 for v in cf.values() if v == 1),
        "top40_df_terms_in_stop_list": stop_hits,
        "share_of_tokens_roman": round(script_counts["roman"] / float(total_tokens), 4),
        "share_of_docs_with_roman_words": round(docs_with_roman / float(num_docs), 4),
        "avg_tokens_per_doc": round(total_tokens / float(num_docs), 1),
    }
    with open(os.path.join(config.RESULTS_DIR, "e3_corpus_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print("top df terms:", [row["term"] for row in top_rows[:20]])


if __name__ == "__main__":
    main()
