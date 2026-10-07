"""Command-line interface for LipiSetu.

Examples:
    python -m lipisetu.cli search "kal ka mausam" --system S3 --explain
    python -m lipisetu.cli search "भारत का संविधान कब लागू हुआ" --system B2
    python -m lipisetu.cli boolean "मौसम AND बारिश AND NOT क्रिकेट"
    python -m lipisetu.cli phrase "भारत का संविधान"
    python -m lipisetu.cli compare "bharat ka samvidhan kab lagu hua"
"""
import argparse
import time

from lipisetu.search import SearchEngine
from lipisetu.retrieval.boolean import boolean_search, phrase_search

LINE = "-" * 78


def print_tokens(query):
    print("QUERY   :", query["text"])
    print("SCRIPT  :", query["script"])
    print(LINE)
    print("%-4s %-16s %-6s %-5s %-16s %s" % ("pos", "token", "script", "stop", "stem", "dhvani key"))
    for r in query["records"]:
        print("%-4d %-16s %-6s %-5s %-16s %s" % (
            r["position"], r["token"], r["script"], "yes" if r["stop"] else "no",
            "-" if r["stop"] else r["stem"], "-" if r["stop"] else (r["dhvani"] or "(too short)")))


def print_zone_details(engine, details):
    for zone_name in ["raw", "nostem", "all", "soundex", "dhvani", "title"]:
        if zone_name not in details:
            continue
        print(LINE)
        print("ZONE %-7s  term -> df, idf      (N = %d documents)" % (zone_name, engine.num_docs))
        for item in details[zone_name]:
            if "idf" in item:
                print("   %-20s df=%-7d idf=%.3f" % (item["term"], item["df"], item["idf"]))
            else:
                print("   %-20s df=%-7d ltc weight=%.3f" % (item["term"], item["df"], item["query_weight"]))
    if "pooled_df" in details:
        print(LINE)
        print("POOLED DF (surface term uses the df of its Dhvani class):")
        zone = engine.index.zones["all"]
        for term in details["pooled_df"]:
            print("   %-20s own df=%-7d pooled df=%d" % (term, zone.get_df(term), details["pooled_df"][term]))


def print_postings(engine, query):
    """Show the first few postings of each Dhvani key (the inverted index itself)."""
    zone = engine.index.zones["dhvani"]
    print(LINE)
    print("POSTINGS in the dhvani zone (first 5 of each list: doc -> tf, positions)")
    for key in query["dhvani_keys"]:
        docs, tfs = zone.postings(key)
        parts = []
        for i in range(min(5, len(docs))):
            positions = zone.positions_in_doc(key, int(docs[i]))
            parts.append("%s tf=%d %s" % (engine.index.doc_ids[docs[i]], tfs[i], positions[:4]))
        print("   %-8s df=%-6d %s" % (key, len(docs), " | ".join(parts)))


def print_results(engine, ranked, details, k):
    print(LINE)
    print("RESULTS")
    zone_scores = details.get("zone_scores", {}) if details else {}
    proximity = details.get("proximity", {}) if details else {}
    for rank in range(min(k, len(ranked))):
        doc, score = ranked[rank]
        info = engine.doc_info(doc, 110)
        print("%2d. %-12s %.3f  %s" % (rank + 1, info["docid"], score, info["title"]))
        parts = []
        for zone_name in zone_scores:
            parts.append("%s=%.2f" % (zone_name, zone_scores[zone_name][doc]))
        if doc in proximity:
            parts.append("proximity=%.2f (window %s)" % (proximity[doc][0], proximity[doc][1]))
        if len(parts) > 0:
            print("    " + "  ".join(parts))
        print("    " + info["snippet"])


def print_gate(details):
    if "gate" not in details:
        return
    gate = details["gate"]
    print(LINE)
    print("GATE: run neural stage? %s  (probability %.2f, threshold %.2f)" % (
        "YES" if gate["use_neural"] else "NO", gate["probability"], gate["threshold"]))
    for name in gate["features"]:
        print("   %-22s %.3f" % (name, gate["features"][name]))


def command_search(engine, args):
    details = {} if args.explain else None
    start = time.perf_counter()
    ranked = engine.search(args.query, args.system, 100, details=details)
    took = (time.perf_counter() - start) * 1000
    if args.explain:
        print_tokens(details["query"])
        print_zone_details(engine, details)
        print_postings(engine, details["query"])
        print_gate(details)
    print_results(engine, ranked, details, args.k)
    print(LINE)
    print("system %s, %.1f ms" % (args.system, took))


def command_boolean(engine, args):
    explain = {}
    docs = boolean_search(engine.index.zones["all"], args.query, use_skips=not args.no_skips, explain=explain)
    print("processing order (term, df):", explain["processing_order"])
    print("comparisons during AND merges:", explain["comparisons"])
    print("matching documents:", len(docs))
    for doc in docs[:args.k]:
        print("  ", engine.index.doc_ids[doc], engine.titles[doc])


def command_phrase(engine, args):
    docs = phrase_search(engine.index.zones["all"], args.query)
    print("documents with the exact phrase:", len(docs))
    for doc in docs[:args.k]:
        print("  ", engine.index.doc_ids[doc], engine.titles[doc])


def command_compare(engine, args):
    for system in args.systems.split(","):
        ranked = engine.search(args.query, system, args.k)
        titles = []
        for doc, _ in ranked[:args.k]:
            titles.append(engine.titles[doc])
        print("%-4s %s" % (system, " | ".join(titles)))


def main():
    parser = argparse.ArgumentParser(description="LipiSetu: script-invariant Hindi search")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--system", default="S3")
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--explain", action="store_true")

    p = sub.add_parser("boolean")
    p.add_argument("query")
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--no-skips", action="store_true")

    p = sub.add_parser("phrase")
    p.add_argument("query")
    p.add_argument("--k", type=int, default=10)

    p = sub.add_parser("compare")
    p.add_argument("query")
    p.add_argument("--systems", default="B1,B2,S1,S3")
    p.add_argument("--k", type=int, default=3)

    args = parser.parse_args()
    engine = SearchEngine()
    if args.command == "search":
        command_search(engine, args)
    elif args.command == "boolean":
        command_boolean(engine, args)
    elif args.command == "phrase":
        command_phrase(engine, args)
    else:
        command_compare(engine, args)


if __name__ == "__main__":
    main()
