"""Dhvani key: a cross-script phonetic key for Hindi (Lecture: Term vocabulary - Soundex).

Dhvani (ध्वनि) means "sound". The idea is the same as Soundex: words that
sound alike get the same code. Unlike Soundex, it works on BOTH scripts, so
"mausam", "mosam", "mousam" and "मौसम" all get the key "MSM".

Rules (each one can be switched off for the ablation experiment):
  1. Each consonant sound maps to one class letter (क/k/q -> K, स/श/ष/s/sh -> S, ...)
  2. merge_aspiration:  aspirated = unaspirated  (ख = क, kh = k, भ = ब, bh = b)
  3. merge_retroflex:   ट/त -> T, ड/द -> D, ण/न -> N (Roman spelling can't show the difference)
  4. drop_vowels:       vowels are dropped, except a vowel at the start (-> "A").
                        This also handles the silent "a" (कमल is written k-m-l but typed "kamal")
  5. merge_wv / merge_zj / merge_fp:  w = v, z = j, f = ph
  6. nasal_rule:        anusvara (ं) and m before a consonant -> N (संबंध = sambandh, संविधान = samvidhan)
  7. collapse_doubles:  repeated classes collapse (pakka -> PK, पक्का -> PK)
Unlike English Soundex, the key is NOT cut to 4 characters, because Hindi
words are short and cutting them merges too many different words.
"""

DEFAULT_RULES = {
    "merge_aspiration": True,
    "merge_retroflex": True,
    "drop_vowels": True,
    "merge_wv": True,
    "merge_zj": True,
    "merge_fp": True,
    "nasal_rule": True,
    "collapse_doubles": True,
}

# Keys shorter than this are too ambiguous ("K" would match hundreds of words)
MIN_KEY_LENGTH = 2

# ---------------- Devanagari tables ----------------
# consonant -> (class, is_aspirated, is_retroflex)
DEVANAGARI_CONSONANTS = {
    "क": ("K", False, False), "ख": ("K", True, False),
    "ग": ("G", False, False), "घ": ("G", True, False),
    "ङ": ("N", False, False),
    "च": ("C", False, False), "छ": ("C", True, False),
    "ज": ("J", False, False), "झ": ("J", True, False),
    "ञ": ("N", False, False),
    "ट": ("T", False, True), "ठ": ("T", True, True),
    "ड": ("D", False, True), "ढ": ("D", True, True),
    "ण": ("N", False, True),
    "त": ("T", False, False), "थ": ("T", True, False),
    "द": ("D", False, False), "ध": ("D", True, False),
    "न": ("N", False, False),
    "प": ("P", False, False), "फ": ("P", True, False),
    "ब": ("B", False, False), "भ": ("B", True, False),
    "म": ("M", False, False),
    "य": ("Y", False, False), "र": ("R", False, False),
    "ल": ("L", False, False), "ळ": ("L", False, True),
    "व": ("V", False, False),
    "श": ("S", False, False), "ष": ("S", False, False), "स": ("S", False, False),
    "ह": ("H", False, False),
}

# Vowel classes, used only when drop_vowels is switched off
DEVANAGARI_VOWELS = {
    "अ": "a", "आ": "a", "ा": "a",
    "इ": "i", "ई": "i", "ि": "i", "ी": "i",
    "उ": "u", "ऊ": "u", "ु": "u", "ू": "u",
    "ए": "e", "ऐ": "e", "े": "e", "ै": "e", "ऍ": "e", "ॅ": "e",
    "ओ": "o", "औ": "o", "ो": "o", "ौ": "o", "ऑ": "o", "ॉ": "o",
}

VOCALIC_R = ["ऋ", "ृ"]   # sounds like "ri", so it becomes R
ANUSVARA = "ं"
VIRAMA = "्"

# ---------------- Roman tables ----------------
ROMAN_TRIGRAPHS = {"chh": ("C", True)}
ROMAN_DIGRAPHS = {
    "kh": ("K", True), "gh": ("G", True), "ch": ("C", False), "jh": ("J", True),
    "th": ("T", True), "dh": ("D", True), "ph": ("P", True), "bh": ("B", True),
    "sh": ("S", False), "ck": ("K", False),
}
ROMAN_LETTERS = {
    "k": "K", "q": "K", "c": "K", "g": "G", "j": "J", "z": "Z", "t": "T", "d": "D",
    "n": "N", "p": "P", "f": "F", "b": "B", "m": "M", "y": "Y", "r": "R", "l": "L",
    "v": "V", "w": "W", "s": "S", "h": "H",
}
ROMAN_VOWELS = {"a": "a", "e": "e", "i": "i", "o": "o", "u": "u"}


