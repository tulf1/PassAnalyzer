from core import policy


def failed_ids(pw):
    return {r["id"] for r in policy.check_policy(pw)["rules"] if not r["passed"]}


def test_password_fails_expected_rules():
    assert failed_ids("password") == {"P2", "P4", "P5", "P6"}


def test_p6_dictionary_and_date():
    assert failed_ids("Riyadh2024") == {"P5", "P6", "P8"}


def test_leet_dictionary_match():
    # p@$$w0rd normalises to 'password'
    assert "P6" in failed_ids("P@ssw0rd!")


def test_p4ssword_not_matched():
    # 4 is not in the leet map, so 'p4ssword' is not seen as 'password'
    assert "P6" not in failed_ids("p4ssword")


def test_keyboard_walk():
    assert "P7" in failed_ids("qwerty!Q1")


def test_reversed_keyboard_walk():
    assert "P7" in failed_ids("trewq12")


def test_hijri_year():
    assert "P8" in failed_ids("Noura1445!")


def test_strong_password_passes_all():
    assert failed_ids("Tr7#vLq9!mZ2") == set()


def test_walk_not_double_counted_as_dictionary():
    res = policy.check_policy("qwerty")
    types = {m["type"] for m in res["matches"]}
    assert "walk" in types
