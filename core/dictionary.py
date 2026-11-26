"""Dictionary source, leet-aware normalisation and word lookup.

The dictionary is built from the database itself: each account's username and
email start with a base word (jeddah_6635_0 -> "jeddah"), so the set of base
words is pulled straight from the records. There are no wordlist text files.
"""
from itertools import product

from core import load_config
from core import db

# How many ambiguous-leet variants we allow before giving up on expansion.
_MAX_VARIANTS = 16

_BASE_WORDS = None


def _extract_base(field: str) -> str:
    """The base word is the part before the first underscore, lower-cased.

    Works for a username ('jeddah_6635_0' -> 'jeddah') and for an email's local
    part ('jeddah_6635_0@example.com' -> 'jeddah').
    """
    local = field.split("@")[0]
    return local.split("_")[0].strip().lower()


def base_words(path: str = None) -> set:
    """Base words pulled from every account's username and email.

    Its size is the 'Total base words' figure for the report.
    """
    global _BASE_WORDS
    if _BASE_WORDS is None:
        words = set()
        for acc in db.load_accounts(path):
            for field in (acc.get("username", ""), acc.get("email", "")):
                base = _extract_base(field)
                if base:
                    words.add(base)
        _BASE_WORDS = words
    return _BASE_WORDS


def normalise(password: str) -> list:
    """Lower-case, then reverse leet swaps. Returns every variant (1 can be i or l)."""
    cfg = load_config()
    leet_map = cfg["leet_map"]
    lowered = password.lower()
    choices = []
    for ch in lowered:
        if ch in leet_map:
            opts = [ch] + leet_map[ch]
            seen = []
            for o in opts:
                if o not in seen:
                    seen.append(o)
            choices.append(seen)
        else:
            choices.append([ch])

    total = 1
    for c in choices:
        total *= len(c)
    if total > _MAX_VARIANTS:
        simple = "".join(c[1] if len(c) > 1 else c[0] for c in choices)
        return [lowered, simple] if simple != lowered else [lowered]

    return ["".join(p) for p in product(*choices)]


def find_words(password: str) -> list:
    """Find dictionary words (>= min_word_length) in any normalised variant."""
    cfg = load_config()
    min_len = cfg["min_word_length"]
    words = base_words()
    n = len(password)
    seen = set()
    matches = []
    for variant in normalise(password):
        for start in range(n):
            for end in range(start + min_len, n + 1):
                token = variant[start:end]
                if token in words:
                    key = (start, end)
                    if key not in seen:
                        seen.add(key)
                        matches.append({"type": "dictionary", "token": token,
                                        "start": start, "end": end})
    return matches
