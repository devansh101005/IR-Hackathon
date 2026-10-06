"""Small helpers to read the MIRACL files: topics (queries), qrels (judgments) and the corpus."""
import json


def read_topics(path):
    """Read a topics TSV file. Returns a dict: query id -> query text."""
    topics = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            topics[parts[0]] = parts[1]
    return topics


def read_qrels(path):
    """Read a TREC qrels file (qid Q0 docid rel).

    Returns a dict: query id -> {doc id: relevance}. Relevance is 0 or 1.
    Passages that are not listed count as non-relevant (standard TREC practice).
    """
    qrels = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) != 4:
                continue
            qid, _, doc_id, rel = parts
            if qid not in qrels:
                qrels[qid] = {}
            qrels[qid][doc_id] = int(rel)
    return qrels


def relevant_docs(qrels, qid):
    """Return the set of relevant doc ids for one query."""
    result = set()
    for doc_id, rel in qrels.get(qid, {}).items():
        if rel > 0:
            result.add(doc_id)
    return result


def read_corpus(path):
    """Read our corpus JSONL file. Returns a list of dicts with docid, title, text."""
    docs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return docs


def read_query_tsv(path):
    """Read a query file from queries/ (columns: qid, text). Returns qid -> text."""
    queries = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("qid\t"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1].strip() and parts[1].strip() != "SKIP":
                queries[parts[0]] = parts[1]
    return queries


def write_query_tsv(path, queries):
    """Write qid -> text to a TSV file with a header line."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("qid\ttext\n")
        for qid in queries:
            f.write(qid + "\t" + queries[qid] + "\n")
