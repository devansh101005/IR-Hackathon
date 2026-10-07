"""Tests for the text pipeline: normalisation, tokenizer, stemmer, Dhvani, Soundex, romaniser."""
from lipisetu.text.normalize import normalize
from lipisetu.text.tokenize import tokenize
from lipisetu.text.stemmer import stem
from lipisetu.text.dhvani import dhvani_key, rules_without
from lipisetu.text.soundex import soundex_roman
from lipisetu.text.romanize import romanize, casual_romanize, make_rng
from lipisetu.text.script import query_script
from lipisetu.text.stopwords import is_stop_word


def test_hindi_word_is_one_token():
    # Python's \w would split this word at the vowel signs
    assert tokenize("हिन्दी") == ["हिंदी"]


def test_normalisation_rules():
    assert normalize("क़िला") == "किला"            # nukta folded
    assert normalize("हँसी") == normalize("हंसी")   # chandrabindu = anusvara
    assert normalize("सम्बन्ध") == "संबंध"          # half nasal -> anusvara
    assert normalize("२०२४") == "2024"              # Devanagari digits
    assert normalize("BAHUUUT") == "bahut"          # case folding + repeats


def test_tokenizer_mixed_script():
    assert tokenize("kal ka मौसम kaisa है?") == ["kal", "ka", "मौसम", "kaisa", "है"]


def test_stemmer():
    assert stem("लड़के") == stem("लड़कों")
    assert stem("किताबें") == "किताब"
    assert stem("kitaben") == "kitaben"   # Roman tokens are not stemmed


def test_dhvani_matches_across_scripts():
    key = dhvani_key("मौसम")
    assert key == "MSM"
    assert dhvani_key("mausam") == key
    assert dhvani_key("mosam") == key
    assert dhvani_key("mousam") == key


def test_dhvani_more_pairs():
    pairs = [("कल", "kal"), ("हिंदी", "hindi"), ("संबंध", "sambandh"),
             ("कृष्ण", "krishna"), ("ज्ञान", "gyan"), ("फिल्म", "film"),
             ("जिंदगी", "zindagi"), ("पक्का", "pakka"), ("इलाज", "ilaaj")]
    for deva, roman in pairs:
        assert dhvani_key(normalize(deva)) == dhvani_key(roman), (deva, roman)


def test_dhvani_short_keys_are_skipped():
    assert dhvani_key("ka") == ""
    assert dhvani_key("2024") == ""


def test_dhvani_rule_switches_change_keys():
    # Without merging w/v, "vishwa" and "vishva" stop matching
    rules = rules_without("merge_wv")
    assert dhvani_key("vishwa", rules) != dhvani_key("vishva", rules)
    assert dhvani_key("vishwa") == dhvani_key("vishva")


def test_soundex_lecture_examples():
    assert soundex_roman("robert") == "R163"
    assert soundex_roman("rupert") == "R163"
    assert soundex_roman("herman") == "H655"


def test_romanize_standard():
    assert romanize("कल का मौसम") == "kal ka mausam"
    assert romanize("भारत") == "bharat"
    assert romanize("समझना") == "samajhna"
    assert romanize("हुआ नई") == "hua nai"
    assert romanize("मंत्र") == "mantra"


def test_casual_romanize_is_repeatable():
    first = casual_romanize("कल का मौसम कैसा है", make_rng(13))
    second = casual_romanize("कल का मौसम कैसा है", make_rng(13))
    assert first == second


def test_query_script():
    assert query_script(["kal", "ka", "mausam"]) == "roman"
    assert query_script(["कल", "का", "मौसम"]) == "deva"
    assert query_script(["kal", "ka", "मौसम"]) == "mixed"


def test_stop_words():
    assert is_stop_word("का")
    assert is_stop_word("hai")
    assert is_stop_word("the")
    assert not is_stop_word("मौसम")
