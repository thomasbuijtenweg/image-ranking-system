"""Shared math helpers for the Image Ranking System.

These replace Python's stdlib `statistics.mean` and `statistics.stdev`, which
use exact-arithmetic bookkeeping internally (type dispatch, integer ratio
conversion per element). For our use case — floats coming out of vote
tallies and tier histories — plain float math is 5–20x faster and gives
identical results at our precision.

This module is the single source of truth for these helpers. Do not
redefine them elsewhere; import from here.
"""

import math
from typing import Iterable, Sequence


def fast_mean(data: Sequence[float]) -> float:
    """Arithmetic mean. Returns 0.0 for empty input (matches earlier callers)."""
    if not data:
        return 0.0
    return sum(data) / len(data)


def fast_stdev(data: Sequence[float]) -> float:
    """Sample standard deviation. Returns 0.0 for inputs of length <= 1."""
    n = len(data)
    if n <= 1:
        return 0.0
    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data) / (n - 1)
    return math.sqrt(variance)


# Private-name aliases kept for drop-in compatibility with the three existing
# call sites that already use these names. New code should prefer the
# non-underscore names above.
_fast_mean = fast_mean
_fast_stdev = fast_stdev
