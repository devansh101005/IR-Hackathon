"""E12: How differently do people romanise the same Hindi query? (human query set)

For every query that all three annotators romanised:
  - word-level agreement: share of words spelled exactly the same by all three
  - Dhvani agreement:     share of words whose Dhvani KEY is the same for all three
  - character-bigram Jaccard between each pair of annotators (whole query)
  - normalised edit distance between each pair
If Dhvani agreement is much higher than spelling agreement, the key really
removes the spelling variation that people produce.
Output: results/e12_annotator_agreement.json, results/e12_word_examples.csv
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from lipisetu import config
from lipisetu.human import load_human_forms
from lipisetu.text.tokenize import tokenize
from lipisetu.text.dhvani import dhvani_key
from lipisetu.eval.run_eval import write_rows


def bigrams(text):
    text = " " + text + " "
    result = set()
    for i in range(len(text) - 1):
        result.add(text[i:i + 2])
    return result


def jaccard(a, b):
    set_a = bigrams(a)
    set_b = bigrams(b)
    if len(set_a | set_b) == 0:
        return 1.0
    return len(set_a & set_b) / float(len(set_a | set_b))


def edit_distance(a, b):
    """Classic Levenshtein distance with a dynamic-programming table."""
    previous = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        current = [i]
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost))
        previous = current
    return previous[len(b)]


def main():
    forms = load_human_forms()
    names = ["H-R1", "H-R2", "H-R3"]
    for name in names:
        if name not in forms:
            print("annotation sheets are not complete yet (missing", name + ")")
            return
    shared = sorted(set(forms["H-R1"]) & set(forms["H-R2"]) & set(forms["H-R3"]))
    words_total = 0
    words_same_spelling = 0
    words_same_key = 0
    jaccards = []
    distances = []
    examples = []
    for qid in shared:
        texts = [forms[name][qid].lower() for name in names]
        token_lists = [tokenize(t) for t in texts]
        for i in range(3):
            for j in range(i + 1, 3):
                jaccards.append(jaccard(texts[i], texts[j]))
                distances.append(edit_distance(texts[i], texts[j]) / float(max(len(texts[i]), len(texts[j]), 1)))
        # compare word by word only when all three have the same number of words
        if len(token_lists[0]) == len(token_lists[1]) == len(token_lists[2]):
            for position in range(len(token_lists[0])):
                words = [token_lists[k][position] for k in range(3)]
                keys = [dhvani_key(w) for w in words]
                words_total += 1
                if words[0] == words[1] == words[2]:
                    words_same_spelling += 1
                if keys[0] == keys[1] == keys[2]:
                    words_same_key += 1
                if len(set(words)) > 1 and len(examples) < 40:
                    examples.append({"qid": qid, "spellings": " / ".join(words), "dhvani_keys": " / ".join(keys),
                                     "keys_agree": keys[0] == keys[1] == keys[2]})
    result = {
        "queries_with_three_romanisations": len(shared),
        "words_compared": words_total,
        "same_spelling_all_three": round(words_same_spelling / float(max(words_total, 1)), 4),
        "same_dhvani_key_all_three": round(words_same_key / float(max(words_total, 1)), 4),
        "mean_bigram_jaccard": round(sum(jaccards) / max(len(jaccards), 1), 4),
        "mean_normalised_edit_distance": round(sum(distances) / max(len(distances), 1), 4),
    }
    with open(os.path.join(config.RESULTS_DIR, "e12_annotator_agreement.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    write_rows(os.path.join(config.RESULTS_DIR, "e12_word_examples.csv"), examples,
               ["qid", "spellings", "dhvani_keys", "keys_agree"])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
