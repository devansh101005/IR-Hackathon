"""Build the inverted index from the corpus file and save / load it.

Every document goes through the same pipeline as the queries
(lipisetu.text.analyzer), then its terms are added to each zone.
"""
import json
import os
import pickle
import time

from lipisetu.index.inverted_index import InvertedIndex
from lipisetu.retrieval.topk import ChampionLists
from lipisetu.text.tokenize import tokenize
from lipisetu.text.analyzer import surface_terms, dhvani_terms, soundex_terms, raw_terms

ALL_ZONES = ["all", "title", "dhvani", "soundex", "nostem", "raw"]
POSITIONAL_ZONES = ["all", "dhvani"]
CHAMPION_ZONES = ["all", "dhvani"]
CHAMPION_R = 200
INDEX_VERSION = 1


def shift_positions(terms, offset):
    """Add an offset to every position (so body positions come after the title)."""
    shifted = []
    for term, position in terms:
        shifted.append((term, position + offset))
    return shifted


def document_terms(title, text, zone_names):
    """Make the (term, position) list of every zone for one document."""
    title_tokens = tokenize(title)
    body_tokens = tokenize(text)
    # Leave a gap of 1 between title and body, so a phrase can't cross from one to the other
    offset = len(title_tokens) + 1
    result = {}
    if "all" in zone_names:
        result["all"] = surface_terms(title_tokens) + shift_positions(surface_terms(body_tokens), offset)
    if "title" in zone_names:
        result["title"] = surface_terms(title_tokens)
    if "dhvani" in zone_names:
        result["dhvani"] = dhvani_terms(title_tokens) + shift_positions(dhvani_terms(body_tokens), offset)
    if "soundex" in zone_names:
        result["soundex"] = soundex_terms(title_tokens) + shift_positions(soundex_terms(body_tokens), offset)
    if "nostem" in zone_names:
        result["nostem"] = (surface_terms(title_tokens, use_stemming=False)
                            + shift_positions(surface_terms(body_tokens, use_stemming=False), offset))
    if "raw" in zone_names:
        result["raw"] = raw_terms(title + " " + text)
    return result


def build_index(corpus_path, zone_names=None):
    """Read the corpus and build every zone. Returns (index, titles, texts)."""
    if zone_names is None:
        zone_names = ALL_ZONES
    docs = []
    with open(corpus_path, encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    doc_ids = []
    titles = []
    texts = []
    for doc in docs:
        doc_ids.append(doc["docid"])
        titles.append(doc["title"])
        texts.append(doc["text"])

    index = InvertedIndex(doc_ids)
    for name in zone_names:
        index.add_zone(name, keep_positions=(name in POSITIONAL_ZONES))

    start_time = time.time()
    for doc_number in range(len(docs)):
        zone_terms = document_terms(titles[doc_number], texts[doc_number], zone_names)
        for name in zone_names:
            index.zones[name].add_document(doc_number, zone_terms[name])
        if doc_number % 10000 == 0:
            print("  indexed", doc_number, "docs, %.0fs" % (time.time() - start_time))

    for name in zone_names:
        print("  packing zone", name)
        index.zones[name].finish()
    for name in CHAMPION_ZONES:
        if name in zone_names:
            print("  champion lists for", name)
            index.champions[name] = ChampionLists(index.zones[name], CHAMPION_R)
    index.version = INDEX_VERSION
    return index, titles, texts


def save_index(index, titles, texts, folder):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "index.pkl"), "wb") as f:
        pickle.dump(index, f, protocol=pickle.HIGHEST_PROTOCOL)
    with open(os.path.join(folder, "docstore.pkl"), "wb") as f:
        pickle.dump({"titles": titles, "texts": texts}, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_index(folder):
    with open(os.path.join(folder, "index.pkl"), "rb") as f:
        index = pickle.load(f)
    return index


def load_docstore(folder):
    with open(os.path.join(folder, "docstore.pkl"), "rb") as f:
        store = pickle.load(f)
    return store["titles"], store["texts"]
