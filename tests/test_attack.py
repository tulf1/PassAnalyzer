from core import attack


def test_hash_password_unique_salt():
    a = attack.hash_password("Hello123!")
    b = attack.hash_password("Hello123!")
    assert a["salt"] != b["salt"]
    assert a["hash"] != b["hash"]


def test_digest_matches_database_scheme():
    # the provided DB uses SHA-256(password + salt)
    expected = "d52fdc950bb3a48faaab807d042aa8f2edf3430b48d17d779ecbc270674d6eaf"
    assert attack.digest("Jeddah1442", "V38UpT49", "password_salt") == expected


def test_crack_finds_candidate():
    salt = "abcd1234"
    candidates = ["wrong1", "wrong2", "Riyadh2024", "wrong3"]
    target = attack.digest("Riyadh2024", salt, "password_salt")
    res = attack.crack(target, salt, candidates, scheme="password_salt")
    assert res["cracked"] is True
    assert res["found_as"] == "Riyadh2024"
    assert res["attempts"] == 3


def test_crack_fails_on_absent_password():
    salt = "abcd1234"
    candidates = ["one", "two", "three"]
    target = attack.digest("Tr7#vLq9!mZ2", salt, "password_salt")
    res = attack.crack(target, salt, candidates, scheme="password_salt")
    assert res["cracked"] is False
    assert res["found_as"] is None
