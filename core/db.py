"""Loads the simulated-user records from the SQL dump.

The attack only ever uses each record's salt and hash. The plaintext column is
kept so the lab can label accounts and verify a crack; it is never shown raw to
the attack loop and never logged.
"""
import os
import re

_ROOT = os.path.dirname(os.path.dirname(__file__))
_DEFAULT_SQL = os.path.join(_ROOT, "dictionary_attack_db.sql")

_ROW = re.compile(
    r"\('([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\)"
)


def load_accounts(path: str = None, limit: int = None) -> list:
    """Return [{id, username, email, password, salt, hash}, ...]."""
    path = path or _DEFAULT_SQL
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    out = []
    for i, m in enumerate(_ROW.finditer(text)):
        username, email, password, salt, digest = m.groups()
        out.append({
            "id": i,
            "username": username,
            "email": email,
            "password": password,
            "salt": salt,
            "hash": digest,
        })
        if limit and len(out) >= limit:
            break
    return out
