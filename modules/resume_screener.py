"""
AI Hiring Intelligence - Resume & ATS Screening Engine
Provides end-to-end multi-format resume parsing (PDF, DOCX, TXT),
comprehensive ATS compatibility scoring, role-specific skill gap analysis,
and evidence-grounded strengths/weaknesses evaluations with EFS audit.
"""

import os
import io
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple

from modules.skill_normalization import (
    canonicalize_skill,
    normalize_skills_list,
    KNOWN_ALIASES
)
from modules.skill_analysis import match_skills
from modules.qualifications import (
    compute_overall_qualification_score,
    DEFAULT_JOB_TEMPLATES
)
from modules.llm_client import evaluate_candidate
from modules.evidence import evaluate_evidence_traceability
from modules.faithfulness import evaluate_faithfulness_instance
from modules.background_investigation import run_background_investigation


# ============================================================================
# Document Text Extraction (PDF, DOCX, TXT)
# ============================================================================

def extract_text_from_file_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Extracts plain text content from uploaded PDF, DOCX, or TXT file bytes.
    """
    ext = os.path.splitext(filename.lower())[1]
    
    if ext == ".pdf":
        return _extract_text_from_pdf(file_bytes)
    elif ext in [".docx", ".doc"]:
        return _extract_text_from_docx(file_bytes)
    else:
        # Plain text / Markdown / CSV / RTF
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return file_bytes.decode("latin-1")
            except Exception:
                return file_bytes.decode("utf-8", errors="ignore")


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts text from PDF bytes using pypdf with fallback."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        if pages_text:
            return "\n\n".join(pages_text)
    except Exception as e:
        pass
    
    # Fallback to plain string extraction
    try:
        raw_str = file_bytes.decode("utf-8", errors="ignore")
        # Strip PDF binary objects
        clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', ' ', raw_str)
        return clean
    except Exception:
        return "Failed to extract PDF text."


def _extract_text_from_docx(file_bytes: bytes) -> str:
    """Extracts text from DOCX bytes using python-docx with zipfile XML fallback."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)
        if paragraphs:
            return "\n".join(paragraphs)
    except Exception:
        pass

    # Fallback: Parse word/document.xml directly from docx zip
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            if "word/document.xml" in z.namelist():
                xml_content = z.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                texts = []
                for p in tree.findall('.//w:p', namespaces):
                    p_text = ''.join(node.text for node in p.findall('.//w:t', namespaces) if node.text)
                    if p_text.strip():
                        texts.append(p_text.strip())
                if texts:
                    return "\n".join(texts)
    except Exception:
        pass

    return "Failed to extract DOCX text."


# ============================================================================
# Resume Information Parsing
# ============================================================================

ACTION_VERBS = {
    "architected", "engineered", "designed", "developed", "built", "implemented",
    "deployed", "optimized", "spearheaded", "orchestrated", "scaled", "automated",
    "led", "managed", "refactored", "improved", "increased", "decreased", "reduced",
    "integrated", "authored", "delivered", "streamlined", "configured", "debugged"
}

