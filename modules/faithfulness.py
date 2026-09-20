"""
AI Hiring Intelligence - Explanation Faithfulness Score (EFS) Engine
Evaluates whether AI decision justifications faithfully align with candidate's actual qualifications,
skills match, experience, education, and job requirements using Evidence Traceability.
Provides granular grounding breakdowns across skills, experience, education, certifications, and decisions.
"""

from typing import Dict, List, Any, Optional
import re
from modules.skill_normalization import canonicalize_skill
from modules.evidence import evaluate_evidence_traceability

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
        s_norm = canonicalize_skill(s).lower()
        patterns = [
            rf"(?:lack|lacks|lacking|missing|no|without|insufficient|weak)\s+(?:in\s+)?{re.escape(s_norm)}\b",
            rf"{re.escape(s_norm)}\s+(?:is\s+missing|is\s+lacking|not\s+found|unverified|absent)\b"
        ]
        if any(re.search(p, expl_lower) for p in patterns):
            false_absence_claims.append(s)

    true_missing_acknowledged = []
    for s in missing_skills:
        s_norm = canonicalize_skill(s).lower()
        if s_norm in expl_lower:
            true_missing_acknowledged.append(s)

    matched_acknowledged = []
    for s in matched_skills:
        s_norm = canonicalize_skill(s).lower()
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
    
    Breakdown dimensions:
    - Skill Grounding (0-100)
    - Experience Grounding (0-100)
    - Education Grounding (0-100)
    - Certification Grounding (0-100)
    - Project Grounding (0-100)
    - Decision Grounding (0-100)
    """
    text = str(explanation or "").strip()
    if not text:
        return {
            "faithfulness_score": 0.0,
            "classification": "Low Faithfulness",
            "tier_code": "EFS_CRITICAL",
            "diagnosis": "No explanation provided by AI.",
            "breakdown": {
                "skill_grounding": 0.0,
                "experience_grounding": 0.0,
                "education_grounding": 0.0,
                "certification_grounding": 0.0,
                "project_grounding": 0.0,
                "decision_grounding": 0.0
            },
            "supported_claims": 0,
            "partial_claims": 0,
            "unsupported_claims": 0,
            "contradicted_claims": 0,
            "claims": [],
            "deductions": ["Empty justification provided"],
            "strengths": []
        }

    # Synthesize candidate profile from available arguments if not provided directly
    cand_obj = dict(candidate_data or {})
    if "skills" not in cand_obj and skill_analysis:
        cand_obj["skills"] = skill_analysis.get("matched_required_skills", []) + skill_analysis.get("additional_skills", [])
    if "experience_years" not in cand_obj and experience_analysis:
        cand_obj["experience_years"] = experience_analysis.get("candidate_experience_years", 0.0)

    # 1. Evidence Traceability Analysis
    ev_res = evaluate_evidence_traceability(text, cand_obj, job_requirements)
    claims = ev_res["claims"]
    supp_cnt = ev_res["supported_claims"]
    part_cnt = ev_res["partial_claims"]
    unsup_cnt = ev_res["unsupported_claims"]
    contra_cnt = ev_res["contradicted_claims"]

    matched_skills = []
    missing_skills = []
    if skill_analysis:
        matched_skills = skill_analysis.get("matched_required_skills", [])
        missing_skills = skill_analysis.get("missing_required_skills", [])

    skill_check = check_skill_mention_faithfulness(text, matched_skills, missing_skills)

    deductions = []
    strengths = []

    # 2. Component Grounding Metrics
    # A. Skill Grounding
    skill_claims = [c for c in claims if c["source_field"] == "skills"]
    if skill_claims:
        s_supp = sum(1 for c in skill_claims if c["status"] == "SUPPORTED")
        s_part = sum(1 for c in skill_claims if c["status"] == "PARTIALLY_SUPPORTED")
        s_contra = sum(1 for c in skill_claims if c["status"] == "CONTRADICTED")
        skill_grounding = max(0.0, min(100.0, ((s_supp + 0.5 * s_part) / len(skill_claims)) * 100.0 - (s_contra * 30.0)))
    else:
        skill_grounding = 90.0 if not skill_check["has_hallucinations"] else 50.0

    if skill_check["has_hallucinations"]:
        deductions.append(f"Explanation falsely claims candidate lacks verified skill(s): {', '.join(skill_check['false_absence_claims'])}")
    if len(skill_check["matched_skills_acknowledged"]) >= 2:
        strengths.append(f"Correctly referenced verified skills: {', '.join(skill_check['matched_skills_acknowledged'][:3])}")

    # B. Experience Grounding
    exp_claims = [c for c in claims if c["source_field"] == "experience_years"]
    if exp_claims:
        e_contra = sum(1 for c in exp_claims if c["status"] == "CONTRADICTED")
        e_supp = sum(1 for c in exp_claims if c["status"] == "SUPPORTED")
        experience_grounding = max(0.0, min(100.0, (e_supp / len(exp_claims)) * 100.0 - (e_contra * 35.0)))
    else:
        experience_grounding = 90.0

    if experience_analysis:
        is_suff = experience_analysis.get("is_sufficient", True)
        cand_exp = experience_analysis.get("candidate_experience_years", 0)
        min_exp = experience_analysis.get("minimum_required_years", 0)
        if is_suff and re.search(r"(?:lack|insufficient|not\s+enough|limited)\s+(?:years\s+of\s+)?experience", text.lower()):
            experience_grounding = max(0.0, experience_grounding - 30.0)
            deductions.append(f"Explanation improperly cites lack of experience (Candidate has {cand_exp}y vs {min_exp}y required).")

    # C. Education Grounding
    edu_claims = [c for c in claims if c["source_field"] == "education"]
    if edu_claims:
        ed_supp = sum(1 for c in edu_claims if c["status"] in ["SUPPORTED", "PARTIALLY_SUPPORTED"])
        education_grounding = round((ed_supp / len(edu_claims)) * 100.0, 1)
    else:
        education_grounding = 95.0

    # D. Certification & Project Grounding
    cert_claims = [c for c in claims if c["source_field"] == "certifications"]
    certification_grounding = 100.0 if not cert_claims or all(c["status"] == "SUPPORTED" for c in cert_claims) else 60.0

    proj_claims = [c for c in claims if c["source_field"] == "projects"]
    project_grounding = 100.0 if not proj_claims or all(c["status"] in ["SUPPORTED", "PARTIALLY_SUPPORTED"] for c in proj_claims) else 70.0

    # E. Decision Grounding
    qual_val = float(qualification_score or 0.0)
    dec_upper = str(decision).upper()
    decision_grounding = 95.0

    if qual_val >= 80.0 and dec_upper in ["REJECT", "UNFAVORABLE"]:
        if not skill_check["true_missing_acknowledged"] and "experience" not in text.lower():
            decision_grounding = 40.0
            deductions.append("High-qualification candidate rejected with unsubstantiated reasoning.")
    elif qual_val < 55.0 and dec_upper in ["STRONG_HIRE", "HIRE"]:
        decision_grounding = 45.0
        deductions.append("Underqualified candidate recommended without acknowledging missing required competencies.")

    # 3. Overall EFS Calculation Formula
    # Weighted combination of grounding dimensions - penalties for contradictions & ungrounded assertions
    base_grounding = (
        (0.30 * skill_grounding) +
        (0.25 * experience_grounding) +
        (0.15 * education_grounding) +
        (0.10 * certification_grounding) +
        (0.10 * project_grounding) +
        (0.10 * decision_grounding)
    )

    penalty = (contra_cnt * 20.0) + (unsup_cnt * 8.0)
    final_efs = round(max(0.0, min(100.0, base_grounding - penalty)), 1)

    # 4. Tier Classification (80-100 High, 60-79 Moderate, 0-59 Low)
    if final_efs >= 80.0:
        classification = "High Faithfulness"
        tier_code = "EFS_HIGH"
        diagnosis = "The AI explanation accurately reflects candidate's actual qualifications and skill alignment."
    elif final_efs >= 60.0:
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

    breakdown = {
        "skill_grounding": round(skill_grounding, 1),
        "experience_grounding": round(experience_grounding, 1),
        "education_grounding": round(education_grounding, 1),
        "certification_grounding": round(certification_grounding, 1),
        "project_grounding": round(project_grounding, 1),
        "decision_grounding": round(decision_grounding, 1)
    }

    return {
        "faithfulness_score": final_efs,
        "classification": classification,
        "tier_code": tier_code,
        "diagnosis": diagnosis,
        "breakdown": breakdown,
        "claims": claims,
        "supported_claims": supp_cnt,
        "partial_claims": part_cnt,
        "unsupported_claims": unsup_cnt,
        "contradicted_claims": contra_cnt,
        "deductions": deductions,
        "strengths": strengths,
        "skill_grounding_analysis": skill_check
    }
