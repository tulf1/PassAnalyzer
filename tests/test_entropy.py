import pytest

from core import policy, entropy
from conftest import WORD_COUNT

# password -> (naive, adjusted) from Table 9, |W| = 50000
TABLE9 = {
    "password": (37.6, 15.6),
    "Password123": (65.5, 15.6),
    "P@ssw0rd!": (59.0, 15.6),
    "Riyadh2024": (59.5, 15.6),
    "qwerty!Q1": (59.0, 33.9),
    "k9#Tq2!x": (52.4, 52.4),
    "Tr7#vLq9!mZ2": (78.7, 78.7),
}


@pytest.mark.parametrize("pw,expected", TABLE9.items())
def test_table9(pw, expected):
    matches = policy.check_policy(pw)["matches"]
    out = entropy.compute(pw, matches, WORD_COUNT)
    assert out["naive"] == expected[0]
    assert out["adjusted"] == expected[1]


def test_random_string_no_false_match():
    pw = "k9#Tq2!x"
    out = entropy.compute(pw, policy.check_policy(pw)["matches"], WORD_COUNT)
    assert out["adjusted"] == out["naive"]  # nothing matched


def test_pool_sizes():
    assert entropy.char_pool("abc") == 26
    assert entropy.char_pool("Abc1") == 62
    assert entropy.char_pool("Abc1!") == 94
