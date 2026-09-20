"""
Test Suite for Priority 1 Improvements:
Evidence Traceability, Enhanced EFS, Qualification Semantics, BGI Refactor, Skill Normalization, and API Endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app import app
from modules.skill_normalization import canonicalize_skill, normalize_skill
from modules.skill_analysis import match_skills
from modules.qualifications import (
    compute_overall_qualification_score,
    evaluate_projects_score,
    evaluate_education_relevance,
    DEFAULT_JOB_TEMPLATES
)
from modules.evidence import (
    extract_claims_from_explanation,
    evaluate_evidence_traceability
)
from modules.faithfulness import evaluate_faithfulness_instance
from modules.bgi import compute_bgi, check_decision_consistency
from modules.decision_consistency import check_pairwise_consistency

client = TestClient(app)

# ============================================================================
# 1. Evidence Traceability Tests (Items 1 - 6)
# ============================================================================

def test_evidence_supported_skill_claim():
    cand = {"skills": ["Python", "PostgreSQL", "Docker"], "experience_years": 4.0}
    explanation = "The candidate has strong Python skills and experience."
    res = evaluate_evidence_traceability(explanation, cand)
    assert res["supported_claims"] >= 1
    assert any(c["status"] == "SUPPORTED" and "Python" in c["claim"] for c in res["claims"])

def test_evidence_unsupported_skill_claim():
    cand = {"skills": ["Python", "SQL"], "experience_years": 3.0}
    job = {"required_skills": ["Kubernetes", "Python"]}
    explanation = "The candidate demonstrates strong Kubernetes skills."
    res = evaluate_evidence_traceability(explanation, cand, job)
    assert res["unsupported_claims"] >= 1
    assert any(c["status"] == "UNSUPPORTED" and "Kubernetes" in c["claim"] for c in res["claims"])

def test_evidence_contradicted_experience_claim():
    cand = {"skills": ["Python"], "experience_years": 3.0}
    explanation = "The candidate brings over 8 years of software experience."
    res = evaluate_evidence_traceability(explanation, cand)
    assert res["contradicted_claims"] >= 1
    assert any(c["status"] == "CONTRADICTED" and "8.0" in c["claim"] for c in res["claims"])

def test_evidence_supported_education_claim():
    cand = {"skills": ["Python"], "education": "B.Tech Computer Science", "experience_years": 4.0}
    explanation = "Holds a relevant B.Tech degree in Computer Science."
    res = evaluate_evidence_traceability(explanation, cand)
    assert res["supported_claims"] >= 1
    assert any(c["status"] == "SUPPORTED" and "B.TECH" in c["claim"] for c in res["claims"])

def test_evidence_empty_explanation():
    cand = {"skills": ["Python"], "experience_years": 4.0}
    res = evaluate_evidence_traceability("", cand)
    assert res["total_claims"] == 0
    assert res["evidence_grounding_score"] == 0.0

def test_evidence_multiple_claims():
    cand = {
        "skills": ["Python", "SQL", "Git"],
        "experience_years": 4.0,
        "education": "B.Tech Computer Science",
        "certifications": "AWS Certified"
    }
    explanation = "Candidate has 4 years of experience, strong Python competencies, holds an AWS certified credential, but lacks Docker."
    res = evaluate_evidence_traceability(explanation, cand)
    assert res["total_claims"] >= 3
    assert res["supported_claims"] >= 2

# ============================================================================
# 2. Enhanced EFS Tests (Items 7 - 10)
# ============================================================================

def test_efs_high_faithfulness_explanation():
    cand = {"skills": ["Python", "SQL", "REST API", "Git"], "experience_years": 5.0}
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    skill_analysis = match_skills(cand["skills"], job["required_skills"])
    explanation = "The candidate has 5 years of experience with verified Python, SQL, REST API, and Git skills."
    
    res = evaluate_faithfulness_instance(explanation, 90.0, "HIRE", skill_analysis, candidate_data=cand, job_requirements=job)
    assert res["faithfulness_score"] >= 80.0
    assert res["classification"] == "High Faithfulness"
    assert "breakdown" in res

def test_efs_unsupported_claim_penalty():
    cand = {"skills": ["Python"], "experience_years": 2.0}
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    skill_analysis = match_skills(cand["skills"], job["required_skills"])
    
    # Mentions skills candidate does not have
    expl_grounded = "Candidate has Python experience."
    expl_unsupported = "Candidate has Python, Kubernetes, Redis, GraphQL, and C++ experience."
    
    res_g = evaluate_faithfulness_instance(expl_grounded, 60.0, "INTERVIEW", skill_analysis, candidate_data=cand, job_requirements=job)
    res_u = evaluate_faithfulness_instance(expl_unsupported, 60.0, "INTERVIEW", skill_analysis, candidate_data=cand, job_requirements=job)
    
    assert res_u["faithfulness_score"] < res_g["faithfulness_score"]

def test_efs_contradicted_claim_penalty():
    cand = {"skills": ["Python", "SQL"], "experience_years": 5.0}
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    skill_analysis = match_skills(cand["skills"], job["required_skills"])
    
    # Falsely claims candidate lacks Python (which candidate actually has!)
    expl_contradicted = "Rejected because candidate lacks Python and SQL skills."
    res = evaluate_faithfulness_instance(expl_contradicted, 80.0, "REJECT", skill_analysis, candidate_data=cand, job_requirements=job)
    
    assert res["contradicted_claims"] >= 1
    assert res["faithfulness_score"] < 60.0

def test_efs_breakdown_components_calculated():
    cand = {"skills": ["Python", "SQL"], "experience_years": 4.0, "education": "B.Tech"}
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    res = evaluate_faithfulness_instance("Candidate has 4 years experience with Python.", 85.0, "HIRE", candidate_data=cand, job_requirements=job)
    
    bd = res["breakdown"]
    assert "skill_grounding" in bd
    assert "experience_grounding" in bd
    assert "education_grounding" in bd
    assert "decision_grounding" in bd
    for k, v in bd.items():
        assert 0.0 <= v <= 100.0

# ============================================================================
# 3. Qualification Scoring Semantics Tests (Items 11 - 13)
# ============================================================================

def test_qualification_project_score_not_derived_from_interview_score():
    cand = {
        "candidate_id": "C_TEST_01",
        "skills": ["Python", "SQL", "Git", "REST API", "PostgreSQL"],
        "experience_years": 5.0,
        "education": "B.Tech Computer Science",
        "projects": "High-throughput microservices",
        "projects_score": 90.0,
        "interview_score": 30.0  # Low interview score must NOT drag down project score
    }
    res = compute_overall_qualification_score(cand, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"])
    breakdown = res["component_breakdown"]
    assert breakdown["projects_score"] == 90.0
    assert breakdown["projects_score"] != cand["interview_score"]

def test_qualification_missing_project_data_handled_safely():
    cand_no_proj = {
        "candidate_id": "C_TEST_02",
        "skills": ["Python", "SQL"],
        "experience_years": 3.0,
        "education": "B.S."
    }
    res = compute_overall_qualification_score(cand_no_proj, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"])
    assert res["qualification_score"] > 0
    assert "projects_score" in res["component_breakdown"]
    assert res["component_breakdown"]["projects_score"] == 60.0  # Neutral baseline

def test_qualification_technical_interview_remains_separate():
    cand = {
        "skills": ["Python"],
        "experience_years": 3.0,
        "technical_interview_score": 88.0,
        "projects": "Personal portfolio"
    }
    res = compute_overall_qualification_score(cand, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"])
    assert res["technical_interview_score"] == 88.0
    assert "technical_interview_score" in res["component_breakdown"]
    assert res["component_breakdown"]["projects_score"] != 88.0

# ============================================================================
# 4. BGI Refactor Tests (Items 14 - 19)
# ============================================================================

def test_bgi_zero_gap_case():
    res = compute_bgi(
        qualification_score=85.0,
        expected_decision="STRONG_HIRE",
        ai_decision="STRONG_HIRE",
        ai_score=85.0,
        efs_score=100.0
    )
    assert res["bgi_score"] == 0.0
    assert res["classification"] == "Very Low Gap"
    assert res["is_audit_indicator"] is True

def test_bgi_qualification_gap_case():
    res = compute_bgi(
        qualification_score=90.0,
        expected_decision="HIRE",
        ai_decision="HIRE",
        ai_score=50.0,  # AI score diverged from qualification
        efs_score=95.0
    )
    assert res["components"]["qualification_gap"] == 40.0
    assert res["bgi_score"] > 15.0

def test_bgi_decision_gap_case():
    res = compute_bgi(
        qualification_score=90.0,
        expected_decision="STRONG_HIRE",
        ai_decision="REJECT",  # Massive rank distance
        ai_score=40.0,
        efs_score=90.0
    )
    assert res["components"]["decision_gap"] == 100.0
    assert res["bgi_score"] >= 50.0
    assert res["flagged_for_audit"] is True

def test_bgi_explanation_gap_case():
    res = compute_bgi(
        qualification_score=80.0,
        expected_decision="HIRE",
        ai_decision="HIRE",
        ai_score=80.0,
        efs_score=30.0  # Low EFS -> High explanation gap
    )
    assert res["components"]["explanation_gap"] == 70.0
    assert res["bgi_score"] >= 14.0

def test_bgi_configurable_weights():
    custom_w = {"qualification_gap": 0.80, "decision_gap": 0.10, "explanation_gap": 0.10}
    res = compute_bgi(
        qualification_score=90.0,
        expected_decision="HIRE",
        ai_decision="HIRE",
        ai_score=50.0,
        weights=custom_w
    )
    assert res["weights"]["qualification_gap"] == 0.80
    assert res["weights"]["decision_gap"] == 0.10

def test_bgi_score_remains_in_0_to_100():
    for q in [0.0, 50.0, 100.0]:
        for s in [0.0, 50.0, 100.0]:
            for efs in [0.0, 50.0, 100.0]:
                res = compute_bgi(q, "REJECT", "STRONG_HIRE", s, efs)
                assert 0.0 <= res["bgi_score"] <= 100.0

# ============================================================================
# 5. Skill Normalization Tests (Items 20 - 24)
# ============================================================================

def test_skill_normalization_postgres_aliases():
    for alias in ["postgres", "PostgreSQL", "postgressql", "pg", "psql"]:
        assert canonicalize_skill(alias) == "PostgreSQL"

def test_skill_normalization_javascript_aliases():
    for alias in ["js", "JS", "javascript", "vanilla js"]:
        assert canonicalize_skill(alias) == "JavaScript"

def test_skill_normalization_rest_api_aliases():
    for alias in ["rest", "REST API", "restful", "RESTful API"]:
        assert canonicalize_skill(alias) == "REST API"

def test_skill_normalization_kubernetes_aliases():
    for alias in ["k8s", "kubernetes", "kube"]:
        assert canonicalize_skill(alias) == "Kubernetes"

def test_skill_normalization_unknown_skill_remains_usable():
    unknown = "Custom proprietary lib"
    norm = normalize_skill(unknown)
    assert norm["input"] == unknown
    assert norm["canonical"] == unknown

# ============================================================================
# 6. API Endpoints Tests (Items 25 - 29)
# ============================================================================

def test_api_evidence_endpoint():
    payload = {
        "candidate_id": "SWE_001",
        "job_id": "JOB_SWE_01",
        "explanation": "The candidate has strong Python and PostgreSQL skills with 5 years experience."
    }
    resp = client.post("/api/evidence", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "claims" in data
    assert "evidence_grounding_score" in data
    assert "supported_claims" in data

def test_api_invalid_candidate():
    resp = client.get("/api/report/NON_EXISTENT_CANDIDATE_99999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()

def test_api_invalid_dataset():
    resp = client.post("/api/select_dataset", json={"filename": "non_existent_file.csv"})
    assert resp.status_code == 404

def test_api_malformed_statistics_request():
    resp = client.post("/api/statistics", json={
        "test_type": "invalid_test_type_xyz",
        "original_values": [1, 2],
        "modified_values": [1, 2]
    })
    assert resp.status_code == 400

def test_api_backward_compatibility_evaluate():
    payload = {
        "candidate": {
            "candidate_id": "SWE_TEST",
            "name": "Alex",
            "skills": ["Python", "SQL", "Git", "REST API", "PostgreSQL"],
            "experience_years": 5.0,
            "education": "B.Tech Computer Science"
        },
        "mode": "Demo Simulation Mode"
    }
    resp = client.post("/api/evaluate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "qualification_score" in data
    assert "score" in data  # Backward compatibility field
    assert "recommendation" in data
    assert "decision" in data
    assert "efs" in data
    assert "bgi" in data
    assert "evidence" in data
    assert "component_breakdown" in data

# ============================================================================
# 7. Regression Tests for Issue 1 & Issue 2
# ============================================================================

def test_skill_matching_mutual_exclusivity():
    cand_skills = ["py", "git", "sqlite", "html/css", "custom_lib"]
    req_skills = ["Python", "SQL", "REST API", "Git", "PostgreSQL"]
    pref_skills = ["FastAPI", "Docker", "Kubernetes", "Microservices"]

    res = match_skills(cand_skills, req_skills, pref_skills)

    matched_req = set(res["matched_required_skills"])
    missing_req = set(res["missing_required_skills"])
    matched_pref = set(res["matched_preferred_skills"])
    missing_pref = set(res["missing_preferred_skills"])
    additional = set(res["additional_skills"])

    # Disjointness checks
    assert matched_req.isdisjoint(missing_req), "Matched and missing required must be disjoint"
    assert matched_req.isdisjoint(additional), "Matched required and additional must be disjoint"
    assert missing_req.isdisjoint(additional), "Missing required and additional must be disjoint"
    assert matched_pref.isdisjoint(additional), "Matched preferred and additional must be disjoint"

    # PostgreSQL must be in missing_req and NOT in additional
    assert "PostgreSQL" in missing_req
    assert "PostgreSQL" not in additional
    assert "PostgreSQL" not in matched_req

def test_james_sterling_exact_skill_breakdown():
    cand_skills = ["Python", "Git", "SQLite", "HTML/CSS"]
    req_skills = ["Python", "SQL", "REST API", "Git", "PostgreSQL"]
    pref_skills = ["FastAPI", "Docker", "Kubernetes", "Microservices"]

    res = match_skills(cand_skills, req_skills, pref_skills)

    assert sorted(res["matched_required_skills"]) == ["Git", "Python"]
    assert sorted(res["missing_required_skills"]) == ["PostgreSQL", "REST API", "SQL"]
    assert sorted(res["additional_skills"]) == ["HTML/CSS", "SQLite"]
    assert res["matched_preferred_skills"] == []

def test_contradictory_experience_claim_detection():
    cand = {
        "candidate_id": "SWE_004",
        "name": "James Sterling",
        "skills": ["Python", "Git", "SQLite", "HTML/CSS"],
        "experience_years": 1.5,
        "education": "B.S. Information Technology"
    }
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]

    # Explanation falsely claiming 6 years when candidate has 1.5
    falsified_explanation = "Candidate exhibits comprehensive competency with verified 6 years background."
    ev_res = evaluate_evidence_traceability(falsified_explanation, cand, job)

    assert ev_res["contradicted_claims"] >= 1
    assert ev_res["has_contradictions"] is True
    assert any(c["status"] == "CONTRADICTED" and "6.0" in c["claim"] for c in ev_res["claims"])

    # EFS should reflect contradiction penalty
    efs_res = evaluate_faithfulness_instance(falsified_explanation, 50.0, "REJECT", candidate_data=cand, job_requirements=job)
    assert efs_res["contradicted_claims"] >= 1
    assert efs_res["faithfulness_score"] < 80.0

def test_api_skill_normalization_endpoint():
    resp = client.post("/api/skill-normalization", json={"skills": ["postgres", "k8s", "js", "fast api"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["normalized_skills"] == ["PostgreSQL", "Kubernetes", "JavaScript", "FastAPI"]

def test_education_relevance_field_of_study():
    job_cs = "B.Tech/B.S. in Computer Science or related field"
    
    score_cs = evaluate_education_relevance("B.S. Computer Science", job_cs)
    score_history = evaluate_education_relevance("B.S. History", job_cs)
    score_fine_arts = evaluate_education_relevance("B.S. Fine Arts", job_cs)
    score_mech = evaluate_education_relevance("B.Tech Mechanical Engineering", job_cs)

    assert score_cs == 85.0
    assert score_history == 51.0
    assert score_fine_arts == 51.0
    assert score_mech == 72.2 or score_mech == 72.0
    assert score_cs > score_mech > score_history

def test_invalid_numeric_data_handling():
    cand_invalid = {
        "candidate_id": "TEST_INVALID_NUMERIC",
        "skills": ["Python", "SQL"],
        "experience_years": "not-a-number",
        "interview_score": "bad",
        "certifications_count": "bad"
    }
    # Direct function evaluation must not crash
    res = compute_overall_qualification_score(cand_invalid, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"])
    assert res["qualification_score"] > 0
    assert res["experience_analysis"]["candidate_experience_years"] == 0.0

    # API endpoint must not crash and return HTTP 200
    resp = client.post("/api/qualification-score", json={"candidate": cand_invalid, "job_id": "JOB_SWE_01"})
    assert resp.status_code == 200
    data = resp.json()
    assert "qualification_score" in data

