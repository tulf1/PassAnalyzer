"""PassAnalyzer core package.

All security logic lives here. The web layer only sends input and shows results.
"""
import json
import os
from functools import lru_cache

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "policy.json")


@lru_cache(maxsize=1)
def load_config(path: str = None) -> dict:
    """Load config/policy.json once and cache it."""
    with open(path or _CONFIG_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)
