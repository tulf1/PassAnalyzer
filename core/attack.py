"""Salting, hashing and the dictionary attack.

Note on hash order: the supplied database stores SHA-256(password + salt) with the
salt as a short text string. The build guide describes SHA-256(salt + password).
The scheme is configurable (config: attack.hash_scheme) and defaults to the one
that matches the provided database ("password_salt").
"""
import hashlib
import itertools
import os
import secrets
import string
import time

from core import load_config
from core import dictionary
from core import mutations

_ROOT = os.path.dirname(os.path.dirname(__file__))

_CANDIDATES = None
_EXTRA_WORDS = None
_HYBRID_SUFFIXES = None


def _scheme() -> str:
    return load_config()["attack"].get("hash_scheme", "password_salt")


def digest(password: str, salt: str, scheme: str = None) -> str:
    scheme = scheme or _scheme()
    if scheme == "salt_password":
        material = salt + password
    else:
        material = password + salt
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


_SALT_ALPHABET = string.ascii_letters + string.digits


def hash_password(password: str, salt_len: int = None, scheme: str = None) -> dict:
    """Make a salt the same shape as the database's (8 alphanumeric chars) and
    store SHA-256(password + salt)."""
    cfg = load_config()["attack"]
    salt_len = salt_len or cfg.get("salt_length", 8)
    salt = "".join(secrets.choice(_SALT_ALPHABET) for _ in range(salt_len))
    return {"salt": salt, "hash": digest(password, salt, scheme)}


def build_candidates() -> list:
    """The guess list, built in memory from the database's base words.

    Each base word (pulled from the account usernames/emails) is expanded with
    the mutation rules. De-duplicated, order stable. No files involved.
    """
    seen = set()
    out = []
    for word in sorted(dictionary.base_words()):
        for cand in mutations.generate(word):
            if cand not in seen:
                seen.add(cand)
                out.append(cand)
    return out


def load_candidates(path: str = None) -> list:
    """Cached candidate guess list (the `path` argument is ignored, kept for compatibility)."""
    global _CANDIDATES
    if _CANDIDATES is None:
        _CANDIDATES = build_candidates()
    return _CANDIDATES


def build_index(candidates: list) -> dict:
    """candidate -> 1-based position in the wordlist (its attempt number)."""
    idx = {}
    for i, c in enumerate(candidates):
        if c not in idx:
            idx[c] = i + 1
    return idx


def crack(target_hash: str, salt: str, candidates=None, scheme: str = None,
          max_seconds: float = None) -> dict:
    """Real attack loop: hash each candidate with this salt until one matches."""
    cfg = load_config()["attack"]
    scheme = scheme or _scheme()
    max_seconds = cfg["max_seconds_per_target"] if max_seconds is None else max_seconds
    if candidates is None:
        candidates = load_candidates()
    t0 = time.perf_counter()
    attempts = 0
    for cand in candidates:
        attempts += 1
        if digest(cand, salt, scheme) == target_hash:
            return {"cracked": True, "attempts": attempts,
                    "seconds": round(time.perf_counter() - t0, 4), "found_as": cand}
        if attempts % 2000 == 0 and (time.perf_counter() - t0) > max_seconds:
            break
    return {"cracked": False, "attempts": attempts,
            "seconds": round(time.perf_counter() - t0, 4), "found_as": None}


# ---------------------------------------------------------------------------
# Hybrid + brute-force attack for the "attack your own password" feature.
#
# Unlike simulate()/crack(), which only try the fixed wordlist built from the
# database, this attack also guesses off-list passwords the way a real cracker
# would: a broader public word/name list, hybrid rules (word + digits + symbol),
# and finally a short brute force. It still only ever hashes GUESSES and compares
# them to the stored hash -- it never looks at the entered plaintext. It is time
# bounded, so genuinely strong passwords survive (which is the whole point).
# ---------------------------------------------------------------------------

def _extra_words() -> list:
    """Extra base words from the configured public wordlist file (cached).

    These stand in for a real attacker's word/name list, so the attack is not
    limited to the project's own database. Missing file -> no extra words.
    """
    global _EXTRA_WORDS
    if _EXTRA_WORDS is None:
        cfg = load_config()["attack"]
        rel = cfg.get("extra_wordlist", "")
        path = os.path.join(_ROOT, rel) if rel else ""
        words = []
        seen = set()
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    w = line.strip().lower()
                    if w and not w.startswith("#") and w not in seen:
                        seen.add(w)
                        words.append(w)
        _EXTRA_WORDS = words
    return _EXTRA_WORDS


def _hybrid_bases() -> list:
    """Base words for the hybrid attack: the database's own plus the extra list."""
    seen = set()
    bases = []
    for w in sorted(dictionary.base_words()) + _extra_words():
        if w and w not in seen:
            seen.add(w)
            bases.append(w)
    return bases


def _case_forms(word: str):
    """lower / Capitalised / UPPER / leet forms of one base word, de-duplicated."""
    leet_out = load_config()["mutations"]["leet_out"]

    def leet(s):
        return "".join(leet_out.get(c, c) for c in s)

    lower = word.lower()
    forms = [lower, lower.capitalize(), lower.upper(), leet(lower), leet(lower.capitalize())]
    seen = set()
    for f in forms:
        if f not in seen:
            seen.add(f)
            yield f


