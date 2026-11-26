"""Runs the whole analysis pipeline for one password."""
import time

from core import policy as policy_mod
from core import entropy as entropy_mod
from core import scoring as scoring_mod
from core import crack_time as crack_mod
from core import recommend as recommend_mod
from core import attack as attack_mod

_WORD_COUNT = None


def word_count() -> int:
    """|W|: the number of candidate guesses built from the database."""
    global _WORD_COUNT
    if _WORD_COUNT is None:
        _WORD_COUNT = max(len(attack_mod.load_candidates()), 1)
    return _WORD_COUNT


def analyze(password: str, wc: int = None) -> dict:
    wc = wc or word_count()
    t0 = time.perf_counter()

    pol = policy_mod.check_policy(password)
    ent = entropy_mod.compute(password, pol["matches"], wc)
    sc = scoring_mod.score_password(password, pol["classes"], ent["adjusted"], pol)
    times = crack_mod.crack_times(ent["adjusted"])
    tips = recommend_mod.recommend(password, pol, sc["score"], sc["rating"])

    elapsed = (time.perf_counter() - t0) * 1000.0
    return {
        "length": len(password),
        "classes": pol["classes"],
        "policy": {"passed": pol["passed"], "rules": pol["rules"]},
        "entropy": {"pool": ent["pool"], "naive": ent["naive"], "adjusted": ent["adjusted"]},
        "score": sc["score"],
        "rating": sc["rating"],
        "crack_times": [{"id": t["id"], "label": t["label"], "human": t["human"]} for t in times],
        "recommendations": tips,
        "elapsed_ms": round(elapsed, 1),
    }
