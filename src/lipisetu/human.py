"""Load the human query set from the three annotation sheets (queries/human/sheet_*.tsv).

Forms produced:
    F1     the original Devanagari query (for the same 60 qids, as the reference)
    H-R1   romanisation by annotator 1 (devansh)
    H-R2   romanisation by annotator 2 (teammate_a)
    H-R3   romanisation by annotator 3 (teammate_b)
    H-CM   code-mixed version (rows split between the annotators)
    H-EN   English version   (rows split between the annotators)
A form is only included when it has at least one filled-in row.
"""
import os

from lipisetu import config

ANNOTATORS = ["devansh", "teammate_a", "teammate_b"]


def read_sheet(path):
    """Return a list of dicts, one per row of the sheet."""
    rows = []
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            while len(parts) < len(header):
                parts.append("")
            row = {}
            for i in range(len(header)):
                row[header[i]] = parts[i].strip()
            rows.append(row)
    return rows


def usable(text):
    return text != "" and text.upper() != "SKIP"


def load_human_forms():
    folder = os.path.join(config.QUERY_DIR, "human")
    forms = {"F1": {}, "H-R1": {}, "H-R2": {}, "H-R3": {}, "H-CM": {}, "H-EN": {}}
    for number in range(len(ANNOTATORS)):
        path = os.path.join(folder, "sheet_" + ANNOTATORS[number] + ".tsv")
        if not os.path.exists(path):
            continue
        for row in read_sheet(path):
            qid = row["qid"]
            forms["F1"][qid] = row["devanagari"]
            if usable(row.get("roman", "")):
                forms["H-R" + str(number + 1)][qid] = row["roman"]
            if usable(row.get("code_mixed", "")):
                forms["H-CM"][qid] = row["code_mixed"]
            if usable(row.get("english", "")):
                forms["H-EN"][qid] = row["english"]
    result = {}
    for name in forms:
        if len(forms[name]) > 0:
            result[name] = forms[name]
    # Without any human form there is nothing to compare against F1
    if len(result) == 1 and "F1" in result:
        return {}
    return result
