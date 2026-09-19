"""
AI Hiring Intelligence - Explanation Faithfulness Score (EFS) Engine
Evaluates whether AI decision justifications faithfully align with candidate's actual qualifications,
skills match, experience, and job requirements.
"""

from typing import Dict, List, Any, Optional
import re
from modules.qualifications import normalize_skill_string

def check_skill_mention_faithfulness(
    explanation: str,
    matched_skills: List[str],
    missing_skills: List[str]
) -> Dict[str, Any]:
    """
    Checks whether the explanation accurately cites matched and missing skills.
    Detects hallucinations (claiming a candidate lacks a skill they actually possess).
    """
    expl_lower = explanation.lower()
    
    false_absence_claims = []
    for s in matched_skills:
        s_norm = normalize_skill_string(s)
        patterns = [
            rf"(?:lack|lacks|missing|no|without|insufficient|weak)\s+(?:in\s+)?{re.escape(s_norm)}\b",
            rf"{re.escape(s_norm)}\s+(?:is\s+missing|is\s+lacking|not\s+found|unverified)\b"
        ]
        if any(re.search(p, expl_lower) for p in patterns):
            false_absence_claims.append(s)

    true_missing_acknowledged = []
    for s in missing_skills:
        s_norm = normalize_skill_string(s)
        if s_norm in expl_lower:
            true_missing_acknowledged.append(s)

    matched_acknowledged = []
    for s in matched_skills:
        s_norm = normalize_skill_string(s)
        if s_norm in expl_lower:
            matched_acknowledged.append(s)

    return {
        "false_absence_claims": false_absence_claims,
        "true_missing_acknowledged": true_missing_acknowledged,
        "matched_skills_acknowledged": matched_acknowledged,
        "has_hallucinations": len(false_absence_claims) > 0
    }

def evaluate_faithfulness_instance(
    explanation: str,
    qualification_score: float,
    decision: str,
    skill_analysis: Optional[Dict[str, Any]] = None,
    experience_analysis: Optional[Dict[str, Any]] = None,
    candidate_data: Optional[Dict[str, Any]] = None,
    job_requirements: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes the Explanation Faithfulness Score (EFS, 0-100)
    evaluating alignment between AI text justification and objective candidate merits.
    """
    text = str(explanation or "").strip()
    if not text:
        return {
            "faithfulness_score": 0.0,
            "classification": "Unfaithful / Empty",
            "tier_code": "EFS_CRITICAL",
            "diagnosis": "No explanation provided by AI.",
            "faithfulness_details": {"deductions": ["Empty justification"]}
        }

    matched_skills = []
    missing_skills = []
    if skill_analysis:
        matched_skills = skill_analysis.get("matched_required_skills", [])
        missing_skills = skill_analysis.get("missing_required_skills", [])

    skill_check = check_skill_mention_faithfulness(text, matched_skills, missing_skills)

    score = 100.0
    deductions = []
    strengths = []

    if skill_check["has_hallucinations"]:
        penalty = min(45.0, len(skill_check["false_absence_claims"]) * 25.0)
        score -= penalty
        deductions.append(f"Explanation falsely claims candidate lacks verified skill(s): {', '.join(skill_check['false_absence_claims'])}")

    qual_val = float(qualification_score or 0.0)
    dec_upper = str(decision).upper()

    if qual_val >= 80.0 and dec_upper in ["REJECT", "UNFAVORABLE"]:
        if not skill_check["true_missing_acknowledged"] and "experience" not in text.lower():
            score -= 30.0
            deductions.append("High-qualification profile rejected with generic/unsubstantiated reasoning.")
    elif qual_val < 55.0 and dec_upper in ["STRONG_HIRE", "HIRE"]:
        score -= 25.0
        deductions.append("Underqualified candidate recommended without acknowledging missing required competencies.")

    if experience_analysis:
        is_suff = experience_analysis.get("is_sufficient", True)
        cand_exp = experience_analysis.get("candidate_experience_years", 0)
        min_exp = experience_analysis.get("minimum_required_years", 0)
        
        if is_suff and re.search(r"(?:lack|insufficient|not\s+enough|limited)\s+(?:years\s+of\s+)?experience", text.lower()):
            score -= 25.0
            deductions.append(f"Explanation improperly cites lack of experience (Candidate has {cand_exp}y vs {min_exp}y required).")

    if len(skill_check["matched_skills_acknowledged"]) >= 2:
        strengths.append(f"Correctly referenced candidate's verified skills: {', '.join(skill_check['matched_skills_acknowledged'][:3])}")

    final_efs = round(max(0.0, min(100.0, score)), 1)

    if final_efs >= 85.0:
        classification = "High Faithfulness"
        tier_code = "EFS_HIGH"
        diagnosis = "The AI explanation accurately reflects candidate's actual qualifications and skill alignment."
    elif final_efs >= 65.0:
        classification = "Moderate Faithfulness"
        tier_code = "EFS_MODERATE"
        diagnosis = "Explanation generally aligns with qualifications with minor grounding ambiguities."
    elif final_efs >= 40.0:
        classification = "Low Faithfulness"
        tier_code = "EFS_LOW"
        diagnosis = "Noticeable discrepancy between candidate qualifications and stated justification."
    else:
        classification = "Unfaithful / Deceptive"
        tier_code = "EFS_UNFAITHFUL"
        diagnosis = "High unfaithfulness: Explanation cites false deficits or fails to substantiate recommendation."

    return {
        "faithfulness_score": final_efs,
        "classification": classification,
        "tier_code": tier_code,
        "diagnosis": diagnosis,
        "deductions": deductions,
        "strengths": strengths,
        "skill_grounding_analysis": skill_check
    }
