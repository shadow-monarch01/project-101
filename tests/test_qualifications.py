import pytest
from modules.qualifications import (
    match_skills,
    evaluate_experience_match,
    evaluate_education_relevance,
    compute_overall_qualification_score,
    DEFAULT_JOB_TEMPLATES
)

def test_skill_matching():
    cand_skills = ["Python", "SQL", "Git", "FastAPI", "Docker"]
    req_skills = ["Python", "SQL", "REST API", "Git"]
    pref_skills = ["FastAPI", "Kubernetes"]

    res = match_skills(cand_skills, req_skills, pref_skills)
    assert "Python" in res["matched_required_skills"]
    assert "SQL" in res["matched_required_skills"]
    assert "REST API" in res["missing_required_skills"]
    assert "FastAPI" in res["matched_preferred_skills"]
    assert "Kubernetes" in res["missing_preferred_skills"]
    assert "Docker" in res["additional_skills"]
    assert res["matched_required_count"] == 3
    assert res["missing_required_count"] == 1
    assert res["required_match_percentage"] == 75.0
    assert res["skill_gap_percentage"] == 25.0

def test_experience_matching():
    res1 = evaluate_experience_match(6.0, 4.0)
    assert res1["is_sufficient"] is True
    assert res1["experience_match_percentage"] == 100.0

    res2 = evaluate_experience_match(2.0, 4.0)
    assert res2["is_sufficient"] is False
    assert res2["experience_match_percentage"] == 50.0
    assert res2["experience_gap_years"] == 2.0

def test_overall_qualification_scoring():
    cand = {
        "candidate_id": "SWE_001",
        "name": "Priya Sharma",
        "skills": "Python; SQL; PostgreSQL; REST API; Git; FastAPI",
        "experience_years": 6.0,
        "education": "B.Tech Computer Science",
        "certifications_count": 1,
        "interview_score": 90.0
    }
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    res = compute_overall_qualification_score(cand, job)
    assert res["qualification_score"] >= 80.0
    assert res["expected_decision"] in ["STRONG_HIRE", "HIRE"]
    assert res["component_breakdown"]["required_skills_score"] == 100.0