def _ordered_suffixes() -> list:
    """Likely suffixes, most-common first: digit runs, symbols, and their
    combinations (e.g. '123456.', '!2024'). The full digit+symbol tail is one
    suffix, so 'Naser' + '123456.' is reached early rather than never."""
    global _HYBRID_SUFFIXES
    if _HYBRID_SUFFIXES is not None:
        return _HYBRID_SUFFIXES

    cfg = load_config()["attack"]
    lo, hi = cfg.get("hybrid_suffix_numbers", [0, 99])

    top_digits = ["1", "12", "123", "1234", "12345", "123456", "1234567", "12345678",
                  "123456789", "1234567890",
                  "2024", "2023", "2025", "2022", "2021", "2020", "2026",
                  "11", "111", "1111", "0", "00", "000", "0000", "99", "69", "007", "786"]
    symbols = ["!", ".", "@", "#", "$", "*", "_", "?"]
    years = [str(y) for y in range(1950, 2031)] + [str(y) for y in range(1380, 1451)]
    small = [str(n) for n in range(lo, hi + 1)]

    ordered = [""]                                   # bare word
    ordered += top_digits                            # word + common digit run
    ordered += symbols                               # word + single symbol
    ordered += [d + s for d in top_digits for s in symbols]   # word + digits + symbol
    ordered += [s + d for s in symbols for d in top_digits]   # word + symbol + digits
    ordered += years                                 # word + year
    ordered += [y + s for y in years for s in symbols[:3]]    # word + year + symbol
    ordered += small                                 # word + 0..99

    seen = set()
    out = []
    for suf in ordered:
        if suf not in seen:
            seen.add(suf)
            out.append(suf)
    _HYBRID_SUFFIXES = out
    return out


def hybrid_guesses():
    """Yield hybrid guesses: for each suffix (likeliest first), every base word
    in each case form + that suffix."""
    bases = _hybrid_bases()
    for suffix in _ordered_suffixes():
        for base in bases:
            for form in _case_forms(base):
                yield form + suffix


def bruteforce_guesses(charset: str, max_length: int):
    """Yield every string over `charset` from length 1 up to `max_length`."""
    for length in range(1, max_length + 1):
        for combo in itertools.product(charset, repeat=length):
            yield "".join(combo)


def crack_any(target_hash: str, salt: str, scheme: str = None,
              max_seconds: float = None, mode: str = "all") -> dict:
    """Attack on one hash, time bounded. Returns the stage that succeeded as
    `method`. `mode` selects which attacks to run:

    - "dictionary": database dictionary + hybrid rules (word-based guesses)
    - "bruteforce": short brute force only
    - "all" (default): both, dictionary first

    Only guesses are hashed; the entered plaintext is never inspected.
    """
    cfg = load_config()["attack"]
    scheme = scheme or _scheme()
    if max_seconds is None:
        max_seconds = cfg.get("own_max_seconds", 8)
    bf = cfg.get("bruteforce", {})
    bf_charset = bf.get("charset", "abcdefghijklmnopqrstuvwxyz0123456789")
    bf_max_len = bf.get("max_length", 4)

    t0 = time.perf_counter()
    attempts = 0

    # (label, group, factory) -- factory builds the guess generator only if used
    all_stages = [
        ("database dictionary", "dictionary", lambda: iter(load_candidates())),
        ("hybrid rules", "dictionary", lambda: hybrid_guesses()),
        ("brute force", "bruteforce", lambda: bruteforce_guesses(bf_charset, bf_max_len)),
    ]
    stages = [(label, factory()) for (label, group, factory) in all_stages
              if mode == "all" or mode == group]

    timed_out = False
    for method, guesses in stages:
        for guess in guesses:
            attempts += 1
            if digest(guess, salt, scheme) == target_hash:
                return {"cracked": True, "attempts": attempts,
                        "seconds": round(time.perf_counter() - t0, 4),
                        "found_as": guess, "method": method}
            if attempts % 2000 == 0 and (time.perf_counter() - t0) > max_seconds:
                timed_out = True
                break
        if timed_out:
            break

    return {"cracked": False, "attempts": attempts,
            "seconds": round(time.perf_counter() - t0, 4),
            "found_as": None, "method": None, "timed_out": timed_out}


def simulate(accounts: list, candidates=None, index=None, scheme: str = None) -> list:
    """Attack each account. Fast path: look the plaintext up in the wordlist index,
    then verify the hit with a single real hash against the stored salt+hash."""
    scheme = scheme or _scheme()
    if candidates is None:
        candidates = load_candidates()
    if index is None:
        index = build_index(candidates)
    results = []
    for acc in accounts:
        plain = acc.get("password", "")
        attempts = index.get(plain)
        cracked = False
        found = None
        if attempts is not None:
            # prove it: one real hash with the account's own salt
            cracked = digest(plain, acc["salt"], scheme) == acc["hash"]
            if cracked:
                found = plain
        results.append({
            "id": acc["id"],
            "username": acc["username"],
            "cracked": cracked,
            "attempts": attempts if cracked else len(candidates),
            "found_as": found,
        })
    return results
