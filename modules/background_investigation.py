"""
AI Hiring Intelligence System - Evidence-Based Candidate Background Investigation (BI) Engine
Evaluates whether candidate claims across Education, Experience, Certifications, Skills, Projects,
and Employment History are supported, internally consistent, or contradictory based on provided profile facts.

IMPORTANT:
This module performs EVIDENCE-BASED BACKGROUND INVESTIGATION from data supplied to the application.
It evaluates internal consistency and evidence grounding without claiming external official verification.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import re
from modules.skill_normalization import (
    canonicalize_skill,
    get_canonical_skills
)
from modules.skill_analysis import parse_skills_list

BI_DISCLAIMER: str = (
    "Evidence-Based Background Investigation evaluates whether candidate claims are supported, "
    "internally consistent, or contradictory based on provided profile facts. "
    "This is an internal evidence grounding analysis and does not constitute an external official background check."
)

INVESTIGATION_STATUSES = [
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "MISSING_EVIDENCE",
    "CONTRADICTED",
    "NOT_AVAILABLE"
]

OVERALL_STATUSES = [
    "VERIFIED_FROM_PROVIDED_EVIDENCE",
    "PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE",
    "INSUFFICIENT_EVIDENCE",
    "INCONSISTENCY_DETECTED"
]


def investigate_education(
    candidate: Dict[str, Any],
    job: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Investigates candidate education credentials against provided profile data.
    Checks degree presence, institution (if provided), major/discipline, and consistency.
    """
    edu_str = str(candidate.get("education", candidate.get("degree", ""))).strip()
    institution = str(candidate.get("institution", candidate.get("university", candidate.get("college", "")))).strip()

    if not edu_str:
        return {
            "status": "MISSING_EVIDENCE",
            "degree": "",
            "institution": institution,
            "evidence": "No education credential or degree record provided in candidate profile.",
            "is_supported": False,
            "inconsistency": None
        }

    edu_lower = edu_str.lower()

    # Detect degree level
    if any(k in edu_lower for k in ["ph.d", "phd", "doctorate"]):
        degree_level = "Doctorate / Ph.D."
    elif any(k in edu_lower for k in ["m.s.", "ms in", "m.tech", "master", "mca", "m.sc", "msc"]):
        degree_level = "Master's Degree"
    elif any(k in edu_lower for k in ["b.tech", "b.e.", "b.s.", "bs in", "bachelor", "bca", "b.sc", "bsc"]):
        degree_level = "Bachelor's Degree"
    elif any(k in edu_lower for k in ["associate", "diploma"]):
        degree_level = "Associate / Diploma"
    elif any(k in edu_lower for k in ["bootcamp", "certificate"]):
        degree_level = "Technical Bootcamp / Certificate"
    else:
        degree_level = "Degree / Credential"

    evidence_text = f"Degree documented: {edu_str}"
    if institution:
        evidence_text += f" ({institution})"

    return {
        "status": "SUPPORTED",
        "degree": edu_str,
        "degree_level": degree_level,
        "institution": institution if institution else "Not explicitly specified",
        "evidence": evidence_text,
        "is_supported": True,
        "inconsistency": None
    }


