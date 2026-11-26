"""Naive and pattern-adjusted entropy."""
import math

_SUFFIX_EXTRA = {"123", "1234", "12345"}
_SUFFIX_SYMBOLS = {"!", "@", "#", "."}
_GREG = (1900, 2099)
_HIJRI = (1300, 1499)


def char_pool(pw: str) -> int:
    """26 lower + 26 upper + 10 digit + 32 symbol, capped at 94."""
    n = 0
    if any(c.islower() for c in pw):
        n += 26
    if any(c.isupper() for c in pw):
        n += 26
    if any(c.isdigit() for c in pw):
        n += 10
    if any((not c.isalnum()) for c in pw):
        n += 32
    return min(n, 94)


def naive_entropy(pw: str) -> float:
    n = char_pool(pw)
    if n == 0 or len(pw) == 0:
        return 0.0
    return len(pw) * math.log2(n)


def _is_mutation_suffix(tail: str) -> bool:
    if not tail:
        return False
    if tail in _SUFFIX_EXTRA or tail in _SUFFIX_SYMBOLS:
        return True
    if tail.isdigit():
        if len(tail) <= 2:                       # 0-99
            return True
        if len(tail) == 4:                       # a year
            y = int(tail)
            return _GREG[0] <= y <= _GREG[1] or _HIJRI[0] <= y <= _HIJRI[1]
    return False


def covered_length(pw: str, matches: list) -> int:
    """Union of match spans, plus a trailing mutation suffix if present."""
    n = len(pw)
    covered = [False] * n
    for m in matches:
        for i in range(m["start"], min(m["end"], n)):
            covered[i] = True
    if not any(covered):
        return 0
    last_end = max(i for i in range(n) if covered[i]) + 1
    tail = pw[last_end:]
    if _is_mutation_suffix(tail):
        for i in range(last_end, n):
            covered[i] = True
    return sum(covered)


def _remaining_pool(pw: str, matches: list) -> int:
    n = len(pw)
    covered = [False] * n
    for m in matches:
        for i in range(m["start"], min(m["end"], n)):
            covered[i] = True
    if any(covered):
        last_end = max((i for i in range(n) if covered[i]), default=-1) + 1
        tail = pw[last_end:]
        if _is_mutation_suffix(tail):
            for i in range(last_end, n):
                covered[i] = True
    rest = "".join(ch for i, ch in enumerate(pw) if not covered[i])
    return char_pool(rest)


def adjusted_entropy(pw: str, matches: list, word_count: int) -> float:
    """H_adj = log2(|W|) + (L - l_m) * log2(N_r), capped at the naive value."""
    naive = naive_entropy(pw)
    l_m = covered_length(pw, matches)
    if l_m == 0 or word_count <= 0:
        return naive
    n_r = _remaining_pool(pw, matches)
    remaining = len(pw) - l_m
    adj = math.log2(word_count)
    if remaining > 0 and n_r > 0:
        adj += remaining * math.log2(n_r)
    return min(adj, naive)


def compute(pw: str, matches: list, word_count: int) -> dict:
    naive = naive_entropy(pw)
    adj = adjusted_entropy(pw, matches, word_count)
    return {
        "pool": char_pool(pw),
        "naive": round(naive, 1),
        "adjusted": round(adj, 1),
        "covered": covered_length(pw, matches),
    }
