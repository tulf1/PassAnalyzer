"""0-100 strength score and a five-level rating."""
from core import load_config


def score_password(pw: str, classes: int, adjusted_entropy: float, policy: dict) -> dict:
    cfg = load_config()["scoring"]
    ratings = load_config()["ratings"]

    length_pts = min(len(pw), cfg["length_cap"]) * cfg["length_points_per_char"]
    class_pts = classes * cfg["class_points"]
    entropy_pts = min(adjusted_entropy / cfg["entropy_divisor"], cfg["entropy_cap"])

    failed = {r["id"] for r in policy["rules"] if not r["passed"]}
    penalty = 0
    for rid, pts in cfg["penalties"].items():
        if rid in failed:
            penalty += pts

    raw = length_pts + class_pts + entropy_pts - penalty
    score = max(0, min(100, raw))
    if failed:
        score = min(score, cfg["fail_cap"])
    score = round(score)

    label = ratings[-1]["label"]
    for r in ratings:
        if score >= r["min"]:
            label = r["label"]
            break
    return {"score": score, "rating": label}
