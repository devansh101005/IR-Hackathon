"""Classic Soundex, as taught in the lecture (Lecture: Term vocabulary - Soundex).

I use it only as a comparison for the Dhvani key. It was designed for English
names: keep the first letter, turn the other letters into digits, drop vowels,
then cut the code to 4 characters. It only works on Roman text, so Devanagari
words are first turned into Roman letters with my romaniser.
"""
from lipisetu.text.romanize import romanize_word

SOUNDEX_DIGITS = {
    "b": "1", "f": "1", "p": "1", "v": "1",
    "c": "2", "g": "2", "j": "2", "k": "2", "q": "2", "s": "2", "x": "2", "z": "2",
    "d": "3", "t": "3",
    "l": "4",
    "m": "5", "n": "5",
    "r": "6",
}


def soundex_roman(word):
    """Soundex code of a Roman word, e.g. 'robert' -> 'R163'."""
    letters = []
    for ch in word.lower():
        if "a" <= ch <= "z":
            letters.append(ch)
    if len(letters) == 0:
        return ""
    first_letter = letters[0].upper()
    # Turn every letter into a digit ('0' for vowels and h, w, y)
    digits = []
    for ch in letters:
        digits.append(SOUNDEX_DIGITS.get(ch, "0"))
    # Collapse repeated digits next to each other
    collapsed = [digits[0]]
    for d in digits[1:]:
        if d != collapsed[-1]:
            collapsed.append(d)
    # Drop the first letter's own digit and all zeros
    code = first_letter
    for d in collapsed[1:]:
        if d != "0":
            code = code + d
    # Pad with zeros or cut to 4 characters
    code = (code + "000")[:4]
    return code


def soundex(token):
    """Soundex for any token: Devanagari is romanised first."""
    if token.isdigit():
        return ""
    is_deva = False
    for ch in token:
        if "ऀ" <= ch <= "ॿ":
            is_deva = True
            break
    if is_deva:
        token = romanize_word(token)
    return soundex_roman(token)
