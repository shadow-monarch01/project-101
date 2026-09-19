import pytest
from modules.bgi import compute_bgi, check_decision_consistency

def test_bgi_calculation_consistent():
    res = compute_bgi(
        qualification_score=88.0,
        expected_decision="STRONG_HIRE",
        ai_decision="STRONG_HIRE",
        ai_score=90.0,
        efs_score=95.0,
        required_skill_match=100.0
    )
    assert res["bgi_score"] <= 20.0
    assert res["classification"] == "Very Low Gap"
    assert res["flagged_for_audit"] is False

def test_bgi_calculation_flagged_gap():
    res = compute_bgi(
        qualification_score=92.0,
        expected_decision="STRONG_HIRE",
        ai_decision="REJECT",
        ai_score=40.0,
        efs_score=40.0,
        required_skill_match=100.0
    )
    assert res["bgi_score"] >= 50.0
    assert res["flagged_for_audit"] is True

def test_monotonicity_checker():
    # 1. Consistent
    res1 = check_decision_consistency(70.0, 85.0, "INTERVIEW", "HIRE")
    assert res1["is_consistent"] is True

    # 2. Monotonicity Degradation
    res2 = check_decision_consistency(70.0, 90.0, "HIRE", "REJECT")
    assert res2["is_consistent"] is False
    assert res2["violation_type"] == "MONOTONICITY_DEGRADATION"
