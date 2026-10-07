"""Light Hindi stemmer (Lecture: Term vocabulary - stemming).

Based on the suffix-stripping idea of Ramanathan & Rao (2003), "A Lightweight
Stemmer for Hindi". Hindi nouns and verbs change their ending
(लड़का, लड़के, लड़कों), so I strip the longest matching suffix from a list.
It only works on Devanagari tokens; Roman tokens are left unchanged
(spelling variation in Roman text is handled by the Dhvani key instead).
"""
from lipisetu.text.normalize import normalize_devanagari

# Suffixes grouped by length (in Unicode characters), longest first.
SUFFIX_GROUPS = [
    ["ाएंगी", "ाएंगे", "ाऊंगी", "ाऊंगा", "ाइयाँ", "ाइयों", "ाइयां"],
    ["ाएगी", "ाएगा", "ाओगी", "ाओगे", "एंगी", "ेंगी", "एंगे", "ेंगे", "ूंगी", "ूंगा",
     "ातीं", "नाओं", "नाएं", "ताओं", "ताएं", "ियाँ", "ियों", "ियां"],
    ["ाकर", "ाइए", "ाईं", "ाया", "ेगी", "ेगा", "ोगी", "ोगे", "ाने", "ाना", "ाते",
     "ाती", "ाता", "तीं", "ाओं", "ाएं", "ुओं", "ुएं", "ुआं"],
    ["कर", "ाओ", "िए", "ाई", "ाए", "ने", "नी", "ना", "ते", "ीं", "ती", "ता", "ाँ",
     "ां", "ों", "ें"],
    ["ो", "े", "ू", "ु", "ी", "ि", "ा"],
]


def normalize_suffixes():
    """Normalise every suffix the same way as the text (e.g. ँ becomes ं)."""
    groups = []
    for group in SUFFIX_GROUPS:
        clean_group = []
        for suffix in group:
            clean = normalize_devanagari(suffix)
            if clean not in clean_group:
                clean_group.append(clean)
        groups.append(clean_group)
    return groups


SUFFIXES = normalize_suffixes()

# Keep at least this many characters, so short words are not destroyed
MIN_STEM_LENGTH = 2


def is_devanagari(token):
    for ch in token:
        if "ऀ" <= ch <= "ॿ":
            return True
    return False


def stem(token):
    """Strip the longest matching suffix from a Devanagari token."""
    if not is_devanagari(token):
        return token
    for group in SUFFIXES:
        for suffix in group:
            if token.endswith(suffix) and len(token) - len(suffix) >= MIN_STEM_LENGTH:
                return token[: len(token) - len(suffix)]
    return token
