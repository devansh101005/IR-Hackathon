"""Download the MIRACL Hindi data (topics, relevance judgments and passages).

Source: https://huggingface.co/datasets/miracl (Apache-2.0, text from Wikipedia).
Files are saved in data/raw/. Files that already exist are skipped.
"""
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from lipisetu import config

MIRACL = "https://huggingface.co/datasets/miracl/miracl/resolve/main/miracl-v1.0-hi"
CORPUS = "https://huggingface.co/datasets/miracl/miracl-corpus/resolve/main/miracl-corpus-v1.0-hi"

FILES = [
    (MIRACL + "/topics/topics.miracl-v1.0-hi-dev.tsv", config.TOPICS_DEV),
    (MIRACL + "/topics/topics.miracl-v1.0-hi-train.tsv", config.TOPICS_TRAIN),
    (MIRACL + "/qrels/qrels.miracl-v1.0-hi-dev.tsv", config.QRELS_DEV),
    (MIRACL + "/qrels/qrels.miracl-v1.0-hi-train.tsv", config.QRELS_TRAIN),
    (CORPUS + "/docs-0.jsonl.gz", config.CORPUS_SHARDS[0]),
    (CORPUS + "/docs-1.jsonl.gz", config.CORPUS_SHARDS[1]),
]


def download(url, path):
    """Download one file in chunks and print simple progress."""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        print("already have", os.path.basename(path))
        return
    print("downloading", os.path.basename(path))
    temp_path = path + ".part"
    with urllib.request.urlopen(url) as response, open(temp_path, "wb") as out_file:
        total = int(response.headers.get("Content-Length", 0))
        done = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out_file.write(chunk)
            done += len(chunk)
            if total > 0:
                print("  %.0f%%" % (100.0 * done / total), end="\r")
    os.rename(temp_path, path)
    print("  saved", path)


def main():
    os.makedirs(config.RAW_DIR, exist_ok=True)
    for url, path in FILES:
        download(url, path)
    print("done")


if __name__ == "__main__":
    main()
