"""Mutation rules: turn one base word into its realistic variants."""
from core import load_config


def _leet(word: str, leet_out: dict) -> str:
    return "".join(leet_out.get(c.lower(), c) if c.islower() else c for c in word)


def _case_forms(word: str, cfg: dict):
    leet_out = cfg["leet_out"]
    lower = word.lower()
    cap = word.capitalize()
    for form in cfg["case_forms"]:
        if form == "lower":
            yield lower
        elif form == "capitalized":
            yield cap
        elif form == "upper":
            yield word.upper()
        elif form == "leet_lower":
            yield _leet(lower, leet_out)
        elif form == "leet_capitalized":
            yield _leet(cap, leet_out)


def _numeric_suffixes(cfg: dict):
    """Every digit-only suffix: 0-99, the common runs, and Gregorian/Hijri years."""
    lo, hi = cfg["suffix_numbers"]
    for n in range(lo, hi + 1):
        yield str(n)
    for s in cfg["suffix_extra"]:
        yield s
    g0, g1 = cfg["suffix_years_gregorian"]
    for y in range(g0, g1 + 1):
        yield str(y)
    h0, h1 = cfg["suffix_years_hijri"]
    for y in range(h0, h1 + 1):
        yield str(y)


def _suffixes(cfg: dict):
    yield ""
    numbers = list(_numeric_suffixes(cfg))
    for s in numbers:
        yield s
    for s in cfg["suffix_symbols"]:
        yield s
    # stacked: a number/year followed by a symbol (e.g. iau1425!, security81#)
    if cfg.get("suffix_stack"):
        for n in numbers:
            for sym in cfg["suffix_symbols"]:
                yield n + sym


def generate(word: str):
    """Yield every mutation of one word (case form, then form + each suffix)."""
    cfg = load_config()["mutations"]
    suffixes = list(_suffixes(cfg))
    seen = set()
    for form in _case_forms(word, cfg):
        for suf in suffixes:
            cand = form + suf
            if cand not in seen:
                seen.add(cand)
                yield cand
