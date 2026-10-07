"""The full text pipeline in one place: text -> tokens -> stems and Dhvani keys.

Both the indexer and the query processor call these functions, so documents
and queries are always processed in exactly the same way.
"""
from lipisetu.text.tokenize import tokenize
from lipisetu.text.stemmer import stem
from lipisetu.text.dhvani import dhvani_key
from lipisetu.text.soundex import soundex
from lipisetu.text.stopwords import is_stop_word
from lipisetu.text.script import token_script

# Cache: the same word appears many times, so I only process it once
_token_cache = {}


def process_token(token):
    """Return (stem, dhvani key) for one normalised token, using the cache."""
    if token not in _token_cache:
        _token_cache[token] = (stem(token), dhvani_key(token))
    return _token_cache[token]


def analyze(text):
    """Run the pipeline and return one record per token (used by --explain)."""
    records = []
    tokens = tokenize(text)
    for position in range(len(tokens)):
        token = tokens[position]
        token_stem, key = process_token(token)
        records.append({
            "position": position,
            "token": token,
            "script": token_script(token),
            "stop": is_stop_word(token),
            "stem": token_stem,
            "dhvani": key,
        })
    return records


def surface_terms(tokens, use_stemming=True):
    """Index terms for a surface zone: (term, position) pairs, stop words removed.

    Positions count ALL tokens, so the gaps left by stop words are kept
    (needed for phrase queries like "भारत का संविधान").
    """
    terms = []
    for position in range(len(tokens)):
        token = tokens[position]
        if is_stop_word(token):
            continue
        if use_stemming:
            terms.append((process_token(token)[0], position))
        else:
            terms.append((token, position))
    return terms


def dhvani_terms(tokens):
    """Index terms for the Dhvani zone: (key, position) pairs."""
    terms = []
    for position in range(len(tokens)):
        token = tokens[position]
        if is_stop_word(token):
            continue
        key = process_token(token)[1]
        if key != "":
            terms.append((key, position))
    return terms


_soundex_cache = {}


def soundex_terms(tokens):
    """Index terms for the Soundex zone (comparison system S0): (code, position) pairs."""
    terms = []
    for position in range(len(tokens)):
        token = tokens[position]
        if is_stop_word(token):
            continue
        if token not in _soundex_cache:
            _soundex_cache[token] = soundex(token)
        code = _soundex_cache[token]
        if code != "":
            terms.append((code, position))
    return terms


def raw_terms(text):
    """Terms for the naive baseline B0: split on spaces, no normalisation at all."""
    terms = []
    words = text.split()
    for position in range(len(words)):
        terms.append((words[position], position))
    return terms
