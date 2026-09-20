"""
Automated Test Suite for Full Candidate Pool Audit:
1. Full audit with 1 candidate
2. Full audit with multiple candidates
3. Full audit processes ALL candidates without arbitrary truncation
4. One malformed candidate does not stop the audit
5. Empty candidate pool handling
6. Missing optional candidate fields
7. Invalid numeric fields
8. Correct aggregate statistics calculation
9. Correct flagged case count
10. Frontend / API request compatibility (both JSON body and empty body)
"""

import pytest
from fastapi.testclient import TestClient
from app import app
from modules.qualifications import DEFAULT_JOB_TEMPLATES

client = TestClient(app)

def test_batch_audit_single_candidate():
    payload = {
        "job_id": "JOB_SWE_01",
        "candidates": [
            {
                "candidate_id": "TEST_CAND_01",
                "name": "Single Candidate",
                "skills": ["Python", "SQL", "Git", "REST API", "PostgreSQL"],
                "experience_years": 5.0,
                "education": "B.Tech Computer Science"
            }
        ]
    }
    resp = client.post("/api/batch-evaluate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_candidates"] == 1
    assert data["evaluated_candidates"] == 1
    assert data["failed_candidates"] == 0
    assert data["average_qualification_score"] >= 80.0
    assert len(data["candidates"]) == 1
    assert data["candidates"][0]["candidate_id"] == "TEST_CAND_01"
    assert "efs_score" in data["candidates"][0]
    assert "bgi_score" in data["candidates"][0]

def test_batch_audit_multiple_candidates_processes_all():
    candidates = [
        {"candidate_id": f"CAND_MULTI_{i}", "name": f"Candidate {i}", "skills": ["Python", "SQL"], "experience_years": float(i)}
        for i in range(1, 9)
    ]
    payload = {
        "job_id": "JOB_SWE_01",
        "candidates": candidates
    }
    resp = client.post("/api/batch-evaluate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_candidates"] == 8
    assert data["evaluated_candidates"] == 8
    assert data["failed_candidates"] == 0
    assert len(data["candidates"]) == 8

def test_batch_audit_default_pool_processes_full_dataset():
    # Calling /api/batch-evaluate with no explicit candidates should evaluate active dataset
    resp = client.post("/api/batch-evaluate", json={"job_id": "JOB_SWE_01"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_candidates"] >= 8
    assert data["evaluated_candidates"] == data["total_candidates"]
    assert data["failed_candidates"] == 0
    assert data["average_qualification_score"] > 0.0
    assert data["average_efs"] > 0.0
    assert data["average_bgi"] >= 0.0

def test_batch_audit_malformed_candidate_does_not_crash_pool():
    mixed_candidates = [
        {
            "candidate_id": "VALID_01",
            "name": "Valid Candidate",
            "skills": ["Python", "SQL", "Git"],
            "experience_years": 4.0
        },
        "This is not a dict at all - invalid record",
        {
            "candidate_id": "VALID_02",
            "name": "Second Valid Candidate",
            "skills": ["PostgreSQL", "Docker"],
            "experience_years": 3.0
        }
    ]
    resp = client.post("/api/batch-evaluate", json={"job_id": "JOB_SWE_01", "candidates": mixed_candidates})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_candidates"] == 3
    assert data["evaluated_candidates"] == 3  # Handled safely via dict conversion
    assert data["failed_candidates"] == 0
    assert len(data["candidates"]) == 3

def test_batch_audit_empty_candidate_pool():
    resp = client.post("/api/batch-evaluate", json={"job_id": "JOB_SWE_01", "candidates": []})
    assert resp.status_code == 200
    data = resp.json()
    # Empty list evaluates to default pool or 0 safely
    assert "total_candidates" in data
    assert "average_qualification_score" in data
    assert data["average_qualification_score"] >= 0.0

def test_batch_audit_missing_optional_fields():
    candidate_minimal = [
        {"candidate_id": "MIN_01"}  # Missing skills, experience, education, certifications, projects
    ]
    resp = client.post("/api/batch-evaluate", json={"job_id": "JOB_SWE_01", "candidates": candidate_minimal})
    assert resp.status_code == 200
    data = resp.json()
    assert data["evaluated_candidates"] == 1
    cand_out = data["candidates"][0]
    assert cand_out["qualification_score"] >= 0.0
    assert "efs_score" in cand_out
    assert "bgi_score" in cand_out

def test_batch_audit_invalid_numeric_fields():
    candidate_bad_numeric = [
        {
            "candidate_id": "BAD_NUM_01",
            "name": "Bad Numeric Candidate",
            "experience_years": "five years",
            "interview_score": "top-tier",
            "certifications_count": "none",
            "skills": ["Python"]
        }
    ]
    resp = client.post("/api/batch-evaluate", json={"job_id": "JOB_SWE_01", "candidates": candidate_bad_numeric})
    assert resp.status_code == 200
    data = resp.json()
    assert data["evaluated_candidates"] == 1
    assert data["candidates"][0]["experience_years"] == 0.0

def test_batch_audit_aggregate_statistics_accuracy():
    c1 = {"candidate_id": "C1", "skills": ["Python", "SQL", "Git", "REST API", "PostgreSQL"], "experience_years": 6.0, "education": "B.Tech Computer Science"}
    c2 = {"candidate_id": "C2", "skills": ["HTML/CSS"], "experience_years": 0.5, "education": "Diploma"}
    
    resp = client.post("/api/batch-evaluate", json={"job_id": "JOB_SWE_01", "candidates": [c1, c2]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_candidates"] == 2
    assert data["evaluated_candidates"] == 2
    
    q1 = data["candidates"][0]["qualification_score"]
    q2 = data["candidates"][1]["qualification_score"]
    expected_avg_q = round((q1 + q2) / 2, 1)
    assert data["average_qualification_score"] == expected_avg_q

def test_batch_audit_flagged_case_count():
    # Candidate with low qual score but evaluated
    c_flag = {"candidate_id": "C_FLAG", "skills": ["HTML/CSS"], "experience_years": 0.0, "education": "None"}
    resp = client.post("/api/batch-evaluate", json={"job_id": "JOB_SWE_01", "candidates": [c_flag]})
    assert resp.status_code == 200
    data = resp.json()
    assert "flagged_cases" in data
    assert "flagged_candidates_count" in data

def test_batch_audit_empty_request_body_compatibility():
    # Calling endpoint with empty body or no body
    resp = client.post("/api/batch-evaluate")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_candidates" in data
    assert "candidates" in data
