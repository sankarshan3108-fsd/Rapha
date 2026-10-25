"""Hand-written merge sort for the daily admission report."""


def merge_sort(records):
    """Sort patients by (admission_date, patient_id).

    Divide the list in halves, sort each half recursively, then merge the two
    sorted halves by repeatedly taking the smaller front element.  On ties the
    LEFT element is taken first, which keeps the sort stable.
    Returns (sorted_list, comparisons).  The input list is not modified.
    Time O(n log n), extra space O(n).
    """
    counter = [0]
    sorted_list = _sort(list(records), counter)
    return sorted_list, counter[0]


def _sort(items, counter):
    if len(items) <= 1:
        return items
    middle = len(items) // 2
    left = _sort(items[:middle], counter)
    right = _sort(items[middle:], counter)
    return _merge(left, right, counter)


def _comes_first(a, b):
    """True if a should be placed before b (or equal -> keeps stability)."""
    if a.admission_date != b.admission_date:
        return a.admission_date < b.admission_date
    return a.patient_id <= b.patient_id


def _merge(left, right, counter):
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        counter[0] += 1
        if _comes_first(left[i], right[j]):
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


# ---------------------------------------------------------------------------
# Optional extras (merge_sort() above is unchanged)
# ---------------------------------------------------------------------------
def merge_sort_by(items, key_func, descending=False):
    """Stable merge sort of any list by key_func(item). Used for column sorts.

    Same divide-and-conquer idea as merge_sort(); returns (list, comparisons).
    Descending order flips the comparison (>=), so ties still keep their
    original order.  O(n log n) time, O(n) extra space.
    """
    counter = [0]

    def sort(part):
        if len(part) <= 1:
            return part
        middle = len(part) // 2
        left, right = sort(part[:middle]), sort(part[middle:])
        merged, i, j = [], 0, 0
        while i < len(left) and j < len(right):
            counter[0] += 1
            a, b = key_func(left[i]), key_func(right[j])
            take_left = a >= b if descending else a <= b
            if take_left:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged

    return sort(list(items)), counter[0]


def recursion_depth(count):
    """Number of divide levels merge sort needs for count items."""
    depth = 0
    size = count
    while size > 1:
        size = (size + 1) // 2
        depth += 1
    return depth


def merge_sort_frames(items):
    """Snapshots for animating merge sort.

    Returns a list of (phase, label, segments); segments is a list of lists
    (the current sub-arrays).  Divide frames split every sub-array in half
    (len // 2, exactly like merge_sort); merge frames show those sub-arrays
    merged back together, from the smallest pieces up to the sorted list.
    """
    segments = [list(items)]
    levels = [segments]
    while any(len(part) > 1 for part in segments):
        next_level = []
        for part in segments:
            if len(part) > 1:
                middle = len(part) // 2
                next_level.append(part[:middle])
                next_level.append(part[middle:])
            else:
                next_level.append(part)
        segments = next_level
        levels.append(segments)
    frames = []
    for depth, level in enumerate(levels):
        label = "Original list" if depth == 0 else "Divide - level %d" % depth
        frames.append(("divide", label, level))
    for depth in range(len(levels) - 2, -1, -1):
        merged_level = [merge_sort(part)[0] for part in levels[depth]]
        label = "Merge - level %d" % depth if depth else "Merge - fully sorted"
        frames.append(("merge", label, merged_level))
    return frames
