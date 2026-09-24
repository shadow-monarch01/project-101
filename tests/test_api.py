import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_api_jobs():
    res = client.get("/api/jobs")
    assert res.status_code == 200
    assert len(res.json()["jobs"]) >= 1

def test_api_candidates():
    res = client.get("/api/candidates")
    assert res.status_code == 200
    assert len(res.json()["candidates"]) >= 1

def test_api_skill_analysis():
    payload = {
        "candidate_skills": ["Python", "SQL", "Git"],
        "required_skills": ["Python", "SQL", "REST API", "Git"]
    }
    res = client.post("/api/skill-analysis", json=payload)
    assert res.status_code == 200
    assert res.json()["required_match_percentage"] == 75.0

def test_api_qualification_score():
    payload = {
        "candidate": {
            "skills": "Python; SQL; Git; REST API",
            "experience_years": 5.0,
            "education": "B.Tech Computer Science"
        }
    }
    res = client.post("/api/qualification-score", json=payload)
    assert res.status_code == 200
    assert res.json()["qualification_score"] >= 70.0

def test_api_evaluate():
    payload = {
        "candidate": {
            "candidate_id": "TEST_01",
            "name": "Alex",
            "skills": "Python; SQL; Git; REST API; PostgreSQL",
            "experience_years": 5.0,
            "education": "B.Tech Computer Science"
        },
        "mode": "Demo Simulation Mode"
    }
    res = client.post("/api/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "recommendation" in data
    assert "efs" in data
    assert "background_investigation" in data

def test_api_counterfactual():
    payload = {
        "candidate": {
            "candidate_id": "TEST_01",
            "name": "Alex",
            "skills": "Python; SQL; Git",
            "experience_years": 5.0
        },
        "concept": "experience_years",
        "target_value": "1.0",
        "mode": "Demo Simulation Mode"
    }
    res = client.post("/api/counterfactual", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "original_profile" in data
    assert "counterfactual_profile" in data

def test_api_counterfactual_multi_dimension():
    payload = {
        "candidate": {
            "candidate_id": "TEST_02",
            "name": "Jordan",
            "skills": "Python; SQL; Git; FastAPI",
            "experience_years": 5.0,
            "education": "B.Tech Computer Science",
            "certifications_count": 1
        },
        "interventions": {
            "skills": "Remove Core Skill",
            "experience_years": 1.0,
            "education": "Bootcamp Certificate"
        },
        "mode": "Demo Simulation Mode"
    }
    res = client.post("/api/counterfactual", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "original_profile" in data
    assert "counterfactual_profile" in data
    twin_cand = data["counterfactual_profile"]["candidate"]
    assert twin_cand["experience_years"] == 1.0
    assert twin_cand["education"] == "Bootcamp Certificate"
    assert "Python" not in twin_cand["skills"] or "SQL" in twin_cand["skills"]

def test_api_resume_screen():
    payload = {
        "resume_text": "Senior Backend Developer with 6 years experience in Python, FastAPI, PostgreSQL, SQL, Git, and Docker.",
        "candidate_data": {
            "experience_years": 6.0,
            "education": "B.Tech Computer Science"
        },
        "job_id": "JOB_SWE_01"
    }
    res = client.post("/api/resume-screen", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "qualification_analysis" in data
    assert "ai_evaluation" in data
    assert "decision" in data["ai_evaluation"]
    assert "efs_assessment" in data
    assert "background_investigation" in data

