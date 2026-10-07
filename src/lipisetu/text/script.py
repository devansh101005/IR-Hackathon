"""Script detection for tokens and queries (Lecture: Scoring - query parser).

A query can be Devanagari, Roman (Hinglish or English), or a mix of both.
I detect the script per token, so mixed queries are handled word by word.
"""


def token_script(token):
    """Return 'deva', 'roman' or 'digit' for one token."""
    for ch in token:
        if "ऀ" <= ch <= "ॿ":
            return "deva"
    for ch in token:
        if "a" <= ch <= "z":
            return "roman"
    return "digit"


def query_script(tokens):
    """Return 'deva', 'roman', 'mixed' or 'none' for a list of tokens."""
    has_deva = False
    has_roman = False
    for token in tokens:
        script = token_script(token)
        if script == "deva":
            has_deva = True
        elif script == "roman":
            has_roman = True
    if has_deva and has_roman:
        return "mixed"
    if has_deva:
        return "deva"
    if has_roman:
        return "roman"
    return "none"
