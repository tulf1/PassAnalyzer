from core import crack_time


def test_human_time_units():
    assert crack_time.human_time(0.5) == "< 1 second"
    assert crack_time.human_time(30) == "30.0 seconds"
    assert "minutes" in crack_time.human_time(120)
    assert "hours" in crack_time.human_time(7200)
    assert "days" in crack_time.human_time(200000)


def test_human_time_scientific_for_huge():
    out = crack_time.human_time(1e20)
    assert "10^" in out and "years" in out


def test_crack_times_three_scenarios():
    rows = crack_time.crack_times(50.0)
    assert [r["id"] for r in rows] == ["S1", "S2", "S3"]
    # higher rate -> less time
    assert rows[2]["seconds"] < rows[0]["seconds"]
