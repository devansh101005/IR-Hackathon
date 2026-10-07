"""Query-term proximity (Lecture: Scoring and result assembly - query term proximity).

If the query words appear close together in a passage, the passage is more
likely to be about the query. I find the SMALLEST WINDOW of positions that
contains every query word found in the passage.

I use the Dhvani zone positions, so this works the same way for Devanagari
and Roman queries.

proximity(d) = (m - 1) / window_size     where m = number of distinct query words found
               (0 if fewer than 2 words are found; 1.0 when they are all next to each other)
"""


def smallest_window(position_lists):
    """Smallest window that contains at least one position from every list.

    Classic sliding approach: keep one pointer per list, always move the
    pointer that is at the smallest position.
    """
    pointers = [0] * len(position_lists)
    best = None
    while True:
        current = []
        for i in range(len(position_lists)):
            current.append(position_lists[i][pointers[i]])
        low = min(current)
        high = max(current)
        if best is None or high - low < best:
            best = high - low
        # move the list that holds the smallest position
        smallest_list = current.index(low)
        pointers[smallest_list] += 1
        if pointers[smallest_list] >= len(position_lists[smallest_list]):
            break
    return best + 1


def proximity_score(zone, query_keys, doc_number):
    """Proximity score of one document for the query's Dhvani keys."""
    position_lists = []
    seen = set()
    for key in query_keys:
        if key in seen:
            continue
        seen.add(key)
        positions = zone.positions_in_doc(key, doc_number)
        if len(positions) > 0:
            position_lists.append(positions)
    m = len(position_lists)
    if m < 2:
        return 0.0, 0
    window = smallest_window(position_lists)
    return (m - 1) / float(window - 1 if window > 1 else 1), window
