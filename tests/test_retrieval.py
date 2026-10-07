"""Tests for the index and retrieval code, on a tiny corpus written to a temp folder."""
import json
import math

import numpy as np
from rank_bm25 import BM25Okapi

from lipisetu.index.build import build_index
from lipisetu.retrieval.bm25 import bm25_zone, bm25_idf, pooled_df_table
from lipisetu.retrieval.boolean import boolean_search, phrase_search, intersect, intersect_with_skips
from lipisetu.retrieval.proximity import smallest_window, proximity_score
from lipisetu.retrieval.rrf import rrf
from lipisetu.retrieval.topk import top_k
from lipisetu.retrieval.tfidf import tfidf_cosine
from lipisetu.query import parse_query

DOCS = [
    {"docid": "1#0", "title": "मौसम", "text": "आज का मौसम अच्छा है और कल बारिश होगी"},
    {"docid": "2#0", "title": "क्रिकेट", "text": "भारत ने क्रिकेट मैच जीता बारिश के बाद"},
    {"docid": "3#0", "title": "संविधान", "text": "भारत का संविधान 1950 में लागू हुआ"},
    {"docid": "4#0", "title": "mausam", "text": "kal ka mausam saaf rahega"},
    {"docid": "5#0", "title": "नदी", "text": "गंगा भारत की सबसे लंबी नदी है"},
]


def make_index(tmp_path):
    path = tmp_path / "corpus.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for doc in DOCS:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    index, titles, texts = build_index(str(path))
    return index


def test_postings_are_sorted_and_counted(tmp_path):
    index = make_index(tmp_path)
    zone = index.zones["all"]
    docs, tfs = zone.postings("भारत")
    assert list(docs) == sorted(docs)
    assert len(docs) == 3
    assert zone.get_df("भारत") == 3


def test_bm25_matches_formula(tmp_path):
    index = make_index(tmp_path)
    zone = index.zones["all"]
    scores = np.zeros(index.num_docs)
    bm25_zone(zone, ["बारिश"], scores, 1.0, 1.2, 0.75)
    df = zone.get_df("बारिश")
    idf = math.log(1 + (index.num_docs - df + 0.5) / (df + 0.5))
    doc = 0
    tf = 1
    length = zone.doc_lengths[doc]
    expected = idf * tf * 2.2 / (tf + 1.2 * (1 - 0.75 + 0.75 * length / zone.avg_length))
    assert abs(scores[doc] - expected) < 1e-9


def test_bm25_ranking_matches_reference_library(tmp_path):
    # rank_bm25 uses a slightly different idf, but for a one-word query the ranking must be the same
    index = make_index(tmp_path)
    zone = index.zones["all"]
    corpus_terms = []
    for doc_number in range(index.num_docs):
        terms = []
        for term in zone.terms:
            docs, tfs = zone.postings(term)
            for i in range(len(docs)):
                if docs[i] == doc_number:
                    terms.extend([term] * int(tfs[i]))
        corpus_terms.append(terms)
    reference = BM25Okapi(corpus_terms, k1=1.2, b=0.75)
    ours = np.zeros(index.num_docs)
    bm25_zone(zone, ["बारिश"], ours, 1.0, 1.2, 0.75)
    theirs = reference.get_scores(["बारिश"])
    assert list(np.argsort(-ours)[:2]) == list(np.argsort(-theirs)[:2])


def test_dhvani_zone_finds_roman_query(tmp_path):
    index = make_index(tmp_path)
    query = parse_query("mausam")
    scores = np.zeros(index.num_docs)
    bm25_zone(index.zones["dhvani"], query["dhvani_keys"], scores, 1.0, 1.2, 0.75)
    found = [index.doc_ids[d] for d, _ in top_k(scores, 5)]
    assert "1#0" in found and "4#0" in found


def test_pooled_df_is_never_smaller(tmp_path):
    index = make_index(tmp_path)
    query = parse_query("mausam")
    table = pooled_df_table(query["surface_terms"], query["term_keys"], index.zones["dhvani"], index.zones["all"])
    assert table["mausam"] >= index.zones["all"].get_df("mausam")
    assert table["mausam"] == 2      # one Devanagari doc + one Roman doc


def test_boolean_and_skips(tmp_path):
    index = make_index(tmp_path)
    zone = index.zones["all"]
    assert boolean_search(zone, "भारत AND बारिश") == [1]
    assert boolean_search(zone, "भारत AND NOT क्रिकेट") == [2, 4]
    big1 = list(range(0, 1000, 2))
    big2 = list(range(0, 1000, 100))   # a much sparser list: skips help here
    assert intersect(big1, big2) == intersect_with_skips(big1, big2)
    plain = [0]
    skips = [0]
    intersect(big1, big2, plain)
    intersect_with_skips(big1, big2, skips)
    assert skips[0] < plain[0]


def test_phrase_query_uses_positions(tmp_path):
    index = make_index(tmp_path)
    zone = index.zones["all"]
    assert phrase_search(zone, "भारत का संविधान") == [2]
    assert phrase_search(zone, "संविधान भारत") == []


def test_proximity():
    assert smallest_window([[1, 10], [3, 20]]) == 3
    assert smallest_window([[5], [5]]) == 1


def test_proximity_score_in_index(tmp_path):
    index = make_index(tmp_path)
    query = parse_query("kal mausam")
    # doc 3 ("kal ka mausam ...") has both words two positions apart
    score, window = proximity_score(index.zones["dhvani"], query["dhvani_keys"], 3)
    assert window >= 2 and score > 0


def test_tfidf_cosine_is_bounded(tmp_path):
    index = make_index(tmp_path)
    scores = tfidf_cosine(index.zones["all"], ["भारत", "संविधान"])
    assert scores.max() <= 1.0 + 1e-9
    assert int(np.argmax(scores)) == 2


def test_lnc_document_vectors_are_unit_length(tmp_path):
    # A query made of ALL the terms of a document, each once, must give cosine = 1 only if
    # the document has every term once; in general the doc vector itself must have length 1.
    index = make_index(tmp_path)
    zone = index.zones["all"]
    doc = 1
    total = 0.0
    for term in zone.terms:
        docs, tfs = zone.postings(term)
        for i in range(len(docs)):
            if docs[i] == doc:
                weight = (1.0 + math.log10(tfs[i])) / zone.lnc_norms[doc]
                total += weight * weight
    assert abs(total - 1.0) < 1e-9


def test_rrf_and_topk():
    fused = rrf([[1, 2, 3], [2, 3, 1]], k=60, top=3)
    assert fused[0][0] == 2   # ranks 2 and 1 beat ranks 1 and 3
    scores = np.array([0.0, 3.0, 1.0, 2.0])
    assert [doc for doc, _ in top_k(scores, 2)] == [1, 3]


def test_bm25_idf_positive():
    assert bm25_idf(100, 100) > 0
