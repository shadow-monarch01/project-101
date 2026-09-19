"""
AI Hiring Intelligence - Qualification Counterfactual Engine
Generates controlled, job-relevant qualification perturbations (Skills, Experience, Education, Certifications)
while holding all unrelated candidate attributes strictly invariant to audit AI causal responsiveness.
"""

import copy
from typing import Dict, List, Any, Optional
from modules.qualifications import parse_skills_list

QUALIFICATION_CONCEPTS = [
    {
        "id": "skills",
        "name": "Technical Skills",
        "description": "Add, remove, or substitute required technical skills",
        "type": "categorical_list",
        "options": ["Remove Core Skill", "Add Preferred Skill", "Minimal Skillset", "Mastery Skillset"]
    },
    {
        "id": "experience_years",
        "name": "Years of Experience",
        "description": "Adjust professional domain experience",
        "type": "numeric",
        "options": ["1.0", "2.0", "4.0", "6.0", "8.0", "12.0"]
    },
    {
        "id": "education",
        "name": "Education / Degree Level",
        "description": "Alter educational background or degree relevance",
        "type": "categorical",
        "options": ["M.S. Software Engineering", "B.Tech Computer Science", "B.S. Information Systems", "Associate Degree", "Bootcamp Certificate"]
    },
    {
        "id": "certifications_count",
        "name": "Professional Certifications",
        "description": "Change number and level of domain certifications",
        "type": "numeric",
        "options": ["0", "1", "2", "3", "4"]
    },
    {
        "id": "interview_score",
        "name": "Technical Interview Rating",
        "description": "Modify technical assessment benchmark score",
        "type": "numeric",
        "options": ["60", "70", "80", "88", "95"]
    }
]

def get_available_qualification_concepts() -> List[Dict[str, Any]]:
    return QUALIFICATION_CONCEPTS

def make_qualification_variation(
    candidate: Dict[str, Any],
    concept: str,
    target_value: Any,
    job_requirements: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    twin = copy.deepcopy(candidate)
    concept_lower = str(concept).strip().lower()

    if concept_lower in ["skills", "technical_skills", "skill"]:
        skills = parse_skills_list(candidate.get("skills", candidate.get("technical_skills", [])))
        t_val = str(target_value).strip()

        if t_val == "Remove Core Skill":
            if skills:
                skills = skills[1:]
        elif t_val == "Add Preferred Skill":
            pref_list = ["FastAPI", "Docker", "Kubernetes", "GraphQL", "AWS", "Machine Learning"]
            for p in pref_list:
                if p.lower() not in [s.lower() for s in skills]:
                    skills.append(p)
                    break
        elif t_val == "Minimal Skillset":
            skills = skills[:1] if skills else ["Git"]
        elif t_val == "Mastery Skillset":
            skills = list(set(skills + ["Python", "SQL", "Docker", "Kubernetes", "PostgreSQL", "FastAPI", "CI/CD"]))
        else:
            skills = parse_skills_list(t_val) if t_val else skills

        twin["skills"] = "; ".join(skills)
        twin["technical_skills"] = "; ".join(skills)

    elif concept_lower in ["experience_years", "experience", "years_exp"]:
        try:
            twin["experience_years"] = float(target_value)
        except (ValueError, TypeError):
            twin["experience_years"] = candidate.get("experience_years", 3.0)

    elif concept_lower in ["education", "degree", "education_level"]:
        twin["education"] = str(target_value)
        twin["degree"] = str(target_value)

    elif concept_lower in ["certifications", "certifications_count", "certs"]:
        try:
            val = int(target_value)
            twin["certifications_count"] = val
            twin["certifications"] = [f"Cert #{i+1}" for i in range(val)] if val > 0 else []
        except (ValueError, TypeError):
            twin["certifications_count"] = 0
            twin["certifications"] = []

    elif concept_lower in ["interview_score", "score", "coding_score"]:
        try:
            twin["interview_score"] = float(target_value)
        except (ValueError, TypeError):
            twin["interview_score"] = candidate.get("interview_score", 75.0)

    else:
        twin[concept] = target_value

    return twin

def generate_counterfactual_pair(
    candidate: Dict[str, Any],
    concept: str,
    target_value: Any,
    job_requirements: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    twin = make_qualification_variation(candidate, concept, target_value, job_requirements)
    invariance_report = {}
    ignored_keys = {"skills", "technical_skills", concept}
    for k, v in candidate.items():
        if k not in ignored_keys:
            invariance_report[k] = (twin.get(k) == v)

    return {
        "original_candidate": candidate,
        "counterfactual_candidate": twin,
        "perturbation_concept": concept,
        "target_value": target_value,
        "all_other_attributes_invariant": all(invariance_report.values()) if invariance_report else True,
        "invariance_details": invariance_report
    }
