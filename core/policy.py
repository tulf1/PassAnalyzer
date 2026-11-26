"""Policy rules P1-P8. Returns pass/fail plus the spans P6/P7/P8 matched."""
import re

from core import load_config
from core import dictionary

_ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm", "1234567890"]


def _char_classes(pw: str) -> dict:
    return {
        "upper": bool(re.search(r"[A-Z]", pw)),
        "lower": bool(re.search(r"[a-z]", pw)),
        "digit": bool(re.search(r"\d", pw)),
        "symbol": bool(re.search(r"[^A-Za-z0-9]", pw)),
    }


def _walk_spans(pw: str) -> list:
    """Straight-line keyboard runs (forward or backward) of >= min_walk_length."""
    cfg = load_config()
    min_len = cfg["min_walk_length"]
    low = pw.lower()
    n = len(low)
    spans = []
    lines = _ROWS + [r[::-1] for r in _ROWS]
    for start in range(n):
        best = None
        for end in range(start + min_len, n + 1):
            frag = low[start:end]
            if any(frag in line for line in lines):
                best = (start, end)
        if best:
            spans.append(best)
    # keep only maximal spans (drop ones fully inside another)
    maximal = []
    for s in spans:
        if not any(s != o and o[0] <= s[0] and s[1] <= o[1] for o in spans):
            maximal.append(s)
    # also pick up named walks from config (e.g. 1qaz2wsx)
    for w in cfg.get("keyboard_walks", []):
        idx = low.find(w)
        while idx != -1 and len(w) >= min_len:
            span = (idx, idx + len(w))
            if span not in maximal:
                maximal.append(span)
            idx = low.find(w, idx + 1)
    return sorted(set(maximal))


def _valid_dmy(d: int, m: int, y: int = None) -> bool:
    return 1 <= d <= 31 and 1 <= m <= 12


def _date_spans(pw: str) -> list:
    """Dates and years. Gregorian 1900-2099, Hijri 1300-1499, common date layouts."""
    cfg = load_config()
    greg = cfg["years"]["gregorian"]
    hij = cfg["years"]["hijri"]
    spans = []

    # separated dates: dd/mm, dd-mm, dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd
    for m in re.finditer(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", pw):
        d, mo = int(m.group(1)), int(m.group(2))
        if _valid_dmy(d, mo):
            spans.append((m.start(), m.end()))
    for m in re.finditer(r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b", pw):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid_dmy(d, mo):
            spans.append((m.start(), m.end()))

    # 8-digit ddmmyyyy or yyyymmdd
    for m in re.finditer(r"\d{8}", pw):
        s = m.group(0)
        d, mo, y = int(s[0:2]), int(s[2:4]), int(s[4:8])
        yy, mo2, d2 = int(s[0:4]), int(s[4:6]), int(s[6:8])
        if _valid_dmy(d, mo) or _valid_dmy(d2, mo2):
            spans.append((m.start(), m.end()))

    # bare 4-digit years (Gregorian or Hijri)
    for m in re.finditer(r"\d{4}", pw):
        y = int(m.group(0))
        if greg[0] <= y <= greg[1] or hij[0] <= y <= hij[1]:
            spans.append((m.start(), m.end()))

    # merge overlaps into maximal spans
    spans = sorted(set(spans))
    merged = []
    for s in spans:
        if merged and s[0] <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], s[1]))
        else:
            merged.append(s)
    return merged


def check_policy(password: str) -> dict:
    cfg = load_config()
    cls = _char_classes(password)

    walks = _walk_spans(password)
    dates = _date_spans(password)

    # dictionary hits, but drop any that sit inside a keyboard walk (penalise once)
    raw_dict = dictionary.find_words(password)
    dict_matches = []
    for mt in raw_dict:
        inside_walk = any(w[0] <= mt["start"] and mt["end"] <= w[1] for w in walks)
        if not inside_walk:
            dict_matches.append(mt)

    p1 = len(password) >= cfg["min_length"]
    p6 = len(dict_matches) == 0
    p7 = len(walks) == 0
    p8 = len(dates) == 0

    rules = [
        {"id": "P1", "name": "Minimum length", "passed": p1,
         "detail": f"{len(password)} characters"},
        {"id": "P2", "name": "Uppercase letter", "passed": cls["upper"],
         "detail": "has A-Z" if cls["upper"] else "no uppercase"},
        {"id": "P3", "name": "Lowercase letter", "passed": cls["lower"],
         "detail": "has a-z" if cls["lower"] else "no lowercase"},
        {"id": "P4", "name": "Digit", "passed": cls["digit"],
         "detail": "has 0-9" if cls["digit"] else "no digit"},
        {"id": "P5", "name": "Symbol", "passed": cls["symbol"],
         "detail": "has a symbol" if cls["symbol"] else "no symbol"},
        {"id": "P6", "name": "No dictionary words", "passed": p6,
         "detail": "none found" if p6 else "contains '" + dict_matches[0]["token"] + "'"},
        {"id": "P7", "name": "No keyboard walks", "passed": p7,
         "detail": "none found" if p7 else "contains '" + password[walks[0][0]:walks[0][1]] + "'"},
        {"id": "P8", "name": "No dates or years", "passed": p8,
         "detail": "none found" if p8 else "contains '" + password[dates[0][0]:dates[0][1]] + "'"},
    ]

    matches = []
    for mt in dict_matches:
        matches.append(mt)
    for w in walks:
        matches.append({"type": "walk", "token": password[w[0]:w[1]], "start": w[0], "end": w[1]})
    for d in dates:
        matches.append({"type": "date", "token": password[d[0]:d[1]], "start": d[0], "end": d[1]})

    return {
        "passed": all(r["passed"] for r in rules),
        "rules": rules,
        "matches": matches,
        "classes": sum(1 for v in cls.values() if v),
    }
