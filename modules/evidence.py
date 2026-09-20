"""
AI Hiring Intelligence - Evidence Traceability & Grounding Engine
Extracts verifiable claims from AI-generated hiring justifications and matches them
against objective candidate records and job requirements.
Determines whether each statement is SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, or CONTRADICTED.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
from modules.skill_normalization import canonicalize_skill, KNOWN_ALIASES

def extract_numerical_years(text: str) -> Optional[float]:
    """Extracts mentioned years of experience from text if present."""
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+experience)?',
        r'(?:over|more than|approximately|around)\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs?)'
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except (ValueError, TypeError):
                pass
    # Word numbers
    word_to_num = {
        "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0,
        "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0, "ten": 10.0
    }
    for word, val in word_to_num.items():
        if re.search(rf'\b{word}\s+(?:years?|yrs?)\b', text, re.IGNORECASE):
            return val
    return None

def extract_claims_from_explanation(
    explanation: str,
    candidate_data: Dict[str, Any],
    job_requirements: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Extracts atomic, verifiable claims from the AI explanation and assesses their evidence status.
    """
    text = str(explanation or "").strip()
    if not text:
        return []

    claims: List[Dict[str, Any]] = []
    text_lower = text.lower()

    # 1. Candidate Verified Evidence Setup
    raw_cand_skills = candidate_data.get("skills", candidate_data.get("technical_skills", []))
    if isinstance(raw_cand_skills, str):
        raw_cand_skills = [s.strip() for s in re.split(r'[,;|\n]+', raw_cand_skills) if s.strip()]
    cand_canonical_skills = {canonicalize_skill(s) for s in (raw_cand_skills or []) if s}
    try:
        cand_exp = float(candidate_data.get("experience_years", candidate_data.get("experience", 0)) or 0.0)
    except (ValueError, TypeError):
        cand_exp = 0.0
    cand_edu = str(candidate_data.get("education", candidate_data.get("degree", ""))).strip()
    cand_certs = str(candidate_data.get("certifications", "")).strip()
    cand_proj = str(candidate_data.get("projects", "")).strip()

    job = job_requirements or {}
    req_skills = [canonicalize_skill(s) for s in job.get("required_skills", []) if s]
    pref_skills = [canonicalize_skill(s) for s in job.get("preferred_skills", []) if s]
    try:
        min_exp = float(job.get("minimum_experience", 0.0) or 0.0)
    except (ValueError, TypeError):
        min_exp = 0.0

    # All candidate and job skills to check
    known_skill_names = set(cand_canonical_skills)
    known_skill_names.update(req_skills)
    known_skill_names.update(pref_skills)
    for k, v in KNOWN_ALIASES.items():
        if len(k) >= 3 and k in text_lower:
            known_skill_names.add(v)

    # 2. Skill-Related Claims (Positive Assertions and Deficit/Absence Assertions)
    for skill in sorted(known_skill_names, key=len, reverse=True):
        skill_pat = re.escape(skill.lower())
        
        # Check if mentioned in text
        if not re.search(rf'\b{skill_pat}\b', text_lower):
            continue

        # Deficit / Lacking assertion check
        deficit_patterns = [
            rf'(?:lack|lacks|lacking|missing|no|without|insufficient|weak)\s+(?:in\s+)?{skill_pat}\b',
            rf'{skill_pat}\s+(?:is\s+missing|is\s+lacking|not\s+found|unverified|absent)\b'
        ]
        is_deficit_claim = any(re.search(p, text_lower) for p in deficit_patterns)

        if is_deficit_claim:
            claim_text = f"Candidate lacks or is missing {skill}"
            if skill in cand_canonical_skills:
                # Contradiction: Candidate actually HAS this skill
                status = "CONTRADICTED"
                evidence = f"Candidate verified skills list contains '{skill}'"
                confidence = 1.0
            else:
                # Supported: Candidate does NOT have this skill
                status = "SUPPORTED"
                evidence = f"Verified: '{skill}' is absent from candidate profile"
                confidence = 0.95
        else:
            # Positive assertion
            claim_text = f"Candidate possesses {skill} competency"
            if skill in cand_canonical_skills:
                status = "SUPPORTED"
                evidence = [skill]
                confidence = 0.95
            elif skill in req_skills or skill in pref_skills:
                status = "UNSUPPORTED"
                evidence = f"'{skill}' is required by job but not present in candidate skills"
                confidence = 0.90
            else:
                status = "UNSUPPORTED"
                evidence = f"No record of '{skill}' in candidate profile"
                confidence = 0.85

        claims.append({
            "claim": claim_text,
            "source_field": "skills",
            "evidence": evidence,
            "status": status,
            "confidence": confidence
        })

    # 3. Experience-Related Claims
    exp_mentioned_years = extract_numerical_years(text)
    if exp_mentioned_years is not None:
        claim_text = f"Candidate has {exp_mentioned_years} years of experience"
        diff = abs(exp_mentioned_years - cand_exp)
        if diff <= 0.5:
            status = "SUPPORTED"
            evidence = cand_exp
            confidence = 1.0
        elif diff <= 1.5:
            status = "PARTIALLY_SUPPORTED"
            evidence = cand_exp
            confidence = 0.85
        else:
            status = "CONTRADICTED"
            evidence = cand_exp
            confidence = 1.0

        claims.append({
            "claim": claim_text,
            "source_field": "experience_years",
            "evidence": evidence,
            "status": status,
            "confidence": confidence
        })

    # Qualitative experience deficit assertion
    if re.search(r'\b(?:insufficient|lack|limited|weak|no)\s+(?:years\s+of\s+)?experience\b', text_lower):
        claim_text = "Candidate lacks sufficient years of experience"
        if cand_exp >= min_exp and min_exp > 0:
            status = "CONTRADICTED"
            evidence = f"Candidate has {cand_exp}y which meets/exceeds required {min_exp}y"
            confidence = 0.95
        elif cand_exp < min_exp and min_exp > 0:
            status = "SUPPORTED"
            evidence = f"Candidate has {cand_exp}y vs {min_exp}y required"
            confidence = 0.95
        else:
            status = "SUPPORTED" if cand_exp < 2.0 else "PARTIALLY_SUPPORTED"
            evidence = f"Candidate experience: {cand_exp}y"
            confidence = 0.80

        claims.append({
            "claim": claim_text,
            "source_field": "experience_years",
            "evidence": evidence,
            "status": status,
            "confidence": confidence
        })

    # 4. Education-Related Claims
    edu_terms = ["b.tech", "b.s.", "bachelor", "m.s.", "master", "m.tech", "ph.d", "doctorate", "degree", "computer science"]
    for edu_k in edu_terms:
        if edu_k in text_lower:
            claim_text = f"Education qualification references '{edu_k.upper()}'"
            if edu_k in cand_edu.lower():
                status = "SUPPORTED"
                evidence = cand_edu
                confidence = 0.95
            elif cand_edu:
                status = "PARTIALLY_SUPPORTED"
                evidence = cand_edu
                confidence = 0.75
            else:
                status = "UNSUPPORTED"
                evidence = "No education details in candidate profile"
                confidence = 0.80

            claims.append({
                "claim": claim_text,
                "source_field": "education",
                "evidence": evidence,
                "status": status,
                "confidence": confidence
            })
            break

    # 5. Certification Claims
    if re.search(r'\b(?:certified|certification|aws\s+certified|certificate)\b', text_lower):
        claim_text = "Candidate holds relevant technical certifications"
        if cand_certs and cand_certs.strip() != "0":
            status = "SUPPORTED"
            evidence = cand_certs
            confidence = 0.95
        else:
            status = "UNSUPPORTED"
            evidence = "Candidate profile lists no verified certifications"
            confidence = 0.90

        claims.append({
            "claim": claim_text,
            "source_field": "certifications",
            "evidence": evidence,
            "status": status,
            "confidence": confidence
        })

    # 6. Project & Technical Domain Claims
    if re.search(r'\b(?:project|projects|portfolio|distributed|microservices|pipeline)\b', text_lower):
        claim_text = "Candidate has relevant hands-on project experience"
        if cand_proj:
            status = "SUPPORTED"
            evidence = cand_proj
            confidence = 0.90
        else:
            status = "PARTIALLY_SUPPORTED"
            evidence = "General technical profile assessment"
            confidence = 0.70

        claims.append({
            "claim": claim_text,
            "source_field": "projects",
            "evidence": evidence,
            "status": status,
            "confidence": confidence
        })

    # Fallback if no specific atomic claim patterns matched
    if not claims:
        claims.append({
            "claim": "General qualification assessment statement",
            "source_field": "summary",
            "evidence": "Candidate record overview",
            "status": "SUPPORTED",
            "confidence": 0.75
        })

    return claims

