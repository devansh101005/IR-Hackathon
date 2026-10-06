"""Project settings: folder paths, the random seed and default parameters.

Every script imports this file, so all paths and numbers live in one place.
"""
import os

# Folder layout
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SRC_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
INDEX_DIR = os.path.join(PROJECT_ROOT, "indexes")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
QUERY_DIR = os.path.join(PROJECT_ROOT, "queries")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

# Files made by the scripts
CORPUS_FILE = os.path.join(DATA_DIR, "corpus.jsonl")
MIXED_CORPUS_FILE = os.path.join(DATA_DIR, "corpus_mixed.jsonl")
TOPICS_DEV = os.path.join(RAW_DIR, "topics.miracl-v1.0-hi-dev.tsv")
TOPICS_TRAIN = os.path.join(RAW_DIR, "topics.miracl-v1.0-hi-train.tsv")
QRELS_DEV = os.path.join(RAW_DIR, "qrels.miracl-v1.0-hi-dev.tsv")
QRELS_TRAIN = os.path.join(RAW_DIR, "qrels.miracl-v1.0-hi-train.tsv")
CORPUS_SHARDS = [
    os.path.join(RAW_DIR, "docs-0.jsonl.gz"),
    os.path.join(RAW_DIR, "docs-1.jsonl.gz"),
]

# Random seed used everywhere, so every run gives the same result
SEED = 13

# Corpus size: every judged passage + this many random extra passages
DEFAULT_SAMPLE_SIZE = 100000

# BM25 defaults (tuned later on the train split)
BM25_K1 = 1.2
BM25_B = 0.75

# Zone weights: how much a match in each zone counts
ZONE_WEIGHTS = {"title": 0.5, "body": 1.0, "dhvani": 0.3}

# Dense model
DENSE_MODEL_NAME = "intfloat/multilingual-e5-small"
DENSE_DIM = 384

# Reciprocal rank fusion constant (Cormack et al. 2009)
RRF_K = 60

# How many results each stage keeps
TOP_K = 100
