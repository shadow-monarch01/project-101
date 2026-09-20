"""
AI Hiring Intelligence - Skill Analysis & Gap Engine
Performs canonical skill matching, required vs preferred skill overlap metrics,
and detailed missing/additional skill gap analysis.
"""

from typing import Dict, List, Any, Optional
import re
from modules.skill_normalization import (
    canonicalize_skill,
    normalize_skill,
    normalize_skills_list,
    get_canonical_skills
)

def normalize_skill_string(skill: str) -> str:
    """Canonicalizes and standardizes a single skill string."""
    return canonicalize_skill(skill)

def parse_skills_list(skills_input: Any) -> List[str]:
    """Parses a list, comma-separated, or semicolon-separated string of skills into canonical names."""
    if isinstance(skills_input, list):
        raw_list = []
        for s in skills_input:
            if isinstance(s, str):
                parts = re.split(r'[,;|\n]+', s)
                raw_list.extend([p.strip() for p in parts if p.strip()])
            elif s:
                raw_list.append(str(s).strip())
    elif isinstance(skills_input, str):
        parts = re.split(r'[,;|\n]+', skills_input)
        raw_list = [p.strip() for p in parts if p.strip()]
    else:
        raw_list = []
    
    return get_canonical_skills(raw_list)

def match_skills(
    candidate_skills: Any,
    required_skills: Any,
    preferred_skills: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Compares candidate skills against job required and preferred skills.
    Normalizes both sides to canonical skill names before comparison.
    Guarantees that:
    1. Matched required and missing required are strictly disjoint.
    2. Additional skills only contain candidate skills that are neither required nor preferred.
    3. No skill appears in multiple categories.
    """
    cand_canonical = parse_skills_list(candidate_skills)
    req_canonical = parse_skills_list(required_skills)
    pref_canonical = parse_skills_list(preferred_skills or [])

    cand_set = set(cand_canonical)
    req_set = set(req_canonical)
    pref_set = set(pref_canonical) - req_set

    matched_required = sorted(list(cand_set.intersection(req_set)))
    missing_required = sorted(list(req_set - cand_set))

    matched_preferred = sorted(list(cand_set.intersection(pref_set)))
    missing_preferred = sorted(list(pref_set - cand_set))

    all_job_skills = req_set.union(pref_set)
    additional_skills = sorted(list(cand_set - all_job_skills))

    total_req = max(1, len(req_canonical))
    req_match_ratio = len(matched_required) / float(total_req)
    req_match_pct = round(req_match_ratio * 100.0, 1)

    total_pref = len(pref_canonical)
    if total_pref > 0:
        pref_match_ratio = len(matched_preferred) / float(total_pref)
        pref_match_pct = round(pref_match_ratio * 100.0, 1)
    else:
        pref_match_pct = 100.0

    skill_gap_ratio = len(missing_required) / float(total_req)
    skill_gap_pct = round(skill_gap_ratio * 100.0, 1)

    # Detailed normalized objects for viva/UI display
    matched_required_details = [
        {"candidate_skill": s, "canonical_skill": s, "required_skill": s}
        for s in matched_required
    ]

    return {
        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "additional_skills": additional_skills,
        "matched_required_details": matched_required_details,
        "required_skills_count": len(req_canonical),
        "matched_required_count": len(matched_required),
        "missing_required_count": len(missing_required),
        "required_match_percentage": req_match_pct,
        "preferred_match_percentage": pref_match_pct,
        "skill_gap_percentage": skill_gap_pct
    }
