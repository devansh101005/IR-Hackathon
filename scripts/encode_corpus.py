"""Encode every passage with the int8 e5-small encoder and save the vectors.

Usage: python scripts/encode_corpus.py
Output: indexes/dense/passages.npy  (float16, one 384-dim row per passage, same order as the index)
This takes a while on a CPU (about 30-45 passages per second on 4 cores).
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from lipisetu import config
from lipisetu.dense.encoder import OnnxEncoder

CHUNK = 2000


def main():
    texts = []
    with open(config.CORPUS_FILE, encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            texts.append(doc["title"] + ". " + doc["text"])
    folder = os.path.join(config.INDEX_DIR, "dense")
    os.makedirs(folder, exist_ok=True)
    model_folder = os.path.join(config.MODEL_DIR, "e5-small-onnx")
    threads = int(os.environ.get("ENCODE_THREADS", "4"))
    encoder = OnnxEncoder(os.path.join(model_folder, "model_int8.onnx"), model_folder, threads=threads)

    # Encode in chunks and save each chunk, so an interrupted run can continue
    start = time.time()
    parts = []
    for chunk_start in range(0, len(texts), CHUNK):
        part_path = os.path.join(folder, "part_%06d.npy" % chunk_start)
        if os.path.exists(part_path):
            parts.append(np.load(part_path))
            continue
        vectors = encoder.encode(texts[chunk_start:chunk_start + CHUNK], "passage: ", max_length=256)
        np.save(part_path, vectors.astype(np.float16))
        parts.append(vectors.astype(np.float16))
        done = chunk_start + len(vectors)
        rate = done / (time.time() - start)
        print("  %d / %d passages, %.1f per second" % (done, len(texts), rate), flush=True)

    all_vectors = np.concatenate(parts)
    np.save(os.path.join(folder, "passages.npy"), all_vectors)
    for chunk_start in range(0, len(texts), CHUNK):
        os.remove(os.path.join(folder, "part_%06d.npy" % chunk_start))
    print("saved", all_vectors.shape, "in %.0fs" % (time.time() - start))


if __name__ == "__main__":
    main()
