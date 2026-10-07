"""Make the synthetic query forms, the mixed-script corpus and the human annotation sheets.

Outputs (small, committed to git):
    queries/dev_F1.tsv, dev_F2.tsv, dev_F3.tsv        test queries in 3 forms
    queries/train_F1.tsv, train_F2.tsv, train_F3.tsv  tuning queries in 3 forms
    queries/human/sheet_<name>.tsv                    blank sheets for the 3 annotators
Output (large, not committed):
    data/corpus_mixed.jsonl   30% of passages written in Roman script (experiment E6)
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from lipisetu import config
from lipisetu.data import read_topics, write_query_tsv
from lipisetu.text.romanize import romanize, casual_romanize, make_rng

HUMAN_SET_SIZE = 60
ANNOTATORS = ["devansh", "teammate_a", "teammate_b"]
MIXED_FRACTION = 0.3
CASUAL_NOISE = 0.3


def make_forms(topics, seed):
    """Return three dicts (F1, F2, F3) for the given topics."""
    f1 = {}
    f2 = {}
    f3 = {}
    rng = make_rng(seed)
    for qid in sorted(topics.keys()):
        text = topics[qid]
        f1[qid] = text
        f2[qid] = romanize(text)
        f3[qid] = casual_romanize(text, rng, CASUAL_NOISE)
    return f1, f2, f3


def write_forms(split, topics, seed):
    f1, f2, f3 = make_forms(topics, seed)
    write_query_tsv(os.path.join(config.QUERY_DIR, split + "_F1.tsv"), f1)
    write_query_tsv(os.path.join(config.QUERY_DIR, split + "_F2.tsv"), f2)
    write_query_tsv(os.path.join(config.QUERY_DIR, split + "_F3.tsv"), f3)
    print(split, "queries:", len(f1))


def write_human_sheets(dev_topics):
    """Pick 60 dev queries (fixed seed) and write one blank sheet per annotator."""
    folder = os.path.join(config.QUERY_DIR, "human")
    os.makedirs(folder, exist_ok=True)
    qids = sorted(dev_topics.keys())
    rng = random.Random(config.SEED)
    chosen = sorted(rng.sample(qids, HUMAN_SET_SIZE))
    for name in ANNOTATORS:
        path = os.path.join(folder, "sheet_" + name + ".tsv")
        if os.path.exists(path):
            print("keeping existing", path)
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write("row\tqid\tdevanagari\troman\tcode_mixed\tenglish\n")
            for row in range(len(chosen)):
                qid = chosen[row]
                f.write(str(row + 1) + "\t" + qid + "\t" + dev_topics[qid] + "\t\t\t\n")
        print("wrote", path)


def write_mixed_corpus():
    """Romanise 30% of the passages (title + text) to simulate mixed-script web content."""
    rng = random.Random(config.SEED)
    count = 0
    romanised = 0
    with open(config.CORPUS_FILE, encoding="utf-8") as f_in, \
            open(config.MIXED_CORPUS_FILE, "w", encoding="utf-8") as f_out:
        for line in f_in:
            doc = json.loads(line)
            if rng.random() < MIXED_FRACTION:
                doc["title"] = romanize(doc["title"])
                doc["text"] = romanize(doc["text"])
                romanised += 1
            f_out.write(json.dumps(doc, ensure_ascii=False) + "\n")
            count += 1
    print("mixed corpus:", romanised, "of", count, "passages romanised")


def main():
    os.makedirs(config.QUERY_DIR, exist_ok=True)
    dev_topics = read_topics(config.TOPICS_DEV)
    train_topics = read_topics(config.TOPICS_TRAIN)
    write_forms("dev", dev_topics, config.SEED)
    write_forms("train", train_topics, config.SEED + 1)
    write_human_sheets(dev_topics)
    write_mixed_corpus()


if __name__ == "__main__":
    main()
