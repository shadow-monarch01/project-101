"""
AI Hiring Intelligence - Qualification & Skill Gap Engine
Handles Job Description criteria parsing, skill matching (Required, Preferred, Additional),
skill gap analysis, and configurable multi-criteria qualification scoring.
"""

from typing import Dict, List, Any, Optional, Set
import re

DEFAULT_JOB_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "JOB_SWE_01": {
        "job_id": "JOB_SWE_01",
        "title": "Senior Python Backend Engineer",
        "department": "Engineering",
        "required_skills": ["Python", "SQL", "REST API", "Git", "PostgreSQL"],
        "preferred_skills": ["FastAPI", "Docker", "Kubernetes", "Microservices"],
        "minimum_experience": 4.0,
        "required_education": "B.Tech/B.S. in Computer Science or related field",
        "required_certifications": ["AWS Certified Cloud Practitioner"],
        "description": "Looking for a Senior Python Backend Engineer to build high-scale distributed microservices, REST APIs, and database architectures."
    },
    "JOB_FULLSTACK_02": {
        "job_id": "JOB_FULLSTACK_02",
        "title": "Full Stack Web Developer",
        "department": "Product",
        "required_skills": ["JavaScript", "React", "Node.js", "SQL", "HTML/CSS"],
        "preferred_skills": ["TypeScript", "Next.js", "TailwindCSS", "GraphQL"],
        "minimum_experience": 2.0,
        "required_education": "B.S. in Computer Science, IT, or equivalent experience",
        "required_certifications": [],
        "description": "Responsible for designing and deploying end-to-end full stack web applications with responsive user interfaces and robust APIs."
    },
    "JOB_DEVOPS_03": {
        "job_id": "JOB_DEVOPS_03",
        "title": "Cloud DevOps & Platform Engineer",
        "department": "Infrastructure",
        "required_skills": ["AWS", "Terraform", "Docker", "CI/CD", "Linux"],
        "preferred_skills": ["Kubernetes", "Jenkins", "Python", "Prometheus"],
        "minimum_experience": 3.0,
        "required_education": "B.Tech/B.S. in Engineering, Information Systems or equivalent",
        "required_certifications": ["AWS Solutions Architect"],
        "description": "Lead infrastructure as code deployment, cloud scaling, Kubernetes orchestration, and automated CI/CD pipelines."
    },
    "JOB_DATA_04": {
        "job_id": "JOB_DATA_04",
        "title": "Data Scientist & Machine Learning Engineer",
        "department": "AI & Analytics",
        "required_skills": ["Python", "Machine Learning", "SQL", "Pandas", "Scikit-learn"],
        "preferred_skills": ["PyTorch", "NLP", "BigQuery", "Deep Learning"],
        "minimum_experience": 3.0,
        "required_education": "M.S. or B.Tech in Data Science, CS, Mathematics or Statistics",
        "required_certifications": ["TensorFlow Developer"],
        "description": "Develop predictive ML pipelines, statistical modeling, feature engineering, and generative AI integrations."
    }
}

DEFAULT_SCORING_WEIGHTS: Dict[str, float] = {
    "required_skills": 0.40,
    "preferred_skills": 0.10,
    "experience": 0.25,
    "education": 0.15,
    "certifications": 0.05,
    "projects": 0.05
}

