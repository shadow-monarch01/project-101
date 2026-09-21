"""
AI Hiring Intelligence System - Evidence-Based Candidate Background Investigation (BI) Test Suite
Covers:
1. Investigation of Education
2. Investigation of Experience
3. Investigation of Certifications
4. Investigation of Skills (with canonical normalization)
5. Investigation of Projects
6. Investigation of Employment History
7. Internal Consistency & Contradiction Detection
8. Overall Status Computation (VERIFIED, PARTIAL, INSUFFICIENT, INCONSISTENT)
9. Evidence Coverage Score (0-100)
10. BI Disclaimer Presence & Grounding
11. REST API endpoint /api/background-investigation
12. Batch & Dossier Integration with BI
"""

import pytest
from fastapi.testclient import TestClient

from app import app
from modules.background_investigation import (
    investigate_education,
    investigate_experience,
    investigate_certifications,
    investigate_skills,
    investigate_projects,
    investigate_employment_history,
    check_information_consistency,
    calculate_background_status,
    run_background_investigation,
    BI_DISCLAIMER
)
from modules.qualifications import DEFAULT_JOB_TEMPLATES

client = TestClient(app)

def test_investigate_education_supported():
    cand = {"education": "B.Tech Computer Science", "institution": "State University"}
    res = investigate_education(cand)
    assert res["status"] == "SUPPORTED"
    assert res["degree_level"] == "Bachelor's Degree"
    assert res["is_supported"] is True
    assert "State University" in res["evidence"]

def test_investigate_education_missing():
    cand = {"skills": ["Python"]}
    res = investigate_education(cand)
    assert res["status"] == "MISSING_EVIDENCE"
    assert res["is_supported"] is False

def test_investigate_experience_supported():
    cand = {"experience_years": 5.0, "role": "Senior Engineer"}
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    res = investigate_experience(cand, job)
    assert res["status"] == "SUPPORTED"
    assert res["claimed_years"] == 5.0
    assert res["is_supported"] is True

def test_investigate_experience_missing():
    cand = {"skills": ["Python"]}
    res = investigate_experience(cand)
    assert res["status"] == "MISSING_EVIDENCE"
    assert res["is_supported"] is False

def test_investigate_experience_contradiction():
    cand = {
        "experience_years": 8.0,
        "employment_history": [
            {"role": "Dev", "company": "Co A", "duration_years": 1.0}
        ]
    }
    res = investigate_experience(cand)
    assert res["status"] == "CONTRADICTED"
    assert res["is_supported"] is False
    assert res["inconsistency"] is not None

def test_investigate_certifications_present_and_absent():
    cand_with_certs = {"certifications": "AWS Solutions Architect, CKA"}
    res1 = investigate_certifications(cand_with_certs)
    assert res1["status"] == "SUPPORTED"
    assert res1["count"] == 2

    cand_no_certs = {"skills": ["Python"]}
    res2 = investigate_certifications(cand_no_certs)
    assert res2["status"] in ["NOT_AVAILABLE", "SUPPORTED"]

def test_investigate_skills_corroboration():
    cand = {
        "skills": "python, postgres, git, fast api",
        "projects": "Built FastAPI and PostgreSQL data services in Python"
    }
    res = investigate_skills(cand)
    assert res["status"] == "SUPPORTED"
    assert "Python" in res["canonical_skills"]
    assert "PostgreSQL" in res["canonical_skills"]
    assert len(res["corroborated_skills"]) >= 1

def test_investigate_projects_and_history():
    cand = {
        "projects": "Distributed real-time data streaming pipeline",
        "employment_history": [
            {"role": "Backend Engineer", "company": "Tech Corp", "duration_years": 3.0},
            {"role": "Junior Dev", "company": "StartUp LLC", "duration_years": 2.0}
        ]
    }
    proj_res = investigate_projects(cand)
    emp_res = investigate_employment_history(cand)
    assert proj_res["status"] == "SUPPORTED"
    assert emp_res["status"] == "SUPPORTED"
    assert emp_res["record_count"] == 2

