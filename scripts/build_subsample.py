"""Build the corpus subsample ("deciding what a document is").

One document = one MIRACL passage. I keep every passage that is judged for any
dev or train query, plus a random sample of the other passages. The same
subsample is used for every system, so comparisons between systems are fair.

Usage: python scripts/build_subsample.py --size 100000 --seed 13
"""
import argparse
import gzip
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from lipisetu import config
from lipisetu.data import read_qrels


def judged_doc_ids():
    """All doc ids that appear in the dev or train judgments."""
    doc_ids = set()
    for path in [config.QRELS_DEV, config.QRELS_TRAIN]:
        qrels = read_qrels(path)
        for qid in qrels:
            for doc_id in qrels[qid]:
                doc_ids.add(doc_id)
    return doc_ids


def count_passages():
    """First pass: count how many passages there are in total."""
    total = 0
    for shard in config.CORPUS_SHARDS:
        with gzip.open(shard, "rt", encoding="utf-8") as f:
            for _ in f:
                total += 1
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=config.DEFAULT_SAMPLE_SIZE,
                        help="number of extra random passages to keep")
    parser.add_argument("--seed", type=int, default=config.SEED)
    args = parser.parse_args()

    keep_ids = judged_doc_ids()
    print("judged passages:", len(keep_ids))

    total = count_passages()
    print("passages in MIRACL-hi:", total)

    # Pick random line numbers for the extra passages
    random.seed(args.seed)
    chosen_lines = set(random.sample(range(total), min(args.size, total)))

    os.makedirs(config.DATA_DIR, exist_ok=True)
    kept = 0
    found_judged = 0
    line_number = 0
    with open(config.CORPUS_FILE, "w", encoding="utf-8") as out_file:
        for shard in config.CORPUS_SHARDS:
            with gzip.open(shard, "rt", encoding="utf-8") as f:
                for line in f:
                    doc = json.loads(line)
                    is_judged = doc["docid"] in keep_ids
                    if is_judged or line_number in chosen_lines:
                        record = {"docid": doc["docid"], "title": doc["title"], "text": doc["text"]}
                        out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                        kept += 1
                        if is_judged:
                            found_judged += 1
                    line_number += 1

    print("judged passages found in corpus:", found_judged)
    print("passages kept:", kept)
    print("saved", config.CORPUS_FILE)


if __name__ == "__main__":
    main()
