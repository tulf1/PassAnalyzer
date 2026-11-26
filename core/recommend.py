"""One specific tip per failed rule, plus score-based advice (metric M6)."""

_RULE_TIPS = {
    "P1": "Make it at least 8 characters long; 12 or more is much safer.",
    "P2": "Add an uppercase letter.",
    "P3": "Add a lowercase letter.",
    "P4": "Add a digit.",
    "P5": "Add a symbol such as ! @ # or $.",
}


def recommend(password: str, policy: dict, score: int, rating: str) -> list:
    tips = []
    by_id = {r["id"]: r for r in policy["rules"]}
    matches = policy.get("matches", [])

    def first_token(kind):
        for m in matches:
            if m["type"] == kind:
                return m["token"]
        return None

    for rid in ["P1", "P2", "P3", "P4", "P5"]:
        if rid in by_id and not by_id[rid]["passed"]:
            tips.append(_RULE_TIPS[rid])

    if "P6" in by_id and not by_id["P6"]["passed"]:
        tok = first_token("dictionary")
        tips.append(f"Remove the dictionary word '{tok}'. Swapping letters for symbols "
                    "(p@ss) does not hide it." if tok else
                    "Remove the dictionary word. Letter-for-symbol swaps do not hide it.")
    if "P7" in by_id and not by_id["P7"]["passed"]:
        tok = first_token("walk")
        tips.append(f"Remove the keyboard pattern '{tok}'." if tok
                    else "Remove the keyboard pattern.")
    if "P8" in by_id and not by_id["P8"]["passed"]:
        tok = first_token("date")
        tips.append(f"Remove the date or year '{tok}'. Dates are among the first things "
                    "attackers try." if tok else
                    "Remove the date or year. Dates are among the first things attackers try.")

    # score-based tips
    if len(password) < 12:
        tips.append("Use 12 or more characters.")
    if rating in ("Very Weak", "Weak", "Fair"):
        tips.append("Use a passphrase of 3-4 unrelated words.")

    # de-duplicate, keep order
    seen = set()
    out = []
    for t in tips:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out
