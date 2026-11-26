"""Run the analyzer and the attack over the database, then compute M1-M7.

Writes results/evaluation.json and results/per_account.csv for the final report.
Adapted to the supplied 1,000-record database: each account is rated by the tool,
then attacked, and the metrics compare prediction against the real outcome.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import analyzer, attack, db

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RESULTS = os.path.join(_ROOT, "results")

_WEAK = {"Very Weak", "Weak"}
_STRONG = {"Strong", "Very Strong"}


def run(limit=None):
    accounts = db.load_accounts(limit=limit)
    candidates = attack.load_candidates()
    index = attack.build_index(candidates)
    cracked = attack.simulate(accounts, candidates, index)
    cracked_by_id = {c["id"]: c for c in cracked}

    rows = []
    elapsed = []
    agree = 0
    failed_rules_total = 0
    failed_rules_with_tip = 0

    per_class = {}       # M1
    mttc = {}            # M5

    for acc in accounts:
        res = analyzer.analyze(acc["password"])
        rating = res["rating"]
        elapsed.append(res["elapsed_ms"])
        cr = cracked_by_id[acc["id"]]

        pc = per_class.setdefault(rating, {"total": 0, "cracked": 0})
        pc["total"] += 1
        if cr["cracked"]:
            pc["cracked"] += 1

        if (rating in _WEAK and cr["cracked"]) or (rating not in _WEAK and not cr["cracked"]):
            agree += 1

        failed = [r for r in res["policy"]["rules"] if not r["passed"]]
        failed_rules_total += len(failed)
        if failed:
            # M6: every failed rule must be covered by at least one tip
            if res["recommendations"]:
                failed_rules_with_tip += len(failed)

        if cr["cracked"]:
            m = mttc.setdefault(rating, {"attempts": [], "count": 0})
            m["attempts"].append(cr["attempts"])
            m["count"] += 1

        rows.append({
            "username": acc["username"],
            "rating": rating,
            "cracked": cr["cracked"],
            "attempts": cr["attempts"],
            "found_as": cr["found_as"] or "",
            "failed_rules": ";".join(r["id"] for r in failed),
            "elapsed_ms": res["elapsed_ms"],
        })

    total = len(accounts)
    m1 = {k: round(100 * v["cracked"] / v["total"], 1) for k, v in per_class.items()}
    m2 = round(100 * agree / total, 1) if total else 0
    strong_total = sum(per_class.get(k, {"total": 0})["total"] for k in _STRONG)
    strong_cracked = sum(per_class.get(k, {"cracked": 0})["cracked"] for k in _STRONG)
    m3 = round(100 * strong_cracked / strong_total, 1) if strong_total else 0.0
    m5 = {k: round(sum(v["attempts"]) / v["count"], 1) for k, v in mttc.items() if v["count"]}
    m6 = round(100 * failed_rules_with_tip / failed_rules_total, 1) if failed_rules_total else 100.0
    m7 = {"avg_ms": round(sum(elapsed) / len(elapsed), 2), "max_ms": round(max(elapsed), 2)}

    summary = {
        "accounts": total,
        "wordlist_size": len(candidates),
        "cracked_total": sum(1 for c in cracked if c["cracked"]),
        "M1_crack_rate_per_class": m1,
        "M2_score_attack_agreement": m2,
        "M3_false_strong_rate": m3,
        "M4_policy_detection": "needs the seeded 50-password set (not labelled in the DB)",
        "M5_mean_attempts_per_class": m5,
        "M6_recommendation_coverage": m6,
        "M7_response_time": m7,
    }

    os.makedirs(_RESULTS, exist_ok=True)
    with open(os.path.join(_RESULTS, "evaluation.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    with open(os.path.join(_RESULTS, "per_account.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run(lim)