def test_timeline_inconsistency_detection():
    cand = {
        "name": "Anomalous Candidate",
        "graduation_year": 2025,
        "experience_years": 10.0,  # 10 years experience claimed immediately after 2025 graduation
        "education": "B.Tech Computer Science"
    }
    res = check_information_consistency(cand)
    assert res["is_consistent"] is False
    assert len(res["inconsistencies"]) >= 1
    assert "Timeline Anomaly" in res["inconsistencies"][0]

def test_full_background_investigation_verified_status():
    cand = {
        "candidate_id": "SWE_001",
        "name": "Priya Sharma",
        "skills": "Python, SQL, PostgreSQL, REST API, Git, FastAPI, Docker",
        "experience_years": 6.0,
        "education": "B.Tech Computer Science",
        "institution": "IIT Madras",
        "certifications": "AWS Solutions Architect",
        "projects": "Distributed microservices backend",
        "employment_history": [
            {"role": "Senior Engineer", "company": "Acme Corp", "duration_years": 4.0},
            {"role": "Software Engineer", "company": "Beta LLC", "duration_years": 2.0}
        ]
    }
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    res = run_background_investigation(cand, job)

    assert res["overall_status"] == "VERIFIED_FROM_PROVIDED_EVIDENCE"
    assert res["evidence_coverage_percentage"] >= 90.0
    assert res["is_consistent"] is True
    assert res["disclaimer"] == BI_DISCLAIMER
    assert len(res["inconsistencies"]) == 0

