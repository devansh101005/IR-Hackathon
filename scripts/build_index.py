"""Build the inverted index (all zones + champion lists) and save it in indexes/.

Usage:
    python scripts/build_index.py                 # main corpus  -> indexes/main/
    python scripts/build_index.py --mixed         # mixed-script corpus -> indexes/mixed/
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from lipisetu import config
from lipisetu.index.build import build_index, save_index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mixed", action="store_true", help="index the mixed-script corpus (experiment E6)")
    args = parser.parse_args()

    if args.mixed:
        corpus_path = config.MIXED_CORPUS_FILE
        folder = os.path.join(config.INDEX_DIR, "mixed")
        zones = ["all", "title", "dhvani"]
    else:
        corpus_path = config.CORPUS_FILE
        folder = os.path.join(config.INDEX_DIR, "main")
        zones = None

    start = time.time()
    index, titles, texts = build_index(corpus_path, zones)
    save_index(index, titles, texts, folder)
    print("documents:", index.num_docs)
    for name in index.zones:
        zone = index.zones[name]
        print("zone %-7s terms: %7d   postings: %9d" % (name, len(zone.terms), len(zone.doc_array)))
    print("saved to", folder, "in %.0fs" % (time.time() - start))


if __name__ == "__main__":
    main()
