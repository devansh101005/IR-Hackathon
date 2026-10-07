"""Boolean queries, postings intersection with skip pointers, and phrase queries.

(Lecture: Boolean retrieval; Term vocabulary and postings - skip pointers, positional index)

Query syntax for the command line:   मौसम AND बारिश AND NOT क्रिकेट
                                     "भारत का संविधान"          (phrase)
"""
import math

from lipisetu.text.tokenize import tokenize
from lipisetu.text.analyzer import process_token
from lipisetu.text.stopwords import is_stop_word


def intersect(list1, list2, counter=None):
    """Plain linear merge of two sorted postings lists (the AND operation)."""
    answer = []
    i = 0
    j = 0
    while i < len(list1) and j < len(list2):
        if counter is not None:
            counter[0] += 1
        if list1[i] == list2[j]:
            answer.append(list1[i])
            i += 1
            j += 1
        elif list1[i] < list2[j]:
            i += 1
        else:
            j += 1
    return answer


def intersect_with_skips(list1, list2, counter=None):
    """Merge with skip pointers: every sqrt(L) postings there is a skip.

    If the doc at the skip target is still smaller than the other list's
    current doc, I jump straight there instead of stepping one by one.
    """
    skip1 = int(math.sqrt(len(list1))) or 1
    skip2 = int(math.sqrt(len(list2))) or 1
    answer = []
    i = 0
    j = 0
    while i < len(list1) and j < len(list2):
        if counter is not None:
            counter[0] += 1
        if list1[i] == list2[j]:
            answer.append(list1[i])
            i += 1
            j += 1
        elif list1[i] < list2[j]:
            # follow skips on list1 while they don't go past list2[j]
            if i % skip1 == 0 and i + skip1 < len(list1) and list1[i + skip1] <= list2[j]:
                while i % skip1 == 0 and i + skip1 < len(list1) and list1[i + skip1] <= list2[j]:
                    if counter is not None:
                        counter[0] += 1
                    i += skip1
            else:
                i += 1
        else:
            if j % skip2 == 0 and j + skip2 < len(list2) and list2[j + skip2] <= list1[i]:
                while j % skip2 == 0 and j + skip2 < len(list2) and list2[j + skip2] <= list1[i]:
                    if counter is not None:
                        counter[0] += 1
                    j += skip2
            else:
                j += 1
    return answer


def union(list1, list2):
    """OR: merge two sorted lists without duplicates."""
    return sorted(set(list1) | set(list2))


def difference(list1, list2):
    """AND NOT: docs in list1 that are not in list2."""
    exclude = set(list2)
    answer = []
    for doc in list1:
        if doc not in exclude:
            answer.append(doc)
    return answer


def term_postings(zone, word):
    """Sorted doc list for one query word (normalised and stemmed like the index)."""
    tokens = tokenize(word)
    if len(tokens) == 0:
        return []
    term = process_token(tokens[0])[0]
    docs, _ = zone.postings(term)
    return docs.tolist()


def parse_boolean(query):
    """Split 'a AND b AND NOT c OR d' into (operator, word) steps. Left to right."""
    words = query.split()
    steps = []
    operator = "AND"
    negate = False
    for word in words:
        if word == "AND" or word == "OR":
            operator = word
        elif word == "NOT":
            negate = True
        else:
            if negate:
                steps.append(("NOT", word))
            else:
                steps.append((operator, word))
            operator = "AND"
            negate = False
    return steps


def boolean_search(zone, query, use_skips=True, explain=None):
    """Run a Boolean query on a zone. Returns a sorted list of doc numbers.

    Query optimisation: the AND terms are processed in order of increasing
    df, so the intermediate result stays as small as possible.
    """
    steps = parse_boolean(query)
    and_lists = []
    or_lists = []
    not_lists = []
    for operator, word in steps:
        postings = term_postings(zone, word)
        if operator == "AND":
            and_lists.append((len(postings), word, postings))
        elif operator == "OR":
            or_lists.append(postings)
        else:
            not_lists.append(postings)

    and_lists.sort(key=lambda item: item[0])     # increasing df
    counter = [0]
    result = None
    for df, word, postings in and_lists:
        if result is None:
            result = postings
        elif use_skips:
            result = intersect_with_skips(result, postings, counter)
        else:
            result = intersect(result, postings, counter)
    if result is None:
        result = []
    for postings in or_lists:
        result = union(result, postings)
    for postings in not_lists:
        result = difference(result, postings)

    if explain is not None:
        explain["processing_order"] = [(word, df) for df, word, _ in and_lists]
        explain["comparisons"] = counter[0]
    return result


def phrase_search(zone, phrase):
    """Documents that contain the exact phrase, using the positional index.

    Stop words are not indexed, but their positions are counted, so the
    phrase "भारत का संविधान" means: भारत at position p and संविधान at p + 2.
    """
    tokens = tokenize(phrase)
    wanted = []        # (term, offset from the first word)
    for offset in range(len(tokens)):
        token = tokens[offset]
        if not is_stop_word(token):
            wanted.append((process_token(token)[0], offset))
    if len(wanted) == 0:
        return []
    # Candidate docs: intersection of all the words' postings
    candidates = None
    for term, _ in wanted:
        docs = zone.postings(term)[0].tolist()
        candidates = docs if candidates is None else intersect(candidates, docs)
    first_term, first_offset = wanted[0]
    matches = []
    for doc in candidates:
        starts = zone.positions_in_doc(first_term, doc)
        found = False
        for start in starts:
            ok = True
            for term, offset in wanted[1:]:
                if (start + offset - first_offset) not in zone.positions_in_doc(term, doc):
                    ok = False
                    break
            if ok:
                found = True
                break
        if found:
            matches.append(doc)
    return matches
