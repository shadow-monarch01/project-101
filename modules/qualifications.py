"""
AI Hiring Intelligence - Qualification & Skill Gap Engine
Handles Job Description criteria parsing, skill matching (Required, Preferred, Additional),
skill gap analysis, and configurable multi-criteria qualification scoring.
"""

from typing import Dict, List, Any, Optional, Set
import re
from modules.skill_normalization import (
    canonicalize_skill,
    normalize_skill,
    normalize_skills_list,
    get_canonical_skills
)
from modules.skill_analysis import (
    match_skills,
    parse_skills_list,
    normalize_skill_string
)

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

def evaluate_experience_match(
    candidate_exp: Any,
    minimum_exp: Any
) -> Dict[str, Any]:
    """Computes experience match percentage and gap against minimum job requirement."""
    try:
        cand_exp = max(0.0, float(candidate_exp if candidate_exp is not None else 0.0))
    except (ValueError, TypeError):
        cand_exp = 0.0

    try:
        min_exp = max(0.0, float(minimum_exp if minimum_exp is not None else 0.0))
    except (ValueError, TypeError):
        min_exp = 0.0

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
    """
    Evaluates candidate degree level and technical major relevance against job criteria.
    Factors in degree level (Ph.D., Master's, Bachelor's, Associate, Bootcamp)
    and field-of-study alignment (CS/IT vs. Adjacent STEM vs. Unrelated fields).
    """
    edu_str = str(candidate_education or "").lower().strip()
    if not edu_str:
        return 50.0

    # 1. Degree level base score
    if any(k in edu_str for k in ["ph.d", "phd", "doctorate"]):
        base_score = 100.0
    elif any(k in edu_str for k in ["m.s.", "ms in", "m.tech", "master", "mca", "m.sc", "msc"]):
        base_score = 95.0
    elif any(k in edu_str for k in ["b.tech", "b.e.", "b.s.", "bs in", "bachelor", "bca", "b.sc", "bsc"]):
        base_score = 85.0
    elif any(k in edu_str for k in ["associate", "diploma"]):
        base_score = 65.0
    elif any(k in edu_str for k in ["bootcamp", "certificate"]):
        base_score = 60.0
    else:
        base_score = 70.0

    # 2. Field-of-study relevance keywords
    unrelated_keywords = [
        "history", "fine arts", "fine art", "art", "arts", "literature",
        "philosophy", "music", "humanities", "biology", "sociology",
        "psychology", "theology"
    ]
    adjacent_keywords = [
        "mechanical", "civil", "chemical", "electrical", "electronics",
        "aerospace", "industrial", "physics", "chemistry", "mathematics",
        "math", "statistics", "biomedical"
    ]

    is_unrelated = any(re.search(r'\b' + re.escape(kw) + r'\b', edu_str) for kw in unrelated_keywords)
    is_adjacent = any(re.search(r'\b' + re.escape(kw) + r'\b', edu_str) for kw in adjacent_keywords)
    is_cs = any(cs in edu_str for cs in ["computer", "computing", "software", "information technology", "data science", "data analytics", "artificial intelligence", "cs", "it"])

    if is_unrelated and not is_cs:
        multiplier = 0.60
    elif is_adjacent and not is_cs:
        multiplier = 0.85
    else:
        multiplier = 1.0

    return round(base_score * multiplier, 1)

def evaluate_projects_score(candidate_data: Dict[str, Any]) -> float:
    """
    Evaluates project score strictly from project portfolio data.
    DO NOT derive project score from interview score.
    """
    # 1. Explicit projects_score if provided
    if "projects_score" in candidate_data and candidate_data["projects_score"] is not None:
        try:
            return max(0.0, min(100.0, float(candidate_data["projects_score"])))
        except (ValueError, TypeError):
            pass

    # 2. Evaluate from projects text / list if present
    proj = candidate_data.get("projects", candidate_data.get("project", ""))
    if isinstance(proj, list):
        count = len(proj)
        if count >= 3:
            return 95.0
        elif count == 2:
            return 85.0
        elif count == 1:
            return 75.0
        return 50.0
    elif isinstance(proj, str) and proj.strip():
        p_clean = proj.strip()
        if len(p_clean) > 30 or "," in p_clean or ";" in p_clean:
            return 85.0
        return 75.0

    # 3. Missing project data: neutral baseline (do not fabricate, do not penalize unfairly)
    return 60.0

def compute_overall_qualification_score(
    candidate_data: Dict[str, Any],
    job_requirements: Optional[Dict[str, Any]] = None,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculates multi-criteria qualification score (0-100) using job-related factors:
    - Required Skills (40%)
    - Preferred Skills (10%)
    - Relevant Experience (25%)
    - Education Relevance (15%)
    - Certifications (5%)
    - Projects Portfolio (5%)
    
    Technical interview score is stored separately and NOT substituted into project score.
    """
    job = job_requirements or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    w = weights or DEFAULT_SCORING_WEIGHTS

    cand_skills = parse_skills_list(candidate_data.get("skills", candidate_data.get("technical_skills", [])))
    req_skills = parse_skills_list(job.get("required_skills", []))
    pref_skills = parse_skills_list(job.get("preferred_skills", []))

    skill_analysis = match_skills(cand_skills, req_skills, pref_skills)
    try:
        cand_exp = float(candidate_data.get("experience_years", candidate_data.get("experience", 0)) or 0)
    except (ValueError, TypeError):
        cand_exp = 0.0

    try:
        min_exp = float(job.get("minimum_experience", 2.0) or 2.0)
    except (ValueError, TypeError):
        min_exp = 2.0

    exp_analysis = evaluate_experience_match(cand_exp, min_exp)

    cand_edu = str(candidate_data.get("education", candidate_data.get("degree", "")))
    req_edu = str(job.get("required_education", ""))
    edu_score = evaluate_education_relevance(cand_edu, req_edu)

    # Certification evaluation
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

    # Project score: purely from project data
    proj_score = evaluate_projects_score(candidate_data)

    # Technical interview score: kept completely separate if present
    technical_interview_score = None
    if "technical_interview_score" in candidate_data and candidate_data["technical_interview_score"] is not None:
        try:
            technical_interview_score = float(candidate_data["technical_interview_score"])
        except (ValueError, TypeError):
            pass
    elif "interview_score" in candidate_data and candidate_data["interview_score"] is not None:
        try:
            technical_interview_score = float(candidate_data["interview_score"])
        except (ValueError, TypeError):
            pass

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

    component_breakdown = {
        "required_skills_score": skill_analysis["required_match_percentage"],
        "preferred_skills_score": skill_analysis["preferred_match_percentage"],
        "experience_score": exp_analysis["experience_match_percentage"],
        "education_score": edu_score,
        "certifications_score": cert_score,
        "projects_score": proj_score,
        "project_performance_score": proj_score  # Backward compatibility alias
    }
    if technical_interview_score is not None:
        component_breakdown["technical_interview_score"] = technical_interview_score

    return {
        "qualification_score": overall_score,
        "expected_decision": expected_decision,
        "component_breakdown": component_breakdown,
        "weights_applied": w,
        "skill_analysis": skill_analysis,
        "experience_analysis": exp_analysis,
        "candidate_id": candidate_data.get("candidate_id", "UNKNOWN"),
        "candidate_name": candidate_data.get("name", "Candidate"),
        "job_title": job.get("title", "Software Engineer"),
        "technical_interview_score": technical_interview_score
    }
