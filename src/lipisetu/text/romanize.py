"""Make Roman (Hinglish) versions of Devanagari text, for synthetic query variants.

F2 "standard romanisation": one fixed Hinglish spelling convention
    (ा -> a, ी -> i, the silent final "a" is dropped: कमल -> kamal).
F3 "casual romanisation": F2 plus random spelling changes that real people
    make (a -> aa, i -> ee, v -> w, j -> z, dropping the h in kh/bh ...).
    The random generator uses a fixed seed, so F3 is the same on every run.

I wrote this converter myself (instead of using a library) so the spelling
convention is under my control and looks like what people actually type.
"""
import random
import unicodedata

CONSONANTS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "ळ": "l", "व": "v",
    "श": "sh", "ष": "sh", "स": "s", "ह": "h",
    "क़": "q", "ख़": "kh", "ग़": "g", "ज़": "z", "फ़": "f", "ड़": "r", "ढ़": "rh", "य़": "y",
}

# Consonant + nukta written as two characters (after NFD-style splitting)
NUKTA_FORMS = {"क": "q", "ख": "kh", "ग": "g", "ज": "z", "फ": "f", "ड": "r", "ढ": "rh", "य": "y"}

INDEPENDENT_VOWELS = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऋ": "ri", "ऑ": "o", "ऍ": "e",
}

VOWEL_SIGNS = {
    "ा": "a", "ि": "i", "ी": "i", "ु": "u", "ू": "u", "े": "e", "ै": "ai",
    "ो": "o", "ौ": "au", "ृ": "ri", "ॉ": "o", "ॅ": "e",
}

VIRAMA = "्"
NUKTA = "़"
ANUSVARA = "ं"
CHANDRABINDU = "ँ"
VISARGA = "ः"
DIGITS = "०१२३४५६७८९"


def word_to_units(word):
    """Split a Devanagari word into units [consonant_roman, vowel_roman, vowel_is_inherent]."""
    units = []
    i = 0
    while i < len(word):
        ch = word[i]
        if ch in CONSONANTS:
            roman = CONSONANTS[ch]
            if i + 1 < len(word) and word[i + 1] == NUKTA and ch in NUKTA_FORMS:
                roman = NUKTA_FORMS[ch]
                i += 1
            nxt = word[i + 1] if i + 1 < len(word) else ""
            if nxt == VIRAMA:
                units.append([roman, "", False])
                i += 2
                continue
            if nxt in VOWEL_SIGNS:
                units.append([roman, VOWEL_SIGNS[nxt], False])
                i += 2
                continue
            units.append([roman, "a", True])   # inherent "a"
            i += 1
        elif ch in INDEPENDENT_VOWELS:
            vowel = INDEPENDENT_VOWELS[ch]
            # Inside a word people write the short form: हुआ -> hua, नई -> nai (not huaa, naee)
            if len(units) > 0:
                vowel = vowel.replace("aa", "a").replace("ee", "i").replace("oo", "u")
            units.append(["", vowel, False])
            i += 1
        elif ch == ANUSVARA or ch == CHANDRABINDU:
            units.append(["NASAL", "", False])
            i += 1
        elif ch == VISARGA:
            units.append(["h", "", False])
            i += 1
        elif ch in DIGITS:
            units.append([str(DIGITS.index(ch)), "", False])
            i += 1
        else:
            i += 1
    return units


def delete_schwas(units):
    """Hindi drops some inherent 'a' sounds when speaking (schwa deletion).

    Rule 1: the inherent 'a' at the end of a word is dropped (कमल -> kamal).
    Rule 2: an inherent 'a' between a vowel and a consonant that has its own
            vowel sign is dropped (समझना -> samajhna).
    """
    consonant_count = 0
    for unit in units:
        if unit[0] != "" and unit[0] != "NASAL":
            consonant_count += 1
    last = len(units) - 1
    if consonant_count >= 2 and last >= 0 and units[last][2]:
        # Keep the 'a' after a cluster ending in r, y or v (मंत्र -> mantra, वाक्य -> vakya)
        after_cluster = last >= 1 and units[last - 1][1] == "" and units[last - 1][0] not in ["", "NASAL"]
        if not (after_cluster and units[last][0] in ["r", "y", "v"]):
            units[last][1] = ""
    for i in range(1, len(units) - 1):
        before = units[i - 1]
        after = units[i + 1]
        if units[i][2] and before[1] != "" and after[0] not in ["", "NASAL"] and not after[2] and after[1] != "":
            units[i][1] = ""
    return units


def romanize_word(word):
    """Standard romanisation of one Devanagari word."""
    word = unicodedata.normalize("NFD", word)
    units = delete_schwas(word_to_units(word))
    parts = []
    for i in range(len(units)):
        consonant, vowel, inherent = units[i]
        if consonant == "NASAL":
            nxt = units[i + 1][0] if i + 1 < len(units) else ""
            if nxt[:1] in ["p", "b", "m"]:
                parts.append("m")
            else:
                parts.append("n")
            continue
        parts.append(consonant + vowel)
    return "".join(parts)


def is_devanagari_word(word):
    for ch in word:
        if "ऀ" <= ch <= "ॿ":
            return True
    return False


def romanize(text):
    """F2: standard romanisation of a whole text (non-Devanagari words are kept)."""
    out_words = []
    for word in text.split():
        if is_devanagari_word(word):
            out_words.append(romanize_word(word))
        else:
            out_words.append(word.lower())
    return " ".join(out_words)


# Casual spelling changes: (from, to). Each one is applied with probability p.
CASUAL_CHANGES = [
    ("a", "aa"), ("i", "ee"), ("u", "oo"), ("ee", "i"), ("oo", "u"),
    ("v", "w"), ("w", "v"), ("j", "z"), ("sh", "s"), ("ph", "f"),
    ("kh", "k"), ("gh", "g"), ("bh", "b"), ("dh", "d"), ("th", "t"),
    ("ai", "e"), ("au", "o"), ("e", "ai"),
]


def casual_word(word, rng, p):
    """With probability p, make ONE casual spelling change in the word."""
    if rng.random() >= p:
        return word
    # Which changes are possible for this word?
    possible = []
    for old, new in CASUAL_CHANGES:
        if old in word:
            possible.append((old, new))
    if len(possible) == 0:
        return word
    old, new = possible[rng.randrange(len(possible))]
    # Change one random occurrence of 'old'
    positions = []
    start = word.find(old)
    while start != -1:
        positions.append(start)
        start = word.find(old, start + 1)
    pos = positions[rng.randrange(len(positions))]
    return word[:pos] + new + word[pos + len(old):]


def casual_romanize(text, rng, p=0.3):
    """F3: standard romanisation + random casual spelling changes."""
    words = romanize(text).split()
    out_words = []
    for word in words:
        out_words.append(casual_word(word, rng, p))
    return " ".join(out_words)


def make_rng(seed):
    return random.Random(seed)