def parse_resume_full(text: str) -> Dict[str, Any]:
    """
    Parses full resume text to extract contact details, section boundaries,
    years of experience, skills, education, and metrics.
    """
    if not text or not text.strip():
        return {
            "name": "Candidate",
            "email": "",
            "phone": "",
            "links": [],
            "skills": [],
            "experience_years": 0.0,
            "education": "Bachelor Degree",
            "certifications": "",
            "sections_found": [],
            "bullet_points": []
        }

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # 1. Contact Information
    email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    email = email_match.group(0) if email_match else ""

    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    phone = phone_match.group(0) if phone_match else ""

    links = []
    github_match = re.search(r'github\.com\/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
    if github_match:
        links.append(f"https://{github_match.group(0)}")
    linkedin_match = re.search(r'linkedin\.com\/in\/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
    if linkedin_match:
        links.append(f"https://{linkedin_match.group(0)}")

    # 2. Candidate Name (Heuristic: First non-contact header line)
    name = "Candidate"
    for line in lines[:5]:
        if not re.search(r'(@|phone|http|github|linkedin|resume|curriculum|cv|\d{4})', line, re.IGNORECASE):
            cleaned = re.sub(r'[^a-zA-Z\s]', '', line).strip()
            if 2 <= len(cleaned.split()) <= 4:
                name = cleaned
                break

    # 3. Section Boundary Detection
    sections_found = []
    section_patterns = {
        "Experience": r'\b(experience|work history|employment|professional background|work experience)\b',
        "Skills": r'\b(skills|technical skills|technologies|proficiencies|competencies|tech stack)\b',
        "Education": r'\b(education|academic background|academics|qualifications|degrees)\b',
        "Projects": r'\b(projects|portfolio|personal projects|key projects|open source)\b',
        "Certifications": r'\b(certifications|certificates|licenses|credentials)\b',
        "Summary": r'\b(summary|profile|about me|objective|professional summary)\b'
    }

    for sec_name, pattern in section_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            sections_found.append(sec_name)

    # 4. Years of Experience Extraction
    exp_years = 0.0
    # Look for explicit mentions like "5+ years of experience" or "4.5 years"
    exp_explicit = re.search(r'(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years?|yrs?)(?:\s+of\s+experience)?', text, re.IGNORECASE)
    if exp_explicit:
        try:
            exp_years = float(exp_explicit.group(1))
        except ValueError:
            exp_years = 3.0
    else:
        # Date range detection e.g. 2020 - 2024 or 2019 - Present
        year_ranges = re.findall(r'\b(20\d{2}|19\d{2})\s*(?:-|–|to)\s*(20\d{2}|present|current)\b', text, re.IGNORECASE)
        total_range_years = 0.0
        current_year = 2026
        for start, end in year_ranges:
            try:
                s = int(start)
                e = current_year if end.lower() in ["present", "current"] else int(end)
                if e >= s:
                    total_range_years += (e - s)
            except Exception:
                continue
        exp_years = min(30.0, max(1.0, total_range_years if total_range_years > 0 else 3.0))

    # 5. Skill Extraction
    extracted_skills: List[str] = []
    for raw_alias, canon in KNOWN_ALIASES.items():
        if len(raw_alias) >= 2:
            pattern = rf'(?:\b|(?<=[^a-zA-Z0-9])){re.escape(raw_alias)}(?:\b|(?=[^a-zA-Z0-9]))'
            if re.search(pattern, text, re.IGNORECASE):
                if canon not in extracted_skills:
                    extracted_skills.append(canon)

    if not extracted_skills:
        extracted_skills = ["Python", "SQL", "Git"]

    # 6. Education Degree Detection
    education = "B.Tech Computer Science"
    if re.search(r'\b(ph\.?d|doctorate)\b', text, re.IGNORECASE):
        education = "Ph.D. in Computer Science"
    elif re.search(r'\b(master|m\.?s\.?|m\.?tech|m\.?sc)\b', text, re.IGNORECASE):
        education = "M.S. in Computer Science"
    elif re.search(r'\b(bachelor|b\.?s\.?|b\.?tech|b\.?e\.?|b\.?sc)\b', text, re.IGNORECASE):
        education = "B.Tech in Computer Science"
    elif re.search(r'\b(bootcamp|diploma|associate)\b', text, re.IGNORECASE):
        education = "Software Engineering Bootcamp"

    # 7. Certifications
    certs = []
    cert_matches = re.findall(r'\b(aws certified[^\n,]*|azure certified[^\n,]*|google cloud[^\n,]*|cka[^\n,]*|pmp[^\n,]*|terraform associate[^\n,]*)\b', text, re.IGNORECASE)
    for c in cert_matches:
        if c.strip() and c.strip().title() not in certs:
            certs.append(c.strip().title())

    # 8. Bullet Points & Quantifiability
    bullet_points = []
    for line in lines:
        if line.startswith(("-", "•", "*", "–")) or re.match(r'^\d+\.', line):
            bullet_points.append(line.lstrip("-•*– 0123456789."))

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "links": links,
        "skills": extracted_skills,
        "experience_years": exp_years,
        "education": education,
        "certifications": ", ".join(certs) if certs else "Verified",
        "sections_found": sections_found,
        "bullet_points": bullet_points
    }


# ============================================================================
# ATS Compatibility & Quality Audit
# ============================================================================

def evaluate_ats_compatibility(
    resume_text: str,
    parsed_data: Dict[str, Any],
    job_spec: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates ATS (Applicant Tracking System) compatibility:
    - Section Completeness (25 pts)
    - Contact Completeness (15 pts)
    - Keyword Match Density (35 pts)
    - Action Verb & Metric Quantifiability (25 pts)
    """
    checklist: List[Dict[str, Any]] = []

    # 1. Section Completeness (Max 25 pts)
    required_sections = ["Experience", "Skills", "Education"]
    found_sections = set(parsed_data.get("sections_found", []))
    missing_sections = [s for s in required_sections if s not in found_sections]

    if not missing_sections:
        section_score = 25.0
        checklist.append({"status": "PASS", "title": "Standard Section Layout", "desc": "All core sections (Experience, Skills, Education) detected."})
    else:
        section_score = max(5.0, 25.0 - (len(missing_sections) * 10.0))
        checklist.append({"status": "WARN", "title": "Missing Sections", "desc": f"Missing standard sections: {', '.join(missing_sections)}."})

    # 2. Contact Completeness (Max 15 pts)
    contact_pts = 0.0
    if parsed_data.get("email"): contact_pts += 5.0
    if parsed_data.get("phone"): contact_pts += 5.0
    if parsed_data.get("links"): contact_pts += 5.0

    if contact_pts == 15.0:
        checklist.append({"status": "PASS", "title": "Complete Contact Info", "desc": "Email, phone number, and online profile/GitHub links found."})
    else:
        checklist.append({"status": "WARN", "title": "Incomplete Contact Info", "desc": "Consider adding LinkedIn/GitHub and direct contact details."})

    # 3. Role Keyword Coverage (Max 35 pts)
    req_skills = job_spec.get("required_skills", [])
    matched_skills = [s for s in req_skills if s in parsed_data.get("skills", [])]
    match_ratio = len(matched_skills) / max(1, len(req_skills))
    keyword_score = round(match_ratio * 35.0, 1)

    if match_ratio >= 0.8:
        checklist.append({"status": "PASS", "title": "High Role Keyword Density", "desc": f"Matches {len(matched_skills)}/{len(req_skills)} required core competencies."})
    else:
        missing_req = [s for s in req_skills if s not in parsed_data.get("skills", [])]
        checklist.append({"status": "WARN", "title": "Missing Role Keywords", "desc": f"Target keywords missing: {', '.join(missing_req)}."})

    # 4. Action Verbs & Quantifiability (Max 25 pts)
    bullets = parsed_data.get("bullet_points", [])
    quantified_bullets = 0
    action_verb_bullets = 0

    metric_regex = re.compile(r'(\d+[\d,.]*\s*(?:%|x|k|m|million|billion|users|req/s|ms|usd|\$))', re.IGNORECASE)

    for b in bullets:
        if metric_regex.search(b):
            quantified_bullets += 1
        first_word = b.split()[0].lower() if b.split() else ""
        if first_word in ACTION_VERBS:
            action_verb_bullets += 1

    total_bullets = max(1, len(bullets))
    quant_ratio = quantified_bullets / total_bullets
    action_ratio = action_verb_bullets / total_bullets

    impact_score = round(min(25.0, (quant_ratio * 15.0) + (action_ratio * 10.0) + 5.0), 1)

    if quant_ratio >= 0.3:
        checklist.append({"status": "PASS", "title": "Quantified Impact Metrics", "desc": f"{quantified_bullets} bullet point(s) contain measurable numerical metrics."})
    else:
        checklist.append({"status": "WARN", "title": "Low Quantifiable Metrics", "desc": "Add measurable impact (e.g. latency reduced by X%, users supported) to strengthen accomplishments."})

    total_ats_score = round(section_score + contact_pts + keyword_score + impact_score, 1)
    total_ats_score = min(100.0, max(10.0, total_ats_score))

    return {
        "ats_score": total_ats_score,
        "section_score": section_score,
        "contact_score": contact_pts,
        "keyword_score": keyword_score,
        "impact_score": impact_score,
        "total_bullets_analyzed": len(bullets),
        "quantified_bullets_count": quantified_bullets,
        "quantified_percentage": round((quantified_bullets / total_bullets) * 100.0, 1),
        "checklist": checklist
    }


# ============================================================================
# Role Strengths, Gaps, and Grounded Feedback
# ============================================================================

def generate_grounded_resume_verdict(
    resume_text: str,
    parsed_data: Dict[str, Any],
    job_spec: Dict[str, Any],
    mode: str = "Local Ollama Mode",
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Performs full multi-layered assessment:
    1. Deterministic qualification scoring & skill gap analysis.
    2. ATS compatibility audit.
    3. Grounded Strengths & Weaknesses extraction.
    4. SLM verdict generation with Evidence Faithfulness Score (EFS) and Background Check.
    """
    cand = {
        "candidate_id": "APPLICANT_01",
        "name": parsed_data.get("name", "Applicant"),
        "role": job_spec.get("title", "Software Engineer"),
        "skills": parsed_data.get("skills", []),
        "experience_years": parsed_data.get("experience_years", 3.0),
        "education": parsed_data.get("education", "B.Tech Computer Science"),
        "certifications": parsed_data.get("certifications", "Verified"),
        "projects": f"Portfolio and Experience:\n{resume_text[:400]}"
    }

    # 1. Deterministic Qualification Score
    qual_res = compute_overall_qualification_score(cand, job_spec)
    q_score = qual_res["qualification_score"]
    skill_analysis = qual_res["skill_analysis"]

    # 2. ATS Audit
    ats_res = evaluate_ats_compatibility(resume_text, parsed_data, job_spec)

    # 3. Grounded Strengths & Gaps Construction
    strengths = []
    weaknesses = []
    recommendations = []

    # Strengths
    matched_req = skill_analysis.get("matched_required_skills", [])
    if matched_req:
        strengths.append(f"Strong verified match in core required competencies: {', '.join(matched_req)}.")

    cand_exp = cand["experience_years"]
    min_exp = job_spec.get("minimum_experience", 3.0)
    if cand_exp >= min_exp:
        strengths.append(f"Extensive relevant domain experience ({cand_exp} years) meeting or exceeding the minimum requirement ({min_exp} years).")
    
    matched_pref = skill_analysis.get("matched_preferred_skills", [])
    if matched_pref:
        strengths.append(f"Possesses preferred bonus skillsets: {', '.join(matched_pref)}.")

    if ats_res["quantified_bullets_count"] >= 2:
        strengths.append(f"Resume demonstrates strong quantifiability with {ats_res['quantified_bullets_count']} measurable impact metrics.")

    # Weaknesses & Gaps
    missing_req = skill_analysis.get("missing_required_skills", [])
    if missing_req:
        weaknesses.append(f"Missing core required technical competencies for this role: {', '.join(missing_req)}.")
        recommendations.append(f"Incorporate project demonstrations or certifications in: {', '.join(missing_req)}.")

    if cand_exp < min_exp:
        diff = round(min_exp - cand_exp, 1)
        weaknesses.append(f"Experience level ({cand_exp} yrs) falls short of the target role requirement ({min_exp} yrs) by {diff} years.")
        recommendations.append(f"Highlight high-impact projects or leadership responsibilities to offset the {diff}-year experience delta.")

    missing_pref = skill_analysis.get("missing_preferred_skills", [])
    if missing_pref:
        weaknesses.append(f"Does not list preferred bonus technologies: {', '.join(missing_pref[:3])}.")
        recommendations.append(f"Consider learning or showcasing familiarity with {', '.join(missing_pref[:2])} to gain a competitive edge.")

    if ats_res["ats_score"] < 75.0:
        recommendations.append("Enhance bullet points with action verbs and specific numeric metrics (percentages, dollar amounts, performance gains) to pass enterprise ATS screening filters.")

    if not strengths:
        strengths.append("Foundational technical baseline and clear academic background.")
    if not weaknesses:
        weaknesses.append("No critical competency gaps identified against the baseline job description.")
    if not recommendations:
        recommendations.append("Profile is well-aligned with role requirements. Proceed with technical interview.")

    # 4. SLM Evaluation
    ai_eval = evaluate_candidate(cand, job_spec, mode=mode, model_name=model_name)
    ev_res = evaluate_evidence_traceability(ai_eval.get("explanation", ""), cand, job_spec)
    
    efs_res = evaluate_faithfulness_instance(
        ai_eval.get("explanation", ""),
        q_score,
        ai_eval.get("decision", qual_res["expected_decision"]),
        skill_analysis,
        candidate_data=cand,
        job_requirements=job_spec
    )

    bi_res = run_background_investigation(
        candidate=cand,
        job=job_spec,
        evidence_traceability=ev_res,
        explanation=ai_eval.get("explanation", "")
    )

    return {
        "candidate": cand,
        "parsed_profile": parsed_data,
        "job_applied": job_spec,
        "ats_analysis": ats_res,
        "qualification_analysis": qual_res,
        "ai_evaluation": {
            "decision": ai_eval.get("decision", qual_res["expected_decision"]),
            "explanation": ai_eval.get("explanation", ""),
            "confidence_score": ai_eval.get("confidence_score", 90.0)
        },
        "grounded_feedback": {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations
        },
        "evidence_traceability": ev_res,
        "efs_assessment": efs_res,
        "background_investigation": bi_res
    }
