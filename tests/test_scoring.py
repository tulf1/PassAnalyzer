import pytest

from core import policy, entropy, scoring
from conftest import WORD_COUNT

# password -> (score, rating) from Table 9
TABLE9 = {
    "password": (13, "Very Weak"),
    "Password123": (36, "Weak"),
    "P@ssw0rd!": (40, "Weak"),
    "Riyadh2024": (21, "Very Weak"),
    "qwerty!Q1": (49, "Weak"),
    "k9#Tq2!x": (75, "Strong"),
    "Tr7#vLq9!mZ2": (90, "Very Strong"),
}


@pytest.mark.parametrize("pw,expected", TABLE9.items())
def test_table9_scores(pw, expected):
    pol = policy.check_policy(pw)
    adj = entropy.adjusted_entropy(pw, pol["matches"], WORD_COUNT)
    out = scoring.score_password(pw, pol["classes"], adj, pol)
    assert out["score"] == expected[0]
    assert out["rating"] == expected[1]


def test_failed_rule_caps_at_49():
    pol = policy.check_policy("qwerty!Q1")
    adj = entropy.adjusted_entropy("qwerty!Q1", pol["matches"], WORD_COUNT)
    assert scoring.score_password("qwerty!Q1", pol["classes"], adj, pol)["score"] <= 49
