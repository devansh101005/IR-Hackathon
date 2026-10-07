"""Web demo for LipiSetu: a small FastAPI backend + one static HTML page.

Run:  python app/server.py        then open http://127.0.0.1:8000
The page only displays what the engine returns; all IR logic lives in src/lipisetu.
"""
import csv
import json
import os
import sys
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(APP_DIR, "..", "src"))

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from lipisetu import config
from lipisetu.search import SearchEngine
from lipisetu.query import parse_query
from lipisetu.eval.metrics import rbo
from lipisetu.text.romanize import romanize
from lipisetu.text.tokenize import tokenize
from lipisetu.text.analyzer import process_token

app = FastAPI(title="LipiSetu")
app.mount("/static", StaticFiles(directory=os.path.join(APP_DIR, "static")), name="static")
engine = None

SYSTEM_NAMES = {
    "S3": "LipiSetu (sparse)", "G1": "LipiSetu cascade", "H1": "Hybrid", "L1": "Learning to rank",
    "D1": "SCD encoder", "D0": "e5-small", "B2": "Transliterate + BM25", "B1": "BM25",
}


def get_engine():
    global engine
    if engine is None:
        engine = SearchEngine()
    return engine


def available(system):
    e = get_engine()
    if system in ["D0", "D1"]:
        return system in e.dense
    if system == "H1":
        return "D1" in e.dense
    if system == "L1":
        return e.ltr is not None and "D1" in e.dense
    if system == "G1":
        return e.gate is not None and "D1" in e.dense
    return True


def highlight(text, query):
    """Split a snippet into pieces and mark words that match the query by stem or Dhvani key."""
    stems = set(query["surface_terms"])
    keys = set(query["dhvani_keys"])
    pieces = []
    for word in text.split(" "):
        hit = False
        for token in tokenize(word):
            token_stem, token_key = process_token(token)
            if token_stem in stems or (token_key != "" and token_key in keys):
                hit = True
        pieces.append({"text": word, "hit": hit})
    return pieces


def result_list(e, ranked, query, details, k):
    zone_scores = details.get("zone_scores", {})
    proximity = details.get("proximity", {})
    results = []
    for rank in range(min(k, len(ranked))):
        doc, score = ranked[rank]
        info = e.doc_info(doc, 260)
        info["rank"] = rank + 1
        info["score"] = round(float(score), 4)
        info["snippet"] = highlight(info["snippet"], query)
        breakdown = {}
        for zone_name in zone_scores:
            breakdown[zone_name] = round(float(zone_scores[zone_name][doc]), 3)
        if doc in proximity:
            breakdown["proximity"] = proximity[doc][0]
            breakdown["window"] = proximity[doc][1]
        info["breakdown"] = breakdown
        results.append(info)
    return results


def explain_payload(e, details):
    query = details.get("query", {})
    payload = {"tokens": query.get("records", []), "script": query.get("script", ""), "zones": {}}
    for zone_name in ["all", "dhvani", "title"]:
        if zone_name in details:
            payload["zones"][zone_name] = details[zone_name]
    if "pooled_df" in details:
        zone = e.index.zones["all"]
        payload["pooled"] = [{"term": t, "own_df": zone.get_df(t), "pooled_df": int(details["pooled_df"][t])}
                             for t in details["pooled_df"]]
    postings = []
    dhvani_zone = e.index.zones["dhvani"]
    for key in query.get("dhvani_keys", [])[:6]:
        docs, tfs = dhvani_zone.postings(key)
        sample = []
        for i in range(min(4, len(docs))):
            sample.append({"doc": e.index.doc_ids[docs[i]], "tf": int(tfs[i]),
                           "positions": dhvani_zone.positions_in_doc(key, int(docs[i]))[:4]})
        postings.append({"key": key, "df": int(len(docs)), "sample": sample})
    payload["postings"] = postings
    if "gate" in details:
        gate = details["gate"]
        payload["gate"] = {"use_neural": bool(gate["use_neural"]), "probability": round(gate["probability"], 3),
                           "threshold": round(gate["threshold"], 3),
                           "features": {k: round(float(v), 3) for k, v in gate["features"].items()}}
    return payload


@app.get("/")
def home():
    return FileResponse(os.path.join(APP_DIR, "static", "index.html"))


@app.get("/api/dhvani")
def dhvani(words: str):
    """Dhvani keys for a few words (used by the page's header illustration)."""
    result = []
    for word in words.split(",")[:8]:
        tokens = tokenize(word)
        key = process_token(tokens[0])[1] if len(tokens) > 0 else ""
        result.append({"word": word, "key": key})
    return result


@app.get("/api/systems")
def systems():
    result = []
    for code in ["S3", "G1", "H1", "L1", "B2"]:
        result.append({"code": code, "name": SYSTEM_NAMES[code], "available": available(code)})
    return result


@app.get("/api/search")
def search(q: str, system: str = "S3", k: int = 10):
    e = get_engine()
    if not available(system):
        return JSONResponse({"error": "system " + system + " is not built yet"}, status_code=400)
    details = {}
    start = time.perf_counter()
    ranked = e.search(q, system, 100, details=details)
    took = (time.perf_counter() - start) * 1000.0
    query = details.get("query") or parse_query(q)
    return {"query": q, "system": system, "took_ms": round(took, 1),
            "results": result_list(e, ranked, query, details, k),
            "explain": explain_payload(e, details)}


@app.get("/api/consistency")
def consistency(q: str, system: str = "S3"):
    """Run the query and its Roman version, and report how similar the two top-10 lists are."""
    e = get_engine()
    if parse_query(q)["script"] != "deva":
        return {"available": False}
    roman = romanize(q)
    result = {"available": True, "roman": roman, "systems": []}
    for code in [system, "B2"]:
        if not available(code):
            continue
        first = [doc for doc, _ in e.search(q, code, 10)]
        second = [doc for doc, _ in e.search(roman, code, 10)]
        result["systems"].append({"code": code, "name": SYSTEM_NAMES.get(code, code),
                                  "rbo": round(rbo(first, second, 0.9, 10), 3),
                                  "shared_top10": len(set(first) & set(second))})
    return result


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


@app.get("/api/results")
def results():
    """Everything the Evidence section shows, straight from the results/ files."""
    return {
        "main": read_csv("main_metrics.csv"),
        "invariance": read_csv("invariance.csv"),
        "efficiency": read_csv("efficiency.csv"),
        "budget": read_csv("e10_budget_curve.csv"),
        "operating_point": read_json("e10_operating_point.json"),
        "ablation": read_csv("e5_dhvani_ablation.csv"),
        "scd": read_json("scd_training.json"),
        "corpus": read_json("e3_corpus_stats.json"),
        "significance": read_csv("significance.csv"),
        "human": read_csv("human_invariance.csv"),
        "human_metrics": read_csv("human_metrics.csv"),
        "agreement": read_json("e12_annotator_agreement.json"),
        "word_examples": read_csv("e12_word_examples.csv"),
    }


if __name__ == "__main__":
    import uvicorn
    get_engine()
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))
