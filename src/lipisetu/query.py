"""Query processing: turn the user's text into the terms each zone needs.

(Lecture: Scoring and result assembly - query parser)
The query goes through the SAME pipeline as the documents.
"""
from indic_transliteration import sanscript

from lipisetu.text.analyzer import analyze, process_token
from lipisetu.text.tokenize import tokenize
from lipisetu.text.script import query_script
from lipisetu.text.soundex import soundex

VIRAMA = "्"


def parse_query(text):
    """Return a dict with everything the scorers need for this query."""
    records = analyze(text)
    surface_terms = []      # stems for the 'all' and 'title' zones
    nostem_terms = []       # unstemmed tokens for the 'nostem' zone
    dhvani_keys = []        # keys for the 'dhvani' zone
    soundex_codes = []      # codes for the 'soundex' zone
    term_keys = {}          # stem -> Dhvani key (for pooled df)
    tokens = []
    for record in records:
        tokens.append(record["token"])
        if record["stop"]:
            continue
        surface_terms.append(record["stem"])
        nostem_terms.append(record["token"])
        if record["dhvani"] != "":
            dhvani_keys.append(record["dhvani"])
            term_keys[record["stem"]] = record["dhvani"]
        code = soundex(record["token"])
        if code != "":
            soundex_codes.append(code)
    return {
        "text": text,
        "records": records,
        "tokens": tokens,
        "script": query_script(tokens),
        "surface_terms": surface_terms,
        "nostem_terms": nostem_terms,
        "dhvani_keys": dhvani_keys,
        "soundex_codes": soundex_codes,
        "term_keys": term_keys,
    }


def transliterate_token(token):
    """Baseline B2: Roman token -> Devanagari with the ITRANS scheme.

    This is what most teams would do. I remove the final virama that ITRANS
    adds to words ending in a consonant ("mausam" -> "मौसम्" -> "मौसम"),
    so the baseline is fair, not a strawman.
    """
    deva = sanscript.transliterate(token, sanscript.ITRANS, sanscript.DEVANAGARI)
    if deva.endswith(VIRAMA):
        deva = deva[:-1]
    return deva


def transliterated_surface_terms(query):
    """Surface terms for B2: Roman tokens are transliterated before stemming."""
    terms = []
    for record in query["records"]:
        if record["stop"]:
            continue
        if record["script"] == "roman":
            deva_tokens = tokenize(transliterate_token(record["token"]))
            for deva in deva_tokens:
                terms.append(process_token(deva)[0])
        else:
            terms.append(record["stem"])
    return terms
