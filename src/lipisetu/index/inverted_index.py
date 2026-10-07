"""Positional inverted index with zones (Lectures: Boolean retrieval, Term vocabulary, Scoring).

Classic layout: a DICTIONARY (term -> where its postings start) and one big
POSTINGS FILE (all postings stored one after another), like on disk.

While building, I use normal Python dicts and lists. When building is done,
finish() packs everything into numpy arrays, which saves a lot of memory:

    term_ids[term]  -> t
    term_start[t] .. term_start[t+1]   = this term's postings
    doc_array[i]    = doc number of posting i     (sorted, needed for AND merges)
    tf_array[i]     = term frequency of posting i
    pos_start[i] .. pos_start[i+1]     = positions of posting i inside `positions`

A zone is one field of the document. LipiSetu has these zones:
    all    : title + body, stemmed            (positional; B1/B2 and phrase queries)
    title  : title only, stemmed              (zone weighting)
    dhvani : Dhvani keys of title + body      (positional; cross-script matching, proximity)
    soundex: classic Soundex codes             (comparison system S0)
    nostem : title + body, NOT stemmed        (stemming experiment)
    raw    : whitespace tokens, no processing (naive baseline B0)
"""
import math

import numpy as np


class Zone:
    def __init__(self, name, num_docs, keep_positions):
        self.name = name
        self.num_docs = num_docs
        self.keep_positions = keep_positions
        # Used only while building
        self.build_postings = {}       # term -> list of doc numbers
        self.build_positions = {}      # term -> list of position lists
        self.doc_lengths = np.zeros(num_docs, dtype=np.int32)

    # ---------------- building ----------------
    def add_document(self, doc_number, terms):
        """Add one document. `terms` is a list of (term, position) pairs."""
        self.doc_lengths[doc_number] = len(terms)
        term_positions = {}
        for term, position in terms:
            if term not in term_positions:
                term_positions[term] = []
            term_positions[term].append(position)
        for term in term_positions:
            if term not in self.build_postings:
                self.build_postings[term] = []
                self.build_positions[term] = []
            self.build_postings[term].append(doc_number)
            self.build_positions[term].append(term_positions[term])

    def finish(self):
        """Pack the postings into numpy arrays and compute df, avg length and lnc norms."""
        terms = sorted(self.build_postings.keys())
        self.term_ids = {}
        term_start = [0]
        doc_list = []
        tf_list = []
        pos_start = [0]
        pos_list = []
        for term_id in range(len(terms)):
            term = terms[term_id]
            self.term_ids[term] = term_id
            docs = self.build_postings[term]
            position_lists = self.build_positions[term]
            for i in range(len(docs)):
                doc_list.append(docs[i])
                tf_list.append(len(position_lists[i]))
                if self.keep_positions:
                    pos_list.extend(position_lists[i])
                    pos_start.append(len(pos_list))
            term_start.append(len(doc_list))

        self.terms = terms
        self.term_start = np.array(term_start, dtype=np.int64)
        self.doc_array = np.array(doc_list, dtype=np.int32)
        self.tf_array = np.array(tf_list, dtype=np.int32)
        if self.keep_positions:
            self.pos_start = np.array(pos_start, dtype=np.int64)
            self.positions = np.array(pos_list, dtype=np.int32)
        else:
            self.pos_start = None
            self.positions = None
        self.df = np.diff(self.term_start).astype(np.int32)
        self.avg_length = float(np.mean(self.doc_lengths)) if self.num_docs > 0 else 0.0
        self.compute_lnc_norms()
        # Free the build-time dicts
        self.build_postings = None
        self.build_positions = None

    def compute_lnc_norms(self):
        """Length of each document vector with log tf weights (the 'lnc' in lnc.ltc).

        Must use the same log as retrieval/tfidf.py (log10), otherwise the
        document vectors are not really unit length.
        """
        weights = 1.0 + np.log10(np.maximum(self.tf_array, 1))
        norm_squared = np.zeros(self.num_docs, dtype=np.float64)
        np.add.at(norm_squared, self.doc_array, weights * weights)
        self.lnc_norms = np.sqrt(norm_squared)
        self.lnc_norms[self.lnc_norms == 0] = 1.0

    # ---------------- lookups ----------------
    def has_term(self, term):
        return term in self.term_ids

    def get_df(self, term):
        if term not in self.term_ids:
            return 0
        return int(self.df[self.term_ids[term]])

    def postings(self, term):
        """Return (doc numbers, term frequencies) for a term, as numpy arrays."""
        if term not in self.term_ids:
            empty = np.zeros(0, dtype=np.int32)
            return empty, empty
        term_id = self.term_ids[term]
        start = self.term_start[term_id]
        end = self.term_start[term_id + 1]
        return self.doc_array[start:end], self.tf_array[start:end]

    def positions_in_doc(self, term, doc_number):
        """Positions of a term inside one document ([] if the term is not there)."""
        if not self.keep_positions or term not in self.term_ids:
            return []
        term_id = self.term_ids[term]
        start = self.term_start[term_id]
        end = self.term_start[term_id + 1]
        docs = self.doc_array[start:end]
        # Postings are sorted by doc number, so binary search works
        index = int(np.searchsorted(docs, doc_number))
        if index >= len(docs) or docs[index] != doc_number:
            return []
        posting_number = start + index
        p_start = self.pos_start[posting_number]
        p_end = self.pos_start[posting_number + 1]
        return self.positions[p_start:p_end].tolist()

    def idf(self, term):
        """Plain idf = log10(N / df), as in the lecture (used by tf-idf)."""
        df = self.get_df(term)
        if df == 0:
            return 0.0
        return math.log10(self.num_docs / df)


class InvertedIndex:
    """All zones together, plus the list of MIRACL doc ids."""

    def __init__(self, doc_ids):
        self.doc_ids = doc_ids
        self.num_docs = len(doc_ids)
        self.zones = {}
        self.champions = {}

    def add_zone(self, name, keep_positions):
        self.zones[name] = Zone(name, self.num_docs, keep_positions)
        return self.zones[name]

    def zone(self, name):
        return self.zones[name]