def evaluate_evidence_traceability(
    explanation: str,
    candidate_data: Dict[str, Any],
    job_requirements: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates evidence traceability for an AI explanation against candidate profile.
    Computes groundedness statistics and evidence grounding score (0-100).
    """
    text = str(explanation or "").strip()
    if not text:
        return {
            "claims": [],
            "supported_claims": 0,
            "partial_claims": 0,
            "unsupported_claims": 0,
            "contradicted_claims": 0,
            "total_claims": 0,
            "evidence_grounding_score": 0.0,
            "status_summary": "Empty explanation provided."
        }

    claims = extract_claims_from_explanation(text, candidate_data, job_requirements)
    
    supported_cnt = sum(1 for c in claims if c["status"] == "SUPPORTED")
    partial_cnt = sum(1 for c in claims if c["status"] == "PARTIALLY_SUPPORTED")
    unsupported_cnt = sum(1 for c in claims if c["status"] == "UNSUPPORTED")
    contradicted_cnt = sum(1 for c in claims if c["status"] == "CONTRADICTED")
    total_cnt = len(claims)

    if total_cnt == 0:
        score = 0.0
    else:
        # Base positive grounding ratio
        pos_ratio = (supported_cnt + (0.5 * partial_cnt)) / float(total_cnt)
        raw_score = pos_ratio * 100.0
        # Penalties for unsupported and severe penalty for contradicted claims
        raw_score -= (contradicted_cnt * 25.0)
        raw_score -= (unsupported_cnt * 10.0)
        score = round(max(0.0, min(100.0, raw_score)), 1)

    return {
        "candidate_id": candidate_data.get("candidate_id", "UNKNOWN"),
        "candidate_name": candidate_data.get("name", "Candidate"),
        "job_title": (job_requirements or {}).get("title", "Position"),
        "claims": claims,
        "supported_claims": supported_cnt,
        "partial_claims": partial_cnt,
        "unsupported_claims": unsupported_cnt,
        "contradicted_claims": contradicted_cnt,
        "total_claims": total_cnt,
        "evidence_grounding_score": score,
        "has_contradictions": contradicted_cnt > 0
    }