def test_api_background_investigation_endpoint():
    payload = {
        "candidate": {
            "candidate_id": "API_BI_01",
            "name": "David Chen",
            "skills": ["Python", "SQL", "Git", "PostgreSQL"],
            "experience_years": 4.0,
            "education": "B.S. Computer Science"
        },
        "job": {
            "title": "Senior Python Backend Engineer",
            "required_skills": ["Python", "SQL", "Git", "PostgreSQL"],
            "minimum_experience": 3.0
        }
    }
    resp = client.post("/api/background-investigation", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_status" in data
    assert "evidence_coverage_percentage" in data
    assert "investigations" in data
    assert "disclaimer" in data
    assert data["overall_status"] in [
        "VERIFIED_FROM_PROVIDED_EVIDENCE",
        "PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE"
    ]

def test_background_investigation_insufficient_evidence():
    cand_empty = {"candidate_id": "EMPTY_01"}
    res = run_background_investigation(cand_empty)
    assert res["overall_status"] == "INSUFFICIENT_EVIDENCE"
    assert res["evidence_coverage_percentage"] < 70.0


# ============================================================================
# Core Specification Tests: TEST 1 - TEST 6
# ============================================================================

def test_1_all_evidence_supported_verified():
    """TEST 1: All relevant declared BI information is supported -> VERIFIED_FROM_PROVIDED_EVIDENCE"""
    cand = {
        "candidate_id": "TEST_01",
        "name": "Sarah Connor",
        "skills": "Python, SQL, PostgreSQL, REST API, Git",
        "experience_years": 5.0,
        "education": "B.Tech Computer Science",
        "institution": "MIT",
        "certifications": "AWS Developer",
        "projects": "API Microservices",
        "employment_history": [
            {"role": "Backend Engineer", "company": "Tech Corp", "duration_years": 5.0}
        ]
    }
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    res = run_background_investigation(cand, job)
    assert res["overall_status"] == "VERIFIED_FROM_PROVIDED_EVIDENCE"
    assert res["is_consistent"] is True
    assert res["unsupported_claims_count"] == 0
    assert len(res["inconsistencies"]) == 0
    assert res["evidence_coverage_percentage"] >= 85.0


def test_2_some_unsupported_qualification_evidence_partial():
    """TEST 2: Some unsupported qualification evidence -> PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE"""
    cand = {
        "candidate_id": "TEST_02",
        "name": "Alex Mercer",
        "skills": "Python, SQL",
        "experience_years": 4.0,
        "education": "B.S. Computer Science"
    }
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    # Evidence traceability with 2 unsupported qualification claims (e.g. JavaScript, Node.js)
    evidence_traceability = {
        "claims": [
            {"claim": "Candidate possesses Python competency", "source_field": "skills", "status": "SUPPORTED"},
            {"claim": "Candidate possesses JavaScript competency", "source_field": "skills", "status": "UNSUPPORTED"},
            {"claim": "Candidate possesses Node.js competency", "source_field": "skills", "status": "UNSUPPORTED"}
        ]
    }
    res = run_background_investigation(cand, job, evidence_traceability=evidence_traceability)
    assert res["overall_status"] == "PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE"
    assert res["unsupported_claims_count"] == 2
    assert "Candidate possesses JavaScript competency" in res["unsupported_qualification_claims"]


def test_3_insufficient_candidate_evidence():
    """TEST 3: Insufficient candidate evidence -> INSUFFICIENT_EVIDENCE"""
    cand_sparse = {
        "candidate_id": "TEST_03",
        "name": "Sparse Profile"
    }
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    res = run_background_investigation(cand_sparse, job)
    assert res["overall_status"] == "INSUFFICIENT_EVIDENCE"
    assert res["evidence_coverage_percentage"] <= 70.0


def test_4_direct_contradiction_inconsistency_detected():
    """TEST 4: Direct contradiction -> INCONSISTENCY_DETECTED"""
    cand_inconsistent = {
        "candidate_id": "TEST_04",
        "name": "Contradictory Candidate",
        "skills": "Python, SQL",
        "experience_years": 8.0,
        "employment_history": [
            {"role": "Engineer", "company": "A", "duration_years": 1.0}
        ],
        "education": "B.Tech Computer Science"
    }
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    res = run_background_investigation(cand_inconsistent, job)
    assert res["overall_status"] == "INCONSISTENCY_DETECTED"
    assert res["is_consistent"] is False
    assert len(res["inconsistencies"]) >= 1


def test_5_unsupported_ai_explanation_claims_prevent_verified():
    """TEST 5: Unsupported AI explanation claims must NOT allow BI to become VERIFIED."""
    cand = {
        "candidate_id": "TEST_05",
        "name": "Jane Doe",
        "skills": "Python, SQL, PostgreSQL",
        "experience_years": 5.0,
        "education": "B.Tech Computer Science",
        "institution": "Stanford",
        "certifications": "AWS Certified",
        "projects": "Cloud Backend",
        "employment_history": [
            {"role": "Senior Dev", "company": "Beta Corp", "duration_years": 5.0}
        ]
    }
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    # AI explanation hallucinating that candidate knows Rust and Golang
    explanation = "Candidate is strong in Python and PostgreSQL. Candidate possesses Rust competency and Golang competency."
    res = run_background_investigation(cand, job, explanation=explanation)
    assert res["overall_status"] != "VERIFIED_FROM_PROVIDED_EVIDENCE"
    assert res["overall_status"] == "PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE"
    assert res["unsupported_claims_count"] >= 1


def test_6_multiple_candidates_calculated_independently():
    """TEST 6: Multiple candidates in pool evaluated independently with correct respective statuses."""
    candidates = [
        # Candidate A: fully verified
        {
            "candidate_id": "POOL_A",
            "name": "Candidate A",
            "skills": "Python, SQL, PostgreSQL, REST API, Git",
            "experience_years": 5.0,
            "education": "B.Tech Computer Science",
            "certifications": "AWS Solutions Architect",
            "projects": "Microservices",
            "employment_history": [{"role": "Dev", "company": "Co", "duration_years": 5.0}]
        },
        # Candidate B: unsupported explanation claims
        {
            "candidate_id": "POOL_B",
            "name": "Candidate B",
            "skills": "Python, SQL",
            "experience_years": 4.0,
            "education": "B.S. Computer Science",
            "explanation": "Candidate has strong Python and possesses JavaScript competency and Docker competency."
        },
        # Candidate C: timeline anomaly
        {
            "candidate_id": "POOL_C",
            "name": "Candidate C",
            "skills": "Python",
            "graduation_year": 2025,
            "experience_years": 10.0,
            "education": "B.Tech Computer Science"
        },
        # Candidate D: sparse / insufficient
        {
            "candidate_id": "POOL_D",
            "name": "Candidate D"
        }
    ]
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]

    statuses = [run_background_investigation(c, job)["overall_status"] for c in candidates]
    
    assert statuses[0] == "VERIFIED_FROM_PROVIDED_EVIDENCE"
    assert statuses[1] == "PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE"
    assert statuses[2] == "INCONSISTENCY_DETECTED"
    assert statuses[3] == "INSUFFICIENT_EVIDENCE"
