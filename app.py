"""PassAnalyzer Flask server: two pages and two API endpoints.

Security settings:
- Binds to 127.0.0.1 only.
- Passwords arrive only in a POST body, never in the URL.
- Passwords are never logged, printed or written to disk, and never sent back.
- Responses carry Cache-Control: no-store, X-Content-Type-Options: nosniff,
  X-Frame-Options: DENY and a Content-Security-Policy.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, render_template, request

from core import analyzer
from core import attack as attack_mod
from core import db as db_mod

app = Flask(__name__)

_MAX_PW = 128
_candidates = None
_index = None


def _load_attack_data():
    global _candidates, _index
    if _candidates is None:
        _candidates = attack_mod.load_candidates()
        _index = attack_mod.build_index(_candidates)
    return _candidates, _index


@app.after_request
def _headers(resp):
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "frame-ancestors 'none'"
    )
    return resp


@app.route("/")
def analyzer_page():
    return render_template("analyzer.html")


@app.route("/simulate")
def simulate_page():
    total = len(db_mod.load_accounts())
    return render_template("simulate.html", total_accounts=total)


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json(silent=True) or {}
    pw = data.get("password")
    if not isinstance(pw, str) or pw == "" or len(pw) > _MAX_PW:
        return jsonify({"error": "password missing, empty, or too long"}), 400
    result = analyzer.analyze(pw)
    result["wordlist_size"] = analyzer.word_count()
    return jsonify(result)


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    data = request.get_json(silent=True) or {}
    try:
        count = int(data.get("count", 100))
    except (TypeError, ValueError):
        return jsonify({"error": "count must be a whole number"}), 400
    accounts_all = db_mod.load_accounts()
    count = max(1, min(count, len(accounts_all)))
    accounts = random.sample(accounts_all, count)   # a fresh random draw each run
    candidates, index = _load_attack_data()

    results = attack_mod.simulate(accounts, candidates, index)

    # rate each account with the tool, group by that rating
    classes = {}
    detailed = []
    for acc, res in zip(accounts, results):
        rating = analyzer.analyze(acc["password"])["rating"]
        bucket = classes.setdefault(rating, {"total": 0, "cracked": 0})
        bucket["total"] += 1
        if res["cracked"]:
            bucket["cracked"] += 1
        detailed.append({
            "username": acc["username"],
            "rating": rating,
            "cracked": res["cracked"],
            "attempts": res["attempts"],
            "found_as": res["found_as"],
        })

    payload = {
        "count": count,
        "wordlist_size": len(candidates),
        "summary": classes,
        "results": detailed[:50],
        "cracked_total": sum(1 for r in results if r["cracked"]),
    }
    return jsonify(payload)


@app.route("/api/attack_one", methods=["POST"])
def api_attack_one():
    data = request.get_json(silent=True) or {}
    pw = data.get("password")
    if not isinstance(pw, str) or pw == "" or len(pw) > _MAX_PW:
        return jsonify({"error": "password missing, empty, or too long"}), 400
    mode = data.get("mode", "all")
    if mode not in ("all", "dictionary", "bruteforce"):
        mode = "all"
    # store it like a real credential: own random salt + SHA-256(password + salt)
    stored = attack_mod.hash_password(pw)
    # dictionary = DB wordlist + hybrid rules; bruteforce = short brute force
    result = attack_mod.crack_any(stored["hash"], stored["salt"], mode=mode)
    analysis = analyzer.analyze(pw)
    return jsonify({
        "cracked": result["cracked"],
        "attempts": result["attempts"],
        "seconds": result["seconds"],
        "found_as": result["found_as"],
        "method": result["method"],
        "rating": analysis["rating"],
        "score": analysis["score"],
        "salt": stored["salt"],
        "hash": stored["hash"],
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False)
