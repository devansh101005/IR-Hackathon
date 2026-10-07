"""Make the figures for the report from the CSV/JSON files in results/.

Usage: python scripts/make_plots.py
Outputs: results/fig_*.png
Every number in a figure is read from results/ (nothing is typed in by hand).
Style: matplotlib's default look (default colours, black text); only the resolution is raised for the PDF.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lipisetu import config

SERIES = ["tab:blue", "tab:orange", "tab:green"]
INK = "black"
MUTED = "black"
GRID = "#b0b0b0"
SYSTEM_ORDER = ["B0", "B1", "B1N", "B2", "V1", "S0", "S1", "S2", "S3", "D0", "D1", "H1", "L1", "G1"]
FORM_NAMES = {"F1": "Devanagari", "F2": "Standard Roman", "F3": "Casual Roman"}


def style():
    # Keep matplotlib's default style; only make the images sharp enough for print
    plt.rcParams.update({"figure.dpi": 200, "savefig.bbox": "tight", "font.size": 10})


def read_csv(name):
    path = os.path.join(config.RESULTS_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(name):
    path = os.path.join(config.RESULTS_DIR, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def metric(rows, system, form, name):
    for row in rows:
        if row["system"] == system and row["query_form"] == form and row["metric"] == name:
            return float(row["value"])
    return None


def save(fig, name):
    path = os.path.join(config.RESULTS_DIR, name)
    fig.savefig(path)
    plt.close(fig)
    print("saved", path)


def plot_systems(rows):
    systems = [s for s in SYSTEM_ORDER if metric(rows, s, "F1", "ndcg@10") is not None]
    if not systems:
        return
    fig, ax = plt.subplots(figsize=(10, 3.6))
    width = 0.26
    for j, form in enumerate(["F1", "F2", "F3"]):
        xs = [i + (j - 1) * (width + 0.02) for i in range(len(systems))]
        values = [metric(rows, s, form, "ndcg@10") or 0 for s in systems]
        ax.bar(xs, values, width=width, color=SERIES[j], label=FORM_NAMES[form], zorder=2)
    ax.set_xticks(range(len(systems)))
    ax.set_xticklabels(systems)
    ax.set_ylabel("nDCG@10")
    ax.set_title("Effectiveness by system and query script (350 dev queries)")
    ax.legend(ncol=3, loc="upper left", bbox_to_anchor=(0, 1.0))
    ax.set_ylim(0, max(0.1, ax.get_ylim()[1] * 1.12))
    save(fig, "fig_ndcg_by_system.png")


def plot_script_gap(inv_rows):
    systems = [s for s in SYSTEM_ORDER if any(r["system"] == s for r in inv_rows)]
    if not systems:
        return
    fig, ax = plt.subplots(figsize=(10, 3.2))
    width = 0.36
    for j, form in enumerate(["F2", "F3"]):
        values = []
        for s in systems:
            row = [r for r in inv_rows if r["system"] == s][0]
            values.append(float(row.get("gap_" + form) or 0))
        xs = [i + (j - 0.5) * (width + 0.02) for i in range(len(systems))]
        ax.bar(xs, values, width=width, color=SERIES[j + 1], label=FORM_NAMES[form], zorder=2)
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_xticks(range(len(systems)))
    ax.set_xticklabels(systems)
    ax.set_ylabel("nDCG@10 lost vs Devanagari")
    ax.set_title("Script Gap: how much worse Roman-script queries are served (lower is better)")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.2)
    ax.legend(ncol=2, loc="upper left")
    save(fig, "fig_script_gap.png")


def plot_consistency(inv_rows):
    systems = [s for s in SYSTEM_ORDER if any(r["system"] == s for r in inv_rows)]
    if not systems:
        return
    values = [float([r for r in inv_rows if r["system"] == s][0]["csc@10"]) for s in systems]
    fig, ax = plt.subplots(figsize=(10, 2.8))
    ax.bar(range(len(systems)), values, width=0.5, color=SERIES[0], zorder=2)
    for i, v in enumerate(values):
        if systems[i] in ["B2", "S3", "G1"]:
            ax.text(i, v + 0.015, "%.2f" % v, ha="center", color=INK, fontsize=9)
    ax.set_xticks(range(len(systems)))
    ax.set_xticklabels(systems)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("CSC@10 (RBO)")
    ax.set_title("Cross-script consistency: same top-10 for every script = 1.0")
    save(fig, "fig_consistency.png")


def plot_budget(rows, point):
    if not rows:
        return
    rows = sorted(rows, key=lambda r: float(r["neural_share"]))
    xs = [100 * float(r["neural_share"]) for r in rows]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot(xs, [float(r["gate_ndcg@10"]) for r in rows], color=SERIES[0], linewidth=2, label="learned gate")
    ax.plot(xs, [float(r["random_ndcg@10"]) for r in rows], color=SERIES[1], linewidth=2, label="random gate, same budget")
    if point:
        ax.scatter([100 * point["gate_neural_share"]], [point["gate_ndcg@10"]], s=40, color=SERIES[0],
                   edgecolor="white", linewidth=1.5, zorder=3)
        ax.annotate("threshold chosen on train", (100 * point["gate_neural_share"], point["gate_ndcg@10"]),
                    xytext=(8, -16), textcoords="offset points", color=INK, fontsize=9)
    ax.set_xlabel("% of queries that run the neural stage")
    ax.set_ylabel("nDCG@10")
    ax.set_title("Quality vs neural compute (dev, all forms)")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.legend(loc="lower left")
    save(fig, "fig_budget_curve.png")


def plot_ablation(rows):
    if not rows:
        return
    names = [r["variant"] for r in rows][::-1]
    values = [float(r["csc@10"]) for r in rows][::-1]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.barh(range(len(names)), values, height=0.5, color=SERIES[0], zorder=2)
    for i, v in enumerate(values):
        ax.text(v + 0.003, i, "%.3f" % v, va="center", color=INK, fontsize=8.5)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_xlim(min(values) * 0.9, max(values) * 1.06)
    ax.set_xlabel("CSC@10 (higher = more script-invariant)")
    ax.set_title("Dhvani rule ablation (one rule off at a time)")
    save(fig, "fig_dhvani_ablation.png")


def plot_corpus(zipf_rows, idf_rows):
    if zipf_rows:
        fig, ax = plt.subplots(figsize=(4.8, 3.2))
        ax.loglog([int(r["rank"]) for r in zipf_rows], [int(r["collection_frequency"]) for r in zipf_rows],
                  color=SERIES[0], linewidth=2)
        ax.set_xlabel("rank (log)")
        ax.set_ylabel("collection frequency (log)")
        ax.set_title("Zipf's law on the Hindi corpus")
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        save(fig, "fig_zipf.png")
    if idf_rows:
        fig, ax = plt.subplots(figsize=(4.8, 3.2))
        centers = [(float(r["idf_from"]) + float(r["idf_to"])) / 2 for r in idf_rows]
        widths = [(float(r["idf_to"]) - float(r["idf_from"])) * 0.85 for r in idf_rows]
        ax.bar(centers, [int(r["terms"]) for r in idf_rows], width=widths, color=SERIES[0], zorder=2)
        ax.set_xlabel("idf = log10(N / df)")
        ax.set_ylabel("vocabulary terms")
        ax.set_title("idf distribution of the vocabulary")
        save(fig, "fig_idf_hist.png")


def main():
    style()
    main_rows = read_csv("main_metrics.csv")
    inv_rows = read_csv("invariance.csv")
    plot_systems(main_rows)
    plot_script_gap(inv_rows)
    plot_consistency(inv_rows)
    plot_budget(read_csv("e10_budget_curve.csv"), read_json("e10_operating_point.json"))
    plot_ablation(read_csv("e5_dhvani_ablation.csv"))
    plot_corpus(read_csv("e3_zipf.csv"), read_csv("e3_idf_hist.csv"))


if __name__ == "__main__":
    main()
