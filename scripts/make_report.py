"""Build the project report (HTML, then PDF) from the files in results/.

Usage:
    python scripts/make_report.py            -> docs/report/report.html
    node scripts/print_pdf.js                -> docs/report/LipiSetu_report.pdf   (optional; or print the
                                                HTML from a browser: Print -> Save as PDF)
Every number in the report is read from results/, so the report always matches the experiments.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from lipisetu import config

REPORT_DIR = os.path.join(config.PROJECT_ROOT, "docs", "report")
NAMES = {
    "B0": "BM25, raw whitespace tokens", "B1": "BM25 + normalisation + stemming", "B1N": "B1 without stemming",
    "B2": "B1 + Roman→Devanagari transliteration", "V1": "tf-idf lnc.ltc cosine", "S0": "B1 + classic Soundex zone",
    "S1": "B1 + Dhvani zone", "S2": "S1 + pooled df", "S3": "S2 + title zone + proximity",
    "D0": "dense e5-small (int8)", "D1": "dense, SCD query encoder", "H1": "RRF(S3, D1)",
    "L1": "learning to rank", "G1": "gated cascade",
}
ORDER = ["B0", "B1", "B1N", "B2", "V1", "S0", "S1", "S2", "S3", "D0", "D1", "H1", "L1", "G1"]


# ---------------- reading results ----------------
def read_csv(name):
    path = os.path.join(config.RESULTS_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(name):
    path = os.path.join(config.RESULTS_DIR, name)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def metric(rows, system, form, name="ndcg@10"):
    for row in rows:
        if row["system"] == system and row["query_form"] == form and row["metric"] == name:
            return float(row["value"])
    return None


def row_for(rows, key, value):
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def f3(value):
    if value is None or value == "":
        return "–"
    return "%.3f" % float(value)


def pct(value):
    return "%.0f%%" % (100.0 * float(value))


# ---------------- HTML helpers ----------------
def table(headers, rows, numeric_from=1, highlight=None):
    html = "<table><thead><tr>"
    for i in range(len(headers)):
        html += '<th class="%s">%s</th>' % ("num" if i >= numeric_from else "", headers[i])
    html += "</tr></thead><tbody>"
    for row in rows:
        cls = ' class="hl"' if highlight is not None and row[0] in highlight else ""
        html += "<tr%s>" % cls
        for i in range(len(row)):
            html += '<td class="%s">%s</td>' % ("num" if i >= numeric_from else "", row[i])
        html += "</tr>"
    return html + "</tbody></table>"


def figure(path, caption, width="100%"):
    return '<figure><img src="%s" style="width:%s"><figcaption>%s</figcaption></figure>' % (path, width, caption)


# ---------------- sections ----------------
def effectiveness_table(main):
    rows = []
    for s in ORDER:
        if metric(main, s, "F1") is None:
            continue
        rows.append([s, NAMES[s], f3(metric(main, s, "F1")), f3(metric(main, s, "F2")), f3(metric(main, s, "F3")),
                     f3(metric(main, s, "F1", "p@5")), f3(metric(main, s, "F1", "recall@100")),
                     f3(metric(main, s, "F3", "recall@100"))])
    return table(["", "system", "nDCG@10 Deva", "nDCG@10 Roman", "nDCG@10 casual", "P@5 Deva", "R@100 Deva",
                  "R@100 casual"], rows, numeric_from=2, highlight=["S3", "G1"])


def invariance_table(inv):
    rows = []
    for s in ORDER:
        r = row_for(inv, "system", s)
        if not r:
            continue
        rows.append([s, NAMES[s], f3(r.get("gap_F2")), f3(r.get("gap_F3")), f3(r.get("csc@10")), f3(r.get("worst_ndcg@10"))])
    return table(["", "system", "Script Gap Roman", "Script Gap casual", "CSC@10 (RBO)", "worst-script nDCG@10"],
                 rows, numeric_from=2, highlight=["S3", "G1"])


def efficiency_rows(eff):
    rows = []
    for s in ORDER:
        r = row_for(eff, "system", s)
        if r:
            rows.append([s, NAMES[s], "%.1f" % float(r["median_ms"]), "%.1f" % float(r["p95_ms"])])
    return table(["", "system", "median ms", "p95 ms"], rows, numeric_from=2)


def ablation_table(rows_in):
    rows = []
    for r in rows_in:
        rows.append([r["variant"], "{:,}".format(int(r["distinct_keys"])), "%.2f" % float(r["surface_words_per_key"]),
                     f3(r["ndcg@10_F1"]), f3(r["ndcg@10_F2"]), f3(r["ndcg@10_F3"]), f3(r["csc@10"])])
    return table(["variant", "keys", "words/key", "nDCG Deva", "nDCG Roman", "nDCG casual", "CSC@10"], rows,
                 highlight=["all rules (Dhvani)"])


def mixed_table(mixed):
    rows = []
    for s in ["B1", "B2", "S1", "S2", "S3"]:
        if metric(mixed, s, "F1") is None:
            continue
        rows.append([s, NAMES[s], f3(metric(mixed, s, "F1")), f3(metric(mixed, s, "F2")), f3(metric(mixed, s, "F3"))])
    return table(["", "system", "nDCG Deva", "nDCG Roman", "nDCG casual"], rows, numeric_from=2, highlight=["S2"])


def idf_table(examples):
    rows = []
    for r in examples[:8]:
        rows.append(['<span lang="hi">%s</span> / %s' % (r["word"], r["roman"]), r["dhvani_key"],
                     "{:,}".format(int(r["df_devanagari"])), "{:,}".format(int(r["df_roman"])),
                     "{:,}".format(int(r["df_pooled"])), "%.2f" % float(r["idf_devanagari"]),
                     "%.2f" % float(r["idf_roman"]), "%.2f" % float(r["idf_pooled"])])
    return table(["word", "key", "df Deva", "df Roman", "df pooled", "idf Deva", "idf Roman", "idf pooled"], rows,
                 numeric_from=2)


def eff_structures_table(rows_in):
    rows = []
    for r in rows_in:
        rows.append([r["experiment"], r["variant"], r.get("median_ms") or "–", r.get("ndcg@10") or "–",
                     r.get("comparisons") or "–", r.get("docs_scored") or "–", r.get("overlap@100_with_exact") or "–"])
    return table(["experiment", "variant", "median ms", "nDCG@10", "comparisons", "docs scored", "overlap@100"],
                 rows, numeric_from=2)


def significance_table(rows_in):
    rows = []
    for r in rows_in:
        if r["set"] != "dev":
            continue
        rows.append(["%s vs %s" % (r["system_a"], r["system_b"]), r["form"], f3(r["ndcg_a"]), f3(r["ndcg_b"]),
                     "%+.3f" % float(r["difference"]), "%.4f" % float(r["p_value"]),
                     "yes" if r["significant"] == "True" else "no"])
    return table(["comparison", "form", "nDCG A", "nDCG B", "difference", "p-value", "p < 0.05"], rows, numeric_from=2)


def weights_table(rows_in, title):
    rows = [[r["feature"], "%+.3f" % float(r["weight"])] for r in rows_in]
    return table([title, "weight"], rows)


def build():
    main = read_csv("main_metrics.csv")
    inv = read_csv("invariance.csv")
    eff = read_csv("efficiency.csv")
    ablation = read_csv("e5_dhvani_ablation.csv")
    mixed = read_csv("e6_mixed_metrics.csv")
    idf_examples = read_csv("e6_idf_examples.csv")
    structures = read_csv("e11_efficiency.csv")
    significance = read_csv("significance.csv")
    ltr = read_csv("ltr_weights.csv")
    gate_w = read_csv("gate_weights.csv")
    corpus = read_json("e3_corpus_stats.json")
    params = read_json("tuned_params.json")
    scd = read_json("scd_training.json")
    point = read_json("e10_operating_point.json")
    human = read_json("e12_annotator_agreement.json")
    top_terms = read_csv("e3_top_df_terms.csv")
    length_bias = read_json("e13_length_bias.json")
    mixed_inv = read_csv("e6_mixed_invariance.csv")

    b2 = row_for(inv, "system", "B2")
    s1 = row_for(inv, "system", "S1")
    s3 = row_for(inv, "system", "S3")
    numbers = {
        "b1_f1": f3(metric(main, "B1", "F1")), "b1_f2": f3(metric(main, "B1", "F2")),
        "b1n_f1": f3(metric(main, "B1N", "F1")),
        "b2_f2": f3(metric(main, "B2", "F2")), "b2_f3": f3(metric(main, "B2", "F3")),
        "s0_f2": f3(metric(main, "S0", "F2")), "s1_f2": f3(metric(main, "S1", "F2")), "s1_f3": f3(metric(main, "S1", "F3")),
        "s3_f1": f3(metric(main, "S3", "F1")), "s3_f2": f3(metric(main, "S3", "F2")), "s3_f3": f3(metric(main, "S3", "F3")),
        "v1_f1": f3(metric(main, "V1", "F1")),
        "b2_gap3": f3(b2.get("gap_F3")), "s3_gap3": f3(s3.get("gap_F3")), "s1_gap3": f3(s1.get("gap_F3")),
        "b2_csc": f3(b2.get("csc@10")), "s3_csc": f3(s3.get("csc@10")),
        "mixed_s1_f2": f3(metric(mixed, "S1", "F2")), "mixed_s2_f2": f3(metric(mixed, "S2", "F2")),
        "mixed_s1_f3": f3(metric(mixed, "S1", "F3")), "mixed_s2_f3": f3(metric(mixed, "S2", "F3")),
        "d0_f3": f3(metric(main, "D0", "F3")), "d1_f3": f3(metric(main, "D1", "F3")),
        "d0_f1": f3(metric(main, "D0", "F1")), "d1_f1": f3(metric(main, "D1", "F1")),
        "h1_f1": f3(metric(main, "H1", "F1")), "h1_f3": f3(metric(main, "H1", "F3")),
        "l1_f1": f3(metric(main, "L1", "F1")), "l1_f3": f3(metric(main, "L1", "F3")),
        "g1_f1": f3(metric(main, "G1", "F1")), "g1_f3": f3(metric(main, "G1", "F3")),
        "g1_f2": f3(metric(main, "G1", "F2")), "l1_f2": f3(metric(main, "L1", "F2")), "h1_f2": f3(metric(main, "H1", "F2")),
        "s2_f1": f3(metric(main, "S2", "F1")), "s1_f1": f3(metric(main, "S1", "F1")), "s0_f3": f3(metric(main, "S0", "F3")),
        "s2_gap3": f3(row_for(inv, "system", "S2").get("gap_F3")), "s2_csc": f3(row_for(inv, "system", "S2").get("csc@10")),
        "l1_csc": f3(row_for(inv, "system", "L1").get("csc@10")), "g1_csc": f3(row_for(inv, "system", "G1").get("csc@10")),
        "l1_worst": f3(row_for(inv, "system", "L1").get("worst_ndcg@10")), "b2_worst": f3(b2.get("worst_ndcg@10")),
        "mixed_s1_csc": f3(row_for(mixed_inv, "system", "S1").get("csc@10")),
        "mixed_s2_csc": f3(row_for(mixed_inv, "system", "S2").get("csc@10")),
        "v1_len": str(int(length_bias.get("V1_median_top1_length", 0))),
        "b1_len": str(int(length_bias.get("B1_median_top1_length", 0))),
        "corpus_len": str(int(length_bias.get("corpus_median_length", 0))),
        "op_share": pct(point.get("gate_neural_share", 0)), "op_ndcg": f3(point.get("gate_ndcg@10")),
        "op_sparse": f3(point.get("always_sparse_ndcg@10")), "op_neural": f3(point.get("always_neural_ndcg@10")),
        "op_oracle": f3(point.get("oracle_ndcg@10")), "op_oracle_share": pct(point.get("oracle_neural_share", 0)),
        "g1_ms": "%.1f" % float(row_for(eff, "system", "G1").get("median_ms", 0)),
        "h1_ms": "%.1f" % float(row_for(eff, "system", "H1").get("median_ms", 0)),
        "l1_ms": "%.1f" % float(row_for(eff, "system", "L1").get("median_ms", 0)),
        "s3_ms": "%.1f" % float(row_for(eff, "system", "S3").get("median_ms", 0)),
    }
    from report_text import report_html
    html = report_html(numbers, {
        "effectiveness": effectiveness_table(main), "invariance": invariance_table(inv),
        "efficiency": efficiency_rows(eff), "ablation": ablation_table(ablation), "mixed": mixed_table(mixed),
        "idf": idf_table(idf_examples), "structures": eff_structures_table(structures),
        "significance": significance_table(significance), "ltr": weights_table(ltr, "LTR feature"),
        "gate": weights_table(gate_w, "gate feature"),
    }, corpus, params, scd, point, human, top_terms)
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, "report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("saved", path)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    build()
