"""Average-case cracking-time estimates for each attacker scenario."""
import math

from core import load_config

_MINUTE = 60
_HOUR = 3600
_DAY = 86400
_YEAR = 365.25 * _DAY


def human_time(seconds: float) -> str:
    if seconds < 1:
        return "< 1 second"
    if seconds < _MINUTE:
        return f"{seconds:.1f} seconds"
    if seconds < _HOUR:
        return f"{seconds / _MINUTE:.1f} minutes"
    if seconds < _DAY:
        return f"{seconds / _HOUR:.1f} hours"
    if seconds < _YEAR:
        return f"{seconds / _DAY:.1f} days"
    years = seconds / _YEAR
    if years >= 1_000_000:
        exp = int(math.floor(math.log10(years)))
        mant = years / (10 ** exp)
        return f"{mant:.1f} × 10^{exp} years"
    return f"{years:.1f} years"


def crack_times(adjusted_entropy: float) -> list:
    """T = 2^(H-1) / R for each scenario."""
    out = []
    try:
        guesses = 2 ** (adjusted_entropy - 1)
    except OverflowError:
        guesses = float("inf")
    for sc in load_config()["scenarios"]:
        rate = sc["rate_per_second"]
        seconds = guesses / rate if rate > 0 else float("inf")
        out.append({
            "id": sc["id"],
            "label": sc["label"],
            "rate": rate,
            "seconds": seconds,
            "human": human_time(seconds),
        })
    return out