def investigate_experience(
    candidate: Dict[str, Any],
    job: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Investigates candidate work experience claims and validates against itemized employment history.
    Detects duration discrepancies or contradictory tenure claims.
    """
    raw_exp = candidate.get("experience_years", candidate.get("experience", None))
    try:
        exp_years = float(raw_exp if raw_exp is not None else 0.0)
    except (ValueError, TypeError):
        exp_years = 0.0

    emp_history = candidate.get("employment_history", candidate.get("work_history", []))

    # Check itemized history duration if available
    itemized_years = 0.0
    has_itemized = False

    if isinstance(emp_history, list) and len(emp_history) > 0:
        has_itemized = True
        for rec in emp_history:
            if isinstance(rec, dict):
                try:
                    dur = float(rec.get("duration_years", rec.get("years", 0.0)))
                    itemized_years += dur
                except (ValueError, TypeError):
                    pass

    # Check for contradictions between claimed years and itemized records
    if has_itemized and itemized_years > 0:
        diff = abs(exp_years - itemized_years)
        if exp_years > 0 and itemized_years < (exp_years * 0.5) and diff >= 2.0:
            return {
                "status": "CONTRADICTED",
                "claimed_years": exp_years,
                "itemized_years": round(itemized_years, 1),
                "evidence": f"Claimed {exp_years} years experience, but itemized employment records sum to only {round(itemized_years, 1)} years.",
                "is_supported": False,
                "inconsistency": f"Duration mismatch: Claimed {exp_years}y vs documented {round(itemized_years, 1)}y."
            }

    if exp_years > 0:
        req_min = float(job.get("minimum_experience", 0.0)) if job else 0.0
        evidence_text = f"Claimed {exp_years} years relevant professional experience."
        if req_min > 0:
            evidence_text += f" (Job requirement: {req_min} years)."

        return {
            "status": "SUPPORTED",
            "claimed_years": exp_years,
            "itemized_years": round(itemized_years, 1) if has_itemized else None,
            "evidence": evidence_text,
            "is_supported": True,
            "inconsistency": None
        }

    if raw_exp is None or exp_years == 0.0:
        return {
            "status": "MISSING_EVIDENCE",
            "claimed_years": 0.0,
            "itemized_years": None,
            "evidence": "No professional experience record provided in candidate profile.",
            "is_supported": False,
            "inconsistency": None
        }

    return {
        "status": "PARTIALLY_SUPPORTED",
        "claimed_years": exp_years,
        "itemized_years": None,
        "evidence": f"Experience indicated as {exp_years} years with limited employment details.",
        "is_supported": True,
        "inconsistency": None
    }


def investigate_certifications(
    candidate: Dict[str, Any],
    job: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Investigates professional certification claims from candidate profile data.
    """
    certs_raw = candidate.get("certifications", candidate.get("certifications_count", None))
    cert_list = []

    if isinstance(certs_raw, list):
        cert_list = [str(c).strip() for c in certs_raw if str(c).strip()]
    elif isinstance(certs_raw, str) and certs_raw.strip():
        cert_str = certs_raw.strip()
        if cert_str.lower() not in ["none", "nil", "n/a", "na", "0", "zero"]:
            cert_list = [c.strip() for c in re.split(r'[,;|\n]+', cert_str) if c.strip()]
    elif isinstance(certs_raw, (int, float)) and certs_raw > 0:
        cert_list = [f"{int(certs_raw)} Certified Credential(s)"]

    if cert_list:
        return {
            "status": "SUPPORTED",
            "certifications": cert_list,
            "count": len(cert_list),
            "evidence": f"Candidate documents {len(cert_list)} certification(s): {', '.join(cert_list)}.",
            "is_supported": True,
            "inconsistency": None
        }

    req_certs = job.get("required_certifications", []) if job else []
    if req_certs:
        return {
            "status": "MISSING_EVIDENCE",
            "certifications": [],
            "count": 0,
            "evidence": f"Job specifies required certifications ({', '.join(req_certs)}), but candidate provided no certification evidence.",
            "is_supported": False,
            "inconsistency": None
        }

    return {
        "status": "NOT_AVAILABLE",
        "certifications": [],
        "count": 0,
        "evidence": "No professional certifications declared in profile.",
        "is_supported": True,
        "inconsistency": None
    }


def investigate_skills(
    candidate: Dict[str, Any],
    job: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Investigates declared technical skills using canonical skill normalization.
    Cross-checks listed skills against project details and experience text.
    """
    raw_skills = candidate.get("skills", candidate.get("technical_skills", []))
    cand_skills_list = parse_skills_list(raw_skills)
    canonical_skills = get_canonical_skills(cand_skills_list)

    if not canonical_skills:
        return {
            "status": "MISSING_EVIDENCE",
            "canonical_skills": [],
            "total_skills": 0,
            "corroborated_skills": [],
            "evidence": "No technical skills listed in candidate submission.",
            "is_supported": False,
            "inconsistency": None
        }

    # Cross-reference with project and experience text
    proj_text = str(candidate.get("projects", candidate.get("project", ""))).lower()
    exp_text = str(candidate.get("role", "")).lower() + " " + str(candidate.get("employment_history", "")).lower()
    combined_context = proj_text + " " + exp_text

    corroborated = [s for s in canonical_skills if s.lower() in combined_context]

    evidence_msg = f"Profile provides {len(canonical_skills)} normalized skills: {', '.join(canonical_skills[:6])}"
    if len(canonical_skills) > 6:
        evidence_msg += f" (+{len(canonical_skills)-6} more)"

    if corroborated:
        evidence_msg += f". Skills corroborated by project/experience records: {', '.join(corroborated[:4])}."

    return {
        "status": "SUPPORTED",
        "canonical_skills": canonical_skills,
        "total_skills": len(canonical_skills),
        "corroborated_skills": corroborated,
        "evidence": evidence_msg,
        "is_supported": True,
        "inconsistency": None
    }


def investigate_projects(
    candidate: Dict[str, Any],
    job: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Investigates portfolio project claims and technical stack alignment.
    """
    proj_data = candidate.get("projects", candidate.get("project", candidate.get("projects_score", None)))

    if isinstance(proj_data, list) and len(proj_data) > 0:
        proj_names = [str(p).strip() for p in proj_data if str(p).strip()]
        return {
            "status": "SUPPORTED",
            "projects_count": len(proj_names),
            "evidence": f"Candidate documents {len(proj_names)} project portfolio entry/entries: {', '.join(proj_names)}.",
            "is_supported": True,
            "inconsistency": None
        }

    if isinstance(proj_data, str) and proj_data.strip():
        p_clean = proj_data.strip()
        return {
            "status": "SUPPORTED",
            "projects_count": 1,
            "evidence": f"Project portfolio documented: {p_clean}.",
            "is_supported": True,
            "inconsistency": None
        }

    return {
        "status": "NOT_AVAILABLE",
        "projects_count": 0,
        "evidence": "No separate portfolio projects documented in profile.",
        "is_supported": True,
        "inconsistency": None
    }


def investigate_employment_history(
    candidate: Dict[str, Any],
    job: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Investigates detailed employment history records, roles, companies, and timelines.
    """
    history = candidate.get("employment_history", candidate.get("work_history", None))

    if isinstance(history, list) and len(history) > 0:
        records = []
        for h in history:
            if isinstance(h, dict):
                role = h.get("role", h.get("title", "Software Engineer"))
                company = h.get("company", h.get("employer", "Company"))
                years = h.get("duration_years", h.get("years", "N/A"))
                records.append(f"{role} at {company} ({years}y)")
            elif isinstance(h, str):
                records.append(h)

        return {
            "status": "SUPPORTED",
            "record_count": len(records),
            "records": records,
            "evidence": f"Itemized employment history documented across {len(records)} role(s): {'; '.join(records)}.",
            "is_supported": True,
            "inconsistency": None
        }

    if isinstance(history, str) and history.strip():
        return {
            "status": "SUPPORTED",
            "record_count": 1,
            "records": [history.strip()],
            "evidence": f"Employment history documented: {history.strip()}.",
            "is_supported": True,
            "inconsistency": None
        }

    # If role or company is in candidate root
    role = candidate.get("role", candidate.get("current_role", ""))
    company = candidate.get("company", candidate.get("current_company", ""))
    if role or company:
        rec_str = f"Current/Recent role: {role}" + (f" at {company}" if company else "")
        return {
            "status": "SUPPORTED",
            "record_count": 1,
            "records": [rec_str],
            "evidence": f"Employment background documented: {rec_str}.",
            "is_supported": True,
            "inconsistency": None
        }

    return {
        "status": "NOT_AVAILABLE",
        "record_count": 0,
        "records": [],
        "evidence": "Detailed itemized employment history not provided; evaluated via total experience.",
        "is_supported": True,
        "inconsistency": None
    }


def check_information_consistency(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cross-evaluates candidate fields for logical coherence, graduation vs experience anomalies,
    or internal data contradictions.
    """
    inconsistencies = []

    # 1. Experience vs itemized history
    raw_exp = candidate.get("experience_years", candidate.get("experience", 0.0))
    try:
        exp_years = float(raw_exp if raw_exp is not None else 0.0)
    except (ValueError, TypeError):
        exp_years = 0.0
    emp_history = candidate.get("employment_history", candidate.get("work_history", []))

    if isinstance(emp_history, list) and len(emp_history) > 0:
        itemized_total = 0.0
        for rec in emp_history:
            if isinstance(rec, dict):
                try:
                    itemized_total += float(rec.get("duration_years", rec.get("years", 0.0)))
                except (ValueError, TypeError):
                    pass
        if exp_years > 0 and itemized_total > 0 and exp_years > (itemized_total * 2.0) and (exp_years - itemized_total) >= 3.0:
            inconsistencies.append(
                f"Experience Discrepancy: Candidate declared {exp_years} years total experience, but itemized employment records sum to {itemized_total} years."
            )

    # 2. Education year vs experience duration check if graduation_year provided
    grad_year = candidate.get("graduation_year", candidate.get("grad_year", None))
    current_year = 2026
    if grad_year is not None:
        try:
            gy = int(grad_year)
            max_possible_exp = current_year - gy
            if exp_years > (max_possible_exp + 2) and exp_years > 3.0:
                inconsistencies.append(
                    f"Timeline Anomaly: Graduated in {gy} ({max_possible_exp} years ago), but claims {exp_years} years post-qualification experience."
                )
        except (ValueError, TypeError):
            pass

    return {
        "is_consistent": len(inconsistencies) == 0,
        "inconsistency_count": len(inconsistencies),
        "inconsistencies": inconsistencies
    }


def calculate_background_status(
    investigations: Dict[str, Any],
    inconsistencies: List[str],
    unsupported_claims_count: int = 0,
    contradicted_claims_count: int = 0,
    coverage_score: float = 100.0,
    missing_evidence: Optional[List[str]] = None
) -> str:
    """
    Computes overall evidence-based background investigation status.
    - VERIFIED_FROM_PROVIDED_EVIDENCE: All relevant declared BI information is supported/consistent,
      zero material unsupported claims, zero contradictions, and sufficient coverage.
    - PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE: Some information is supported, but some evidence is
      missing or unsupported, with no severe direct contradictions.
    - INSUFFICIENT_EVIDENCE: A substantial amount of required information is missing / inadequate coverage.
    - INCONSISTENCY_DETECTED: Direct factual contradictions or material claims directly conflicting with evidence.
    """
    # 1. Direct contradictions / anomalies
    if len(inconsistencies) > 0 or contradicted_claims_count > 0:
        return "INCONSISTENCY_DETECTED"

    statuses = [v.get("status") for v in investigations.values() if isinstance(v, dict)]

    if any(s == "CONTRADICTED" for s in statuses):
        return "INCONSISTENCY_DETECTED"

    edu_status = investigations.get("education", {}).get("status")
    exp_status = investigations.get("experience", {}).get("status")
    skill_status = investigations.get("skills", {}).get("status")

    # 2. Insufficient evidence check
    # Check if core fields are missing or coverage is inadequate (<= 70%)
    if skill_status == "MISSING_EVIDENCE" and edu_status == "MISSING_EVIDENCE":
        return "INSUFFICIENT_EVIDENCE"

    if skill_status == "MISSING_EVIDENCE" and exp_status == "MISSING_EVIDENCE":
        return "INSUFFICIENT_EVIDENCE"

    if coverage_score <= 70.0 and (skill_status == "MISSING_EVIDENCE" or edu_status == "MISSING_EVIDENCE" or exp_status == "MISSING_EVIDENCE"):
        return "INSUFFICIENT_EVIDENCE"

    missing_cnt = sum(1 for s in [edu_status, exp_status, skill_status] if s == "MISSING_EVIDENCE")
    if missing_cnt >= 2 or coverage_score < 65.0:
        return "INSUFFICIENT_EVIDENCE"

    # 3. Unsupported claims check (from Evidence Traceability or profile investigation)
    if unsupported_claims_count > 0:
        return "PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE"

    # 4. Partial verification check (missing optional dimensions, partial experience, or minor gaps)
    missing_evidence_list = missing_evidence or []
    if len(missing_evidence_list) > 0:
        return "PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE"

    if any(s in ["MISSING_EVIDENCE", "PARTIALLY_SUPPORTED"] for s in [edu_status, exp_status, skill_status]):
        return "PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE"

    cert_status = investigations.get("certifications", {}).get("status")
    proj_status = investigations.get("projects", {}).get("status")
    emp_status = investigations.get("employment_history", {}).get("status")

    if any(s == "MISSING_EVIDENCE" for s in [cert_status, proj_status, emp_status]):
        return "PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE"

    # 5. Verified check
    if edu_status == "SUPPORTED" and exp_status == "SUPPORTED" and skill_status == "SUPPORTED":
        return "VERIFIED_FROM_PROVIDED_EVIDENCE"

    if any(s in ["SUPPORTED", "PARTIALLY_SUPPORTED"] for s in [edu_status, exp_status, skill_status]):
        return "PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE"

    return "INSUFFICIENT_EVIDENCE"


def run_background_investigation(
    candidate: Dict[str, Any],
    job: Optional[Dict[str, Any]] = None,
    evidence_traceability: Optional[Dict[str, Any]] = None,
    explanation: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes full Evidence-Based Candidate Background Investigation across all 6 core dimensions:
    1. Education Verification
    2. Experience Verification
    3. Certification Evidence
    4. Skill Corroboration
    5. Project Portfolio Evidence
    6. Employment History & Consistency Analysis
    """
    edu_inv = investigate_education(candidate, job)
    exp_inv = investigate_experience(candidate, job)
    cert_inv = investigate_certifications(candidate, job)
    skill_inv = investigate_skills(candidate, job)
    proj_inv = investigate_projects(candidate, job)
    emp_inv = investigate_employment_history(candidate, job)

    investigations = {
        "education": edu_inv,
        "experience": exp_inv,
        "certifications": cert_inv,
        "skills": skill_inv,
        "projects": proj_inv,
        "employment_history": emp_inv
    }

    consistency_res = check_information_consistency(candidate)
    inconsistencies = list(consistency_res["inconsistencies"])

    # Collect any contradictions from individual investigations
    for dim_name, inv in investigations.items():
        if inv.get("inconsistency"):
            inconsistencies.append(f"{dim_name.capitalize()}: {inv['inconsistency']}")

    # Check evidence traceability if explanation or evidence_traceability provided
    if evidence_traceability is None:
        expl = explanation or candidate.get("explanation")
        if expl:
            try:
                from modules.evidence import evaluate_evidence_traceability
                evidence_traceability = evaluate_evidence_traceability(expl, candidate, job)
            except Exception:
                pass

    unsupported_claims_count = 0
    contradicted_claims_count = 0
    unsupported_qualification_claims = []
    contradicted_qualification_claims = []

    if evidence_traceability and isinstance(evidence_traceability, dict):
        claims = evidence_traceability.get("claims", [])
        qual_fields = {
            "skills", "technical_skills", "skill",
            "experience_years", "experience", "years_exp",
            "education", "degree", "required_education",
            "certifications", "certifications_count",
            "projects", "portfolio", "employment_history", "work_history"
        }
        for c in claims:
            if isinstance(c, dict):
                src = str(c.get("source_field", "")).lower()
                st = str(c.get("status", "")).upper()
                is_qual_field = src in qual_fields or any(qf in src for qf in ["skill", "exp", "edu", "cert", "proj", "employ", "hist"])
                if is_qual_field:
                    if st == "UNSUPPORTED":
                        unsupported_claims_count += 1
                        unsupported_qualification_claims.append(c.get("claim", "Unsupported qualification claim"))
                    elif st == "CONTRADICTED":
                        contradicted_claims_count += 1
                        contradicted_qualification_claims.append(c.get("claim", "Contradicted qualification claim"))
                        inconsistencies.append(f"Evidence Contradiction: {c.get('claim', '')} ({c.get('evidence', '')})")

    # Missing evidence items
    missing_evidence = []
    for dim_name, inv in investigations.items():
        if inv.get("status") == "MISSING_EVIDENCE":
            missing_evidence.append(dim_name)

    # Evidence coverage score calculation (transparent evidence completeness metric)
    dim_weights = {
        "education": 0.25,
        "experience": 0.25,
        "skills": 0.25,
        "certifications": 0.10,
        "projects": 0.10,
        "employment_history": 0.05
    }
    coverage_score = 0.0
    for dim, w in dim_weights.items():
        st = investigations.get(dim, {}).get("status")
        if st == "SUPPORTED":
            coverage_score += (w * 100.0)
        elif st in ["PARTIALLY_SUPPORTED", "NOT_AVAILABLE"]:
            coverage_score += (w * 70.0)
        elif st == "MISSING_EVIDENCE":
            coverage_score += 0.0
        elif st == "CONTRADICTED":
            coverage_score -= (w * 50.0)

    coverage_score = round(max(0.0, min(100.0, coverage_score)), 1)

    overall_status = calculate_background_status(
        investigations=investigations,
        inconsistencies=inconsistencies,
        unsupported_claims_count=unsupported_claims_count,
        contradicted_claims_count=contradicted_claims_count,
        coverage_score=coverage_score,
        missing_evidence=missing_evidence
    )

    is_consistent = (len(inconsistencies) == 0 and overall_status != "INCONSISTENCY_DETECTED")
    c_id = str(candidate.get("candidate_id", candidate.get("id", "UNKNOWN")))
    c_name = str(candidate.get("name", "Candidate"))

    # Human-readable summary
    if overall_status == "VERIFIED_FROM_PROVIDED_EVIDENCE":
        summary = f"All primary credentials (Education, Experience, Skills) for {c_name} are fully supported by provided candidate facts with zero contradictions or unsupported claims."
    elif overall_status == "PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE":
        if unsupported_claims_count > 0:
            summary = f"Candidate credentials for {c_name} are partially supported with {unsupported_claims_count} unsupported qualification claim(s) and {len(missing_evidence)} evidence gap(s)."
        else:
            summary = f"Candidate credentials for {c_name} are partially supported with {len(missing_evidence)} non-critical evidence gap(s)."
    elif overall_status == "INCONSISTENCY_DETECTED":
        summary = f"Internal data inconsistencies or contradictory claims detected during candidate investigation for {c_name}: {'; '.join(inconsistencies[:2])}."
    else:
        summary = f"Insufficient credential evidence supplied in candidate profile for {c_name} (Evidence coverage: {coverage_score}%)."

    return {
        "candidate_id": c_id,
        "candidate_name": c_name,
        "overall_status": overall_status,
        "evidence_coverage_percentage": coverage_score,
        "investigations": investigations,
        "inconsistencies": inconsistencies,
        "missing_evidence": missing_evidence,
        "unsupported_qualification_claims": unsupported_qualification_claims,
        "unsupported_claims_count": unsupported_claims_count,
        "contradicted_claims_count": contradicted_claims_count,
        "is_consistent": is_consistent,
        "summary": summary,
        "disclaimer": BI_DISCLAIMER
    }
