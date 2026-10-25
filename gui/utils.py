"""Small helpers shared by the pages (no DSA logic here)."""
import datetime
import math


def count_by(items, key_func):
    """Count items per key; returns [(key, count)] in first-seen order.

    Uses two parallel lists (not a dict) - fine for a handful of groups.
    """
    keys, counts = [], []
    for item in items:
        key = key_func(item)
        if key in keys:
            counts[keys.index(key)] += 1
        else:
            keys.append(key)
            counts.append(1)
    return list(zip(keys, counts))


def bst_compare_text(key, path):
    """Readable comparisons for a BST path, e.g. ['1120 > 1070 -> right']."""
    lines = []
    for node_key in path:
        if key == node_key:
            lines.append("%d = %d" % (key, node_key))
        elif key < node_key:
            lines.append("%d < %d -> left" % (key, node_key))
        else:
            lines.append("%d > %d -> right" % (key, node_key))
    return lines


def n_log2_n(n):
    """Reference value n * log2(n) (0 for n < 2)."""
    return round(n * math.log2(n)) if n > 1 else 0


def bubble_worst(n):
    """Worst-case comparisons of bubble sort: n(n-1)/2."""
    return n * (n - 1) // 2


def best_height(n):
    """Smallest possible height of a BST with n nodes: ceil(log2(n+1))."""
    return math.ceil(math.log2(n + 1)) if n > 0 else 0


def short_date(date_text):
    """'2026-10-21' -> '21 Oct'."""
    try:
        return datetime.datetime.strptime(date_text, "%Y-%m-%d").strftime("%d %b")
    except ValueError:
        return date_text