def normalize_skill_string(skill: str) -> str:
    s = str(skill).strip().lower()
    s = re.sub(r'[\/\-_]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s

def parse_skills_list(skills_input: Any) -> List[str]:
    if isinstance(skills_input, list):
        return [str(s).strip() for s in skills_input if str(s).strip()]
    if isinstance(skills_input, str):
        parts = re.split(r'[,;|\n]+', skills_input)
        return [p.strip() for p in parts if p.strip()]
    return []

def match_skills(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: Optional[List[str]] = None
) -> Dict[str, Any]:
    cand_norm_map = {normalize_skill_string(s): s for s in candidate_skills if s}
    req_norm_map = {normalize_skill_string(s): s for s in required_skills if s}
    pref_norm_map = {normalize_skill_string(s): s for s in (preferred_skills or []) if s}

    cand_set = set(cand_norm_map.keys())
    req_set = set(req_norm_map.keys())
    pref_set = set(pref_norm_map.keys())

    matched_req_keys = cand_set.intersection(req_set)
    matched_required = [req_norm_map[k] for k in matched_req_keys]

    missing_req_keys = req_set - cand_set
    missing_required = [req_norm_map[k] for k in missing_req_keys]

    matched_pref_keys = cand_set.intersection(pref_set)
    matched_preferred = [pref_norm_map[k] for k in matched_pref_keys]

    missing_pref_keys = pref_set - cand_set
    missing_preferred = [pref_norm_map[k] for k in missing_pref_keys]

    all_job_keys = req_set.union(pref_set)
    additional_keys = cand_set - all_job_keys
    additional_skills = [cand_norm_map[k] for k in additional_keys]

    total_req = max(1, len(required_skills))
    req_match_ratio = len(matched_required) / total_req
    req_match_pct = round(req_match_ratio * 100.0, 1)

    total_pref = len(preferred_skills or [])
    pref_match_ratio = (len(matched_preferred) / total_pref) if total_pref > 0 else 1.0
    pref_match_pct = round(pref_match_ratio * 100.0, 1)

    skill_gap_ratio = len(missing_required) / total_req
    skill_gap_pct = round(skill_gap_ratio * 100.0, 1)

    return {
        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "additional_skills": additional_skills,
        "required_skills_count": len(required_skills),
        "matched_required_count": len(matched_required),
        "missing_required_count": len(missing_required),
        "required_match_percentage": req_match_pct,
        "preferred_match_percentage": pref_match_pct,
        "skill_gap_percentage": skill_gap_pct
    }

def evaluate_experience_match(
    candidate_exp: float,
    minimum_exp: float
) -> Dict[str, Any]:
    cand_exp = max(0.0, float(candidate_exp or 0.0))
    min_exp = max(0.0, float(minimum_exp or 0.0))

    if min_exp <= 0.0:
        exp_score = 100.0
    else:
        ratio = cand_exp / min_exp
        if ratio >= 1.0:
            exp_score = 100.0
        else:
            exp_score = round(ratio * 100.0, 1)

    return {
        "candidate_experience_years": cand_exp,
        "minimum_required_years": min_exp,
        "experience_match_percentage": exp_score,
        "is_sufficient": cand_exp >= min_exp,
        "experience_gap_years": round(max(0.0, min_exp - cand_exp), 1)
    }

def evaluate_education_relevance(
    candidate_education: str,
    required_education: str = ""
) -> float:
    edu_str = str(candidate_education or "").lower()
    if any(k in edu_str for k in ["ph.d", "doctorate"]):
        return 100.0
    if any(k in edu_str for k in ["m.s.", "m.tech", "master", "mca"]):
        return 95.0
    if any(k in edu_str for k in ["b.tech", "b.e.", "b.s.", "bachelor", "bca"]):
        return 85.0
    if any(k in edu_str for k in ["associate", "diploma"]):
        return 65.0
    if any(k in edu_str for k in ["bootcamp", "certificate"]):
        return 60.0
    return 50.0

def compute_overall_qualification_score(
    candidate_data: Dict[str, Any],
    job_requirements: Optional[Dict[str, Any]] = None,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    job = job_requirements or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    w = weights or DEFAULT_SCORING_WEIGHTS

    cand_skills = parse_skills_list(candidate_data.get("skills", candidate_data.get("technical_skills", [])))
    req_skills = parse_skills_list(job.get("required_skills", []))
    pref_skills = parse_skills_list(job.get("preferred_skills", []))

    skill_analysis = match_skills(cand_skills, req_skills, pref_skills)
    cand_exp = float(candidate_data.get("experience_years", candidate_data.get("experience", 0)) or 0)
    min_exp = float(job.get("minimum_experience", 2.0))
    exp_analysis = evaluate_experience_match(cand_exp, min_exp)

    cand_edu = str(candidate_data.get("education", candidate_data.get("degree", "")))
    req_edu = str(job.get("required_education", ""))
    edu_score = evaluate_education_relevance(cand_edu, req_edu)

    # Robust certification parsing
    certs = candidate_data.get("certifications_count", candidate_data.get("certifications", 0))
    if isinstance(certs, list):
        cert_count = len(certs)
    elif isinstance(certs, str):
        cert_count = len([c for c in re.split(r'[,;|\n]+', certs) if c.strip()]) if certs.strip() else 0
    else:
        try:
            cert_count = int(certs or 0)
        except (ValueError, TypeError):
            cert_count = 0

    cert_score = min(100.0, cert_count * 50.0) if cert_count > 0 else 40.0

    interview_score = float(candidate_data.get("interview_score", candidate_data.get("score", 75)) or 75)
    proj_score = min(100.0, max(0.0, interview_score))

    req_skill_contrib = (w.get("required_skills", 0.40) * skill_analysis["required_match_percentage"])
    pref_skill_contrib = (w.get("preferred_skills", 0.10) * skill_analysis["preferred_match_percentage"])
    exp_contrib = (w.get("experience", 0.25) * exp_analysis["experience_match_percentage"])
    edu_contrib = (w.get("education", 0.15) * edu_score)
    cert_contrib = (w.get("certifications", 0.05) * cert_score)
    proj_contrib = (w.get("projects", 0.05) * proj_score)

    overall_score = round(
        req_skill_contrib + pref_skill_contrib + exp_contrib + edu_contrib + cert_contrib + proj_contrib,
        1
    )
    overall_score = max(0.0, min(100.0, overall_score))

    if overall_score >= 85.0:
        expected_decision = "STRONG_HIRE"
    elif overall_score >= 75.0:
        expected_decision = "HIRE"
    elif overall_score >= 60.0:
        expected_decision = "INTERVIEW"
    else:
        expected_decision = "REJECT"

    return {
        "qualification_score": overall_score,
        "expected_decision": expected_decision,
        "component_breakdown": {
            "required_skills_score": skill_analysis["required_match_percentage"],
            "preferred_skills_score": skill_analysis["preferred_match_percentage"],
            "experience_score": exp_analysis["experience_match_percentage"],
            "education_score": edu_score,
            "certifications_score": cert_score,
            "project_performance_score": proj_score
        },
        "weights_applied": w,
        "skill_analysis": skill_analysis,
        "experience_analysis": exp_analysis,
        "candidate_id": candidate_data.get("candidate_id", "UNKNOWN"),
        "candidate_name": candidate_data.get("name", "Candidate"),
        "job_title": job.get("title", "Software Engineer")
    }
