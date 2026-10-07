"""Script-aware tokenizer (Lecture: Term vocabulary - tokenisation).

Why not just use re.findall(r"\\w+", text)? Because in Python, \\w does not
match Devanagari vowel signs (matras) or the virama. So "हिन्दी" would be cut
into ['ह', 'न', 'द']. Instead I use explicit Unicode ranges:
  - Devanagari block: U+0900 to U+097F (danda marks are removed by normalisation)
  - Roman letters and digits: a-z and 0-9 (text is lower-cased first)
"""
import re

from lipisetu.text.normalize import normalize

TOKEN_PATTERN = re.compile("[ऀ-ॣ०-ॿ]+|[a-z0-9]+")


def tokenize(text):
    """Normalise the text and split it into tokens."""
    text = normalize(text)
    return TOKEN_PATTERN.findall(text)
