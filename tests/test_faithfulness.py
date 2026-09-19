import pytest
from modules.faithfulness import evaluate_faithfulness_instance

def test_high_faithfulness():
    skill_analysis = {
        "matched_required_skills": ["Python", "SQL", "Git"],
        "missing_required_skills": []
    }
    explanation = "Candidate demonstrates strong competency in Python and SQL with verified domain experience."
    res = evaluate_faithfulness_instance(explanation, 88.0, "STRONG_HIRE", skill_analysis)
    assert res["faithfulness_score"] >= 85.0
    assert res["classification"] == "High Faithfulness"

def test_false_absence_hallucination_penalty():
    skill_analysis = {
        "matched_required_skills": ["Python", "SQL"],
        "missing_required_skills": []
    }
    explanation = "Candidate rejected because of lack in Python programming and insufficient background."
    res = evaluate_faithfulness_instance(explanation, 88.0, "REJECT", skill_analysis)
    assert res["faithfulness_score"] < 70.0
    assert len(res["deductions"]) > 0
