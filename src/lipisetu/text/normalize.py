"""Text normalisation for Devanagari and Roman text (Lecture: Term vocabulary - normalisation).

The same Hindi word can be stored as different Unicode sequences, for example
"हिन्दी" (half-n + virama) and "हिंदी" (anusvara). If I don't normalise, these
become two different terms in the index and never match each other.
"""
import re
import unicodedata

NUKTA = "़"
VIRAMA = "्"
ANUSVARA = "ं"
CHANDRABINDU = "ँ"
ZWJ = "‍"
ZWNJ = "‌"
DANDA = "।"
DOUBLE_DANDA = "॥"

# Nasal consonants that are often written as an anusvara instead (न्द = ंद)
NASAL_CONSONANTS = "ङञणनम"

# Devanagari digits ० to ९ become 0 to 9
DEVANAGARI_DIGITS = "०१२३४५६७८९"

# A nasal consonant + virama right before another consonant (क to ह)
HALF_NASAL_PATTERN = re.compile("[" + NASAL_CONSONANTS + "]" + VIRAMA + "(?=[क-ह])")

# 3 or more repeats of the same Roman letter ("bahuuut" -> "bahut")
REPEATED_LETTERS = re.compile(r"([a-z])\1{2,}")


def normalize_devanagari(text):
    """Apply the Devanagari rules. The order matters: NFC must come first."""
    # 1. NFC puts every character into one standard Unicode form.
    #    It also splits letters like क़ into क + nukta, so step 2 can remove the nukta.
    text = unicodedata.normalize("NFC", text)
    # 2. Fold nukta: क़ -> क, ज़ -> ज, फ़ -> फ, ड़ -> ड
    text = text.replace(NUKTA, "")
    # 3. Chandrabindu (ँ) and anusvara (ं) are used interchangeably in practice
    text = text.replace(CHANDRABINDU, ANUSVARA)
    # 4. Remove invisible joiner characters
    text = text.replace(ZWJ, "").replace(ZWNJ, "")
    # 5. Half nasal before a consonant -> anusvara (हिन्दी -> हिंदी, सम्बन्ध -> संबंध)
    text = HALF_NASAL_PATTERN.sub(ANUSVARA, text)
    # 6. Devanagari digits -> ASCII digits
    for i in range(10):
        text = text.replace(DEVANAGARI_DIGITS[i], str(i))
    # 7. Danda marks are sentence punctuation, not part of words
    text = text.replace(DANDA, " ").replace(DOUBLE_DANDA, " ")
    return text


def normalize_roman(text):
    """Case folding and simple clean-up for Roman (Latin) text."""
    text = text.lower()
    text = REPEATED_LETTERS.sub(r"\1", text)
    return text


def normalize(text):
    """Normalise any text: Devanagari rules plus Roman rules."""
    text = normalize_devanagari(text)
    text = normalize_roman(text)
    return text