def is_roman_consonant(ch):
    return ch != "" and "a" <= ch <= "z" and ch not in "aeiou"


def consonant_class(letter, aspirated, rules):
    """Turn a consonant class into its final form, depending on the rules."""
    if aspirated and not rules["merge_aspiration"]:
        return letter + "h"
    return letter


def roman_letter_class(letter, rules):
    """Class for a single Roman consonant letter, applying the merge rules."""
    cls = ROMAN_LETTERS[letter]
    if cls == "W" and rules["merge_wv"]:
        cls = "V"
    if cls == "Z" and rules["merge_zj"]:
        cls = "J"
    if cls == "F" and rules["merge_fp"]:
        cls = "P"
    return cls


def devanagari_units(token, rules):
    """Turn a Devanagari token into a list of sound units, e.g. मौसम -> [M, o, S, M]."""
    units = []
    i = 0
    while i < len(token):
        ch = token[i]
        # Special case: ज्ञ is pronounced "gy" (gyan = ज्ञान)
        if ch == "ज" and token[i + 1:i + 3] == VIRAMA + "ञ":
            units.append("G")
            units.append("Y")
            i += 3
            continue
        if ch in DEVANAGARI_CONSONANTS:
            letter, aspirated, retroflex = DEVANAGARI_CONSONANTS[ch]
            if retroflex and not rules["merge_retroflex"]:
                letter = letter + "r"
            units.append(consonant_class(letter, aspirated, rules))
        elif ch in VOCALIC_R:
            units.append("R")
        elif ch == ANUSVARA:
            units.append("N" if rules["nasal_rule"] else "n")
        elif ch in DEVANAGARI_VOWELS:
            units.append(DEVANAGARI_VOWELS[ch])
        elif "0" <= ch <= "9":
            units.append(ch)
        # virama, visarga and other signs add no sound unit
        i += 1
    return units


def roman_units(token, rules):
    """Turn a Roman token into a list of sound units, e.g. mausam -> [M, a, u, S, a, M]."""
    units = []
    i = 0
    while i < len(token):
        three = token[i:i + 3]
        two = token[i:i + 2]
        ch = token[i]
        if three in ROMAN_TRIGRAPHS:
            letter, aspirated = ROMAN_TRIGRAPHS[three]
            units.append(consonant_class(letter, aspirated, rules))
            i += 3
        elif two in ROMAN_DIGRAPHS:
            letter, aspirated = ROMAN_DIGRAPHS[two]
            units.append(consonant_class(letter, aspirated, rules))
            i += 2
        elif ch == "x":
            units.append("K")
            units.append("S")
            i += 1
        elif ch == "m" and rules["nasal_rule"] and is_roman_consonant(token[i + 1:i + 2]):
            # "sambandh", "samvidhan": m before a consonant is the same nasal
            # sound as the anusvara in संबंध, संविधान
            units.append("N")
            i += 1
        elif ch in ROMAN_LETTERS:
            units.append(roman_letter_class(ch, rules))
            i += 1
        elif ch in ROMAN_VOWELS:
            units.append(ROMAN_VOWELS[ch])
            i += 1
        else:
            units.append(ch)  # digits
            i += 1
    return units


def is_vowel_unit(unit):
    return unit in ["a", "e", "i", "o", "u"]


def units_to_key(units, rules):
    """Apply the vowel rule and the double-collapse rule, then join into a key."""
    classes = []
    for position in range(len(units)):
        unit = units[position]
        if is_vowel_unit(unit):
            if position == 0:
                classes.append("A" if rules["drop_vowels"] else unit.upper())
            elif not rules["drop_vowels"]:
                classes.append(unit.upper())
            continue
        if unit == "n":
            unit = "N"
        if rules["collapse_doubles"] and len(classes) > 0 and classes[-1] == unit:
            continue
        classes.append(unit)
    return "".join(classes), len(classes)


def dhvani_key(token, rules=None):
    """Return the Dhvani key of one normalised token ('' if the key is too short)."""
    if rules is None:
        rules = DEFAULT_RULES
    if token.isdigit():
        return ""
    is_deva = False
    for ch in token:
        if "ऀ" <= ch <= "ॿ":
            is_deva = True
            break
    if is_deva:
        units = devanagari_units(token, rules)
    else:
        units = roman_units(token, rules)
    key, length = units_to_key(units, rules)
    if length < MIN_KEY_LENGTH:
        return ""
    return key


def rules_without(rule_name):
    """A copy of the default rules with one rule switched off (for the ablation)."""
    rules = dict(DEFAULT_RULES)
    rules[rule_name] = False
    return rules
