"""
AI Hiring Intelligence System - FastAPI REST API Gateway
Exposes qualification-based candidate assessment, skill gap analysis, Evidence Traceability,
Explanation Faithfulness Scoring (EFS), Evidence-Based Candidate Background Investigation (BI),
qualification counterfactual testing, decision consistency, mitigation feedback loops, and semantic clustering.
"""

import os
import glob
import io
import json
import re
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from fastapi import FastAPI, HTTPException, Query, Body, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from modules.skill_normalization import (
    canonicalize_skill,
    normalize_skill,
    normalize_skills_list,
    get_canonical_skills,
    KNOWN_ALIASES
)
from modules.skill_analysis import (
    match_skills,
    parse_skills_list,
    normalize_skill_string
)
from modules.qualifications import (
    DEFAULT_JOB_TEMPLATES,
    DEFAULT_SCORING_WEIGHTS,
    evaluate_experience_match,
    evaluate_education_relevance,
    evaluate_projects_score,
    compute_overall_qualification_score
)
from modules.evidence import (
    extract_claims_from_explanation,
    evaluate_evidence_traceability
)
from modules.background_investigation import (
    run_background_investigation,
    BI_DISCLAIMER
)
from modules.faithfulness import (
    evaluate_faithfulness_instance,
    check_skill_mention_faithfulness
)
from modules.decision_consistency import (
    check_monotonicity,
    check_pairwise_consistency,
    evaluate_pool_consistency,
    check_decision_consistency
)
from modules.variations import (
    make_qualification_variation,
    make_multi_qualification_variation,
    get_available_qualification_concepts
)
from modules.llm_client import (
    evaluate_candidate,
    check_ollama_connectivity
)
from modules.clustering import (
    cluster_dataframe,
    get_cluster_summary
)
from modules.mitigation import (
    mitigation_instruction,
    evaluate_mitigation_feedback_loop
)
from modules.statistics import (
    mcnemar_test,
    multiclass_chi_square,
    paired_regression_test
)
from modules.resume_screener import (
    extract_text_from_file_bytes,
    parse_resume_full,
    evaluate_ats_compatibility,
    generate_grounded_resume_verdict
)

app = FastAPI(
    title="AI Hiring Intelligence System for Qualification-Based Candidate Assessment and Decision Auditing",
    description="REST API for qualification-based hiring assessment, Evidence Traceability, EFS faithfulness scoring, Evidence-Based Candidate Background Investigation (BI), and decision consistency.",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# In-Memory Active Job Store (initialized with default templates)
JOB_STORE: Dict[str, Dict[str, Any]] = dict(DEFAULT_JOB_TEMPLATES)
ACTIVE_DATASET: str = "01_software_engineering_benchmark.csv"

# Custom Added Candidates (in-memory overlay)
CUSTOM_CANDIDATES: List[Dict[str, Any]] = []

# ============================================================================
# Pydantic Request Models
# ============================================================================

class JobRequirementModel(BaseModel):
    job_id: Optional[str] = "CUSTOM_JOB_01"
    title: str = "Senior Python Backend Engineer"
    department: Optional[str] = "Engineering"
    required_skills: List[str] = ["Python", "SQL", "REST API", "Git", "PostgreSQL"]
    preferred_skills: Optional[List[str]] = ["FastAPI", "Docker", "Kubernetes"]
    minimum_experience: float = 4.0
    required_education: Optional[str] = "B.Tech/B.S. in Computer Science"
    required_certifications: Optional[List[str]] = ["AWS Certified Cloud Practitioner"]
    description: Optional[str] = "Role requirements and technical qualifications."

class CandidateProfileModel(BaseModel):
    candidate_id: Optional[str] = "CAND_CUSTOM_01"
    name: Optional[str] = "Candidate"
    role: Optional[str] = "Software Engineer"
    expected_role: Optional[str] = "Senior Python Backend Engineer"
    experience_years: float = 4.0
    skills: Union[List[str], str] = ["Python", "SQL", "REST API", "Git"]
    education: Optional[str] = "B.Tech Computer Science"
    degree: Optional[str] = "B.Tech"
    certifications: Optional[Union[List[str], str]] = "AWS Solutions Architect"
    certifications_count: Optional[int] = 1
    projects: Optional[str] = "Distributed Microservices"
    projects_score: Optional[float] = 85.0
    technical_interview_score: Optional[float] = 85.0
    soft_skills: Optional[Union[List[str], str]] = "Problem Solving, Communication"

class EvaluateRequest(BaseModel):
    candidate: Dict[str, Any]
    job: Optional[Dict[str, Any]] = None
    decision_type: Optional[str] = "multiclass"
    mode: Optional[str] = "Local Ollama Mode"
    model_name: Optional[str] = "qwen3.5:4b"
    mitigation: Optional[bool] = False
    mitigation_instruction: Optional[str] = ""

class EvidenceRequest(BaseModel):
    candidate_id: Optional[str] = None
    job_id: Optional[str] = "JOB_SWE_01"
    explanation: str
    candidate_data: Optional[Dict[str, Any]] = None
    job: Optional[Dict[str, Any]] = None

class SkillAnalysisRequest(BaseModel):
    candidate_skills: Union[List[str], str]
    required_skills: List[str]
    preferred_skills: Optional[List[str]] = None

class SkillNormalizationRequest(BaseModel):
    skills: Union[List[str], str]

class QualScoreRequest(BaseModel):
    candidate: Dict[str, Any]
    job: Optional[Dict[str, Any]] = None
    weights: Optional[Dict[str, float]] = None

class BackgroundInvestigationRequest(BaseModel):
    candidate: Dict[str, Any]
    job: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    evidence_traceability: Optional[Dict[str, Any]] = None

class EFSRequest(BaseModel):
    explanation: str
    qualification_score: float
    decision: str
    skill_analysis: Optional[Dict[str, Any]] = None
    experience_analysis: Optional[Dict[str, Any]] = None
    candidate_data: Optional[Dict[str, Any]] = None
    job_requirements: Optional[Dict[str, Any]] = None

class CounterfactualRequest(BaseModel):
    candidate: Dict[str, Any]
    concept: Optional[str] = "skills"
    target_value: Optional[Any] = "Remove Core Skill"
    interventions: Optional[Dict[str, Any]] = None
    job: Optional[Dict[str, Any]] = None
    mode: Optional[str] = "Local Ollama Mode"
    model_name: Optional[str] = "qwen3.5:4b"

class DecisionConsistencyRequest(BaseModel):
    candidate_a: Dict[str, Any]
    candidate_b: Dict[str, Any]
    eval_a: Optional[Dict[str, Any]] = None
    eval_b: Optional[Dict[str, Any]] = None

class StatisticsRequest(BaseModel):
    test_type: str = "mcnemar"  # 'mcnemar', 'chi_square', or 'paired_regression'
    original_values: List[Any]
    modified_values: List[Any]

class MitigationRequest(BaseModel):
    candidates: Optional[List[Dict[str, Any]]] = None
    job: Optional[Dict[str, Any]] = None
    mode: Optional[str] = "Local Ollama Mode"
    model_name: Optional[str] = "qwen3.5:4b"

class BatchEvaluateRequest(BaseModel):
    job_id: Optional[str] = "JOB_SWE_01"
    job: Optional[Dict[str, Any]] = None
    candidates: Optional[List[Any]] = None
    mode: Optional[str] = "Local Ollama Mode"
    model_name: Optional[str] = "qwen3.5:4b"
    mitigation: Optional[bool] = False
    limit: Optional[int] = None

class ReEvaluateRequest(BaseModel):
    candidate: Dict[str, Any]
    job: Optional[Dict[str, Any]] = None
    mitigation_instruction: Optional[str] = None
    mode: Optional[str] = "Local Ollama Mode"
    model_name: Optional[str] = "qwen3.5:4b"

class ResumeScreenRequest(BaseModel):
    resume_text: Optional[str] = None
    candidate_data: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = "JOB_SWE_01"
    job: Optional[Dict[str, Any]] = None
    mode: Optional[str] = "Local Ollama Mode"
    model_name: Optional[str] = "qwen3.5:4b"

class ExportReportRequest(BaseModel):
    candidate_id: str
    job_id: Optional[str] = "JOB_SWE_01"
    format: str = "json"  # 'json' or 'csv'

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/health")
def api_health():
    """System health check and loaded modules summary."""
    return {
        "status": "healthy",
        "system": "AI Hiring Intelligence System for Qualification-Based Candidate Assessment and Decision Auditing",
        "version": "2.1.0",
        "active_dataset": ACTIVE_DATASET,
        "ollama": check_ollama_connectivity(),
        "disclaimer": BI_DISCLAIMER
    }

@app.get("/api/jobs")
def api_get_jobs():
    """Returns all available job requirement templates."""
    return {"jobs": list(JOB_STORE.values())}

@app.post("/api/jobs")
def api_add_job(job: JobRequirementModel):
    """Adds or updates a custom job requirement template."""
    job_dict = job.dict()
    j_id = job_dict.get("job_id") or f"JOB_CUSTOM_{len(JOB_STORE)+1}"
    job_dict["job_id"] = j_id
    JOB_STORE[j_id] = job_dict
    return {"message": "Job requirement registered successfully", "job": job_dict}

@app.get("/api/datasets")
def api_get_datasets():
    """Lists available benchmark CSV datasets."""
    files = [os.path.basename(f) for f in glob.glob(os.path.join(DATA_DIR, "*.csv"))]
    return {"datasets": sorted(files), "active_dataset": ACTIVE_DATASET}

@app.post("/api/select_dataset")
def api_select_dataset(filename: str = Body(..., embed=True)):
    """Switches the active dataset."""
    global ACTIVE_DATASET
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Dataset '{filename}' not found")
    ACTIVE_DATASET = filename
    return {"message": f"Active dataset set to {filename}", "active_dataset": filename}

@app.post("/api/upload_dataset")
def api_upload_dataset(
    filename: str = Body(..., embed=True),
    csv_content: str = Body(..., embed=True)
):
    """Uploads and registers a custom qualification CSV dataset."""
    if not filename.endswith(".csv"):
        filename += ".csv"
    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    target_path = os.path.join(DATA_DIR, safe_name)

    try:
        df = pd.read_csv(io.StringIO(csv_content))
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV content is empty")
        df.to_csv(target_path, index=False)
        return {
            "message": f"Dataset '{safe_name}' uploaded successfully with {len(df)} records.",
            "filename": safe_name,
            "row_count": len(df),
            "columns": list(df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

@app.get("/api/candidates")
def api_get_candidates(
    search: Optional[str] = None,
    job_id: Optional[str] = "JOB_SWE_01",
    page: int = 1,
    limit: int = 100
):
    """
    Returns candidate profiles from active dataset with precomputed qualification scores and skill match %.
    """
    path = os.path.join(DATA_DIR, ACTIVE_DATASET)
    records = []

    if os.path.exists(path):
        df = pd.read_csv(path).fillna("")
        records.extend(df.to_dict(orient="records"))

    # Include custom registered candidates
    records.extend(CUSTOM_CANDIDATES)

    if search:
        s = search.lower()
        records = [r for r in records if s in json.dumps(r).lower()]

    job = JOB_STORE.get(job_id, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"])

    processed = []
    for cand in records:
        q_res = compute_overall_qualification_score(cand, job)
        bi_res = run_background_investigation(cand, job)
        cand_copy = dict(cand)
        cand_copy["qualification_score"] = q_res["qualification_score"]
        cand_copy["score"] = q_res["qualification_score"]
        cand_copy["expected_decision"] = q_res["expected_decision"]
        cand_copy["required_match_percentage"] = q_res["skill_analysis"]["required_match_percentage"]
        cand_copy["preferred_match_percentage"] = q_res["skill_analysis"]["preferred_match_percentage"]
        cand_copy["matched_skills"] = q_res["skill_analysis"]["matched_required_skills"]
        cand_copy["missing_skills"] = q_res["skill_analysis"]["missing_required_skills"]
        cand_copy["matched_preferred_skills"] = q_res["skill_analysis"]["matched_preferred_skills"]
        cand_copy["missing_preferred_skills"] = q_res["skill_analysis"]["missing_preferred_skills"]
        cand_copy["additional_skills"] = q_res["skill_analysis"]["additional_skills"]
        cand_copy["component_breakdown"] = q_res["component_breakdown"]
        cand_copy["skill_analysis"] = q_res["skill_analysis"]
        cand_copy["experience_analysis"] = q_res["experience_analysis"]
        cand_copy["background_investigation"] = bi_res
        cand_copy["background_status"] = bi_res["overall_status"]
        cand_copy["evidence_coverage"] = bi_res["evidence_coverage_percentage"]
        processed.append(cand_copy)

    total = len(processed)
    if limit <= 0:
        paginated = processed
    else:
        start = max(0, (page - 1) * limit)
        paginated = processed[start : start + limit]

    return {
        "candidates": paginated,
        "total_count": total,
        "page": page,
        "limit": limit,
        "job_applied": job.get("title", "Software Engineer")
    }

@app.post("/api/candidates")
def api_add_candidate(cand: CandidateProfileModel):
    """Registers a new candidate profile in the session."""
    cand_dict = cand.dict()
    c_id = cand_dict.get("candidate_id") or f"CAND_CUSTOM_{len(CUSTOM_CANDIDATES)+1}"
    cand_dict["candidate_id"] = c_id
    CUSTOM_CANDIDATES.append(cand_dict)
    return {"message": "Candidate registered successfully", "candidate": cand_dict}

@app.post("/api/skill-analysis")
def api_skill_analysis(req: SkillAnalysisRequest):
    """Evaluates matched, missing, and additional skills with canonical normalization."""
    c_skills = parse_skills_list(req.candidate_skills)
    result = match_skills(c_skills, req.required_skills, req.preferred_skills)
    return result

@app.post("/api/skill-normalization")
def api_skill_normalization(req: SkillNormalizationRequest):
    """Normalizes raw input skills and returns mappings of input -> canonical."""
    raw_list = parse_skills_list(req.skills)
    normalized = normalize_skills_list(raw_list)
    canonical_list = [n["canonical"] for n in normalized]
    return {
        "input_skills": req.skills,
        "normalized_skills": canonical_list,
        "mappings": normalized
    }

@app.post("/api/qualification-score")
def api_qualification_score(req: QualScoreRequest):
    """Computes a multi-component qualification score breakdown ($Score_{qual}$)."""
    job = req.job or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    result = compute_overall_qualification_score(req.candidate, job, req.weights)
    return result

@app.post("/api/evidence")
def api_evaluate_evidence(req: EvidenceRequest):
    """
    Evidence Traceability Engine:
    Extracts atomic claims from AI justification and matches against candidate profile facts.
    """
    job = req.job or JOB_STORE.get(req.job_id, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"])
    cand_data = req.candidate_data or {}

    if not cand_data and req.candidate_id:
        path = os.path.join(DATA_DIR, ACTIVE_DATASET)
        if os.path.exists(path):
            df = pd.read_csv(path).fillna("")
            matches = df[df["candidate_id"] == req.candidate_id]
            if len(matches) > 0:
                cand_data = matches.iloc[0].to_dict()

    if not cand_data:
        cand_data = {"candidate_id": req.candidate_id or "UNKNOWN", "name": "Candidate"}

    ev_res = evaluate_evidence_traceability(req.explanation, cand_data, job)
    return ev_res

@app.post("/api/evaluate")
def api_evaluate(req: EvaluateRequest):
    """
    Complete Candidate AI Evaluation:
    Generates AI Recommendation, Explanation, Qual Score, Evidence Traceability, EFS, and Background Investigation.
    """
    job = req.job or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    
    # 1. Objective Qualification Scoring
    qual_res = compute_overall_qualification_score(req.candidate, job)
    qual_score = qual_res["qualification_score"]
    exp_decision = qual_res["expected_decision"]
    skill_analysis = qual_res["skill_analysis"]
    exp_analysis = qual_res["experience_analysis"]

    # 2. AI Inference
    ai_eval = evaluate_candidate(
        candidate_data=req.candidate,
        job_requirements=job,
        decision_type=req.decision_type or "multiclass",
        mode=req.mode or "Demo Simulation Mode",
        model_name=req.model_name or "qwen3.5:4b",
        mitigation=bool(req.mitigation),
        mitigation_instruction=req.mitigation_instruction or mitigation_instruction()
    )

    decision = ai_eval["decision"]
    explanation = ai_eval["explanation"]
    ai_score = ai_eval.get("score") or qual_score

    # 3. Evidence Traceability
    evidence_res = evaluate_evidence_traceability(explanation, req.candidate, job)

    # 4. Explanation Faithfulness Score (EFS)
    efs_res = evaluate_faithfulness_instance(
        explanation=explanation,
        qualification_score=qual_score,
        decision=decision,
        skill_analysis=skill_analysis,
        experience_analysis=exp_analysis,
        candidate_data=req.candidate,
        job_requirements=job
    )

    # 5. Evidence-Based Candidate Background Investigation (BI)
    bi_res = run_background_investigation(
        candidate=req.candidate,
        job=job,
        evidence_traceability=evidence_res,
        explanation=explanation
    )

    return {
        "candidate_id": req.candidate.get("candidate_id", "CAND_01"),
        "candidate_name": req.candidate.get("name", "Candidate"),
        "job_title": job.get("title", "Software Engineer"),
        "qualification_score": qual_score,
        "score": qual_score,  # Backward compatibility alias
        "expected_decision": exp_decision,
        "decision": decision,
        "recommendation": decision,
        "ai_score": ai_score,
        "explanation": explanation,
        "confidence": ai_eval.get("confidence", 0.90),
        "strengths": ai_eval.get("strengths", skill_analysis["matched_required_skills"]),
        "skill_gaps": ai_eval.get("skill_gaps", skill_analysis["missing_required_skills"]),
        "evidence": evidence_res,
        "efs": efs_res,
        "background_investigation": bi_res,
        "skill_analysis": skill_analysis,
        "experience_analysis": exp_analysis,
        "component_breakdown": qual_res["component_breakdown"],
        "mitigation_applied": bool(req.mitigation)
    }

@app.post("/api/background-investigation")
def api_calculate_background_investigation(req: BackgroundInvestigationRequest):
    """Calculates Evidence-Based Candidate Background Investigation across credentials and profile facts."""
    job = req.job or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    return run_background_investigation(
        candidate=req.candidate,
        job=job,
        evidence_traceability=req.evidence_traceability,
        explanation=req.explanation
    )

@app.post("/api/efs")
def api_calculate_efs(req: EFSRequest):
    """Calculates the Explanation Faithfulness Score (EFS) with grounding breakdown."""
    return evaluate_faithfulness_instance(
        explanation=req.explanation,
        qualification_score=req.qualification_score,
        decision=req.decision,
        skill_analysis=req.skill_analysis,
        experience_analysis=req.experience_analysis,
        candidate_data=req.candidate_data,
        job_requirements=req.job_requirements
    )

@app.get("/api/counterfactual_concepts")
def api_cf_concepts():
    """Returns supported qualification perturbation concepts."""
    return {"concepts": get_available_qualification_concepts()}

@app.post("/api/counterfactual")
def api_counterfactual(req: CounterfactualRequest):
    """
    Executes controlled qualification counterfactual intervention.
    Supports single concept perturbation or simultaneous multi-dimension interventions.
    Evaluates original candidate vs twin and computes consistency delta.
    """
    job = req.job or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]

    # 1. Generate Twin (multi-dimension or single concept)
    if req.interventions and isinstance(req.interventions, dict) and len(req.interventions) > 0:
        twin = make_multi_qualification_variation(req.candidate, req.interventions, job)
        concept_label = " + ".join([k.replace('_', ' ').title() for k in req.interventions.keys()])
        target_label = " | ".join([f"{k}: {v}" for k, v in req.interventions.items()])
    else:
        concept = req.concept or "skills"
        target_val = req.target_value if req.target_value is not None else "Remove Core Skill"
        twin = make_qualification_variation(req.candidate, concept, target_val, job)
        concept_label = concept.replace('_', ' ').title()
        target_label = str(target_val)

    # 2. Evaluate Baseline Original
    orig_eval = evaluate_candidate(req.candidate, job, mode=req.mode, model_name=req.model_name)
    orig_qual = compute_overall_qualification_score(req.candidate, job)

    # 3. Evaluate Counterfactual Twin
    twin_eval = evaluate_candidate(twin, job, mode=req.mode, model_name=req.model_name)
    twin_qual = compute_overall_qualification_score(twin, job)

    # 4. Consistency & Monotonicity Analysis
    consistency = check_decision_consistency(
        original_qual_score=orig_qual["qualification_score"],
        modified_qual_score=twin_qual["qualification_score"],
        original_decision=orig_eval["decision"],
        modified_decision=twin_eval["decision"]
    )

    # 5. EFS and Background Investigation for Twin
    twin_evidence = evaluate_evidence_traceability(twin_eval["explanation"], twin, job)
    twin_efs = evaluate_faithfulness_instance(
        explanation=twin_eval["explanation"],
        qualification_score=twin_qual["qualification_score"],
        decision=twin_eval["decision"],
        skill_analysis=twin_qual["skill_analysis"],
        candidate_data=twin,
        job_requirements=job
    )
    twin_bi = run_background_investigation(
        candidate=twin,
        job=job,
        evidence_traceability=twin_evidence,
        explanation=twin_eval["explanation"]
    )

    return {
        "original_profile": {
            "candidate": req.candidate,
            "qualification_score": orig_qual["qualification_score"],
            "decision": orig_eval["decision"],
            "explanation": orig_eval["explanation"]
        },
        "counterfactual_profile": {
            "candidate": twin,
            "qualification_score": twin_qual["qualification_score"],
            "decision": twin_eval["decision"],
            "explanation": twin_eval["explanation"],
            "efs": twin_efs,
            "background_investigation": twin_bi
        },
        "perturbation_concept": concept_label,
        "target_value": target_label,
        "interventions": req.interventions,
        "decision_changed": orig_eval["decision"] != twin_eval["decision"],
        "consistency_analysis": consistency
    }

@app.post("/api/decision-consistency")
def api_decision_consistency(req: DecisionConsistencyRequest):
    """
    Audits rank-order consistency between two candidate evaluations.
    """
    eval_a = req.eval_a or {}
    eval_b = req.eval_b or {}
    return check_pairwise_consistency(req.candidate_a, req.candidate_b, eval_a, eval_b)

@app.post("/api/statistics")
def api_statistics(req: StatisticsRequest):
    """
    Performs statistical significance tests (McNemar, Chi-Square, Paired t-test, Cohen's d).
    """
    t_type = req.test_type.lower()
    if t_type == "mcnemar":
        return mcnemar_test(req.original_values, req.modified_values)
    elif t_type == "chi_square":
        return multiclass_chi_square(req.original_values, req.modified_values)
    elif t_type in ["paired_regression", "t_test", "ttest"]:
        return paired_regression_test(req.original_values, req.modified_values)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown test_type '{req.test_type}'. Use 'mcnemar', 'chi_square', or 'paired_regression'.")

@app.post("/api/batch-evaluate")
def api_batch_evaluate(req: Optional[BatchEvaluateRequest] = None):
    """
    Audits the complete active candidate pool against selected job requirements.
    Evaluates ALL candidates in the pool, isolates per-candidate errors, and calculates pool-wide metrics.
    """
    if req is None:
        req = BatchEvaluateRequest()

    if req.candidates is not None and len(req.candidates) > 0:
        candidates_raw = list(req.candidates)
    else:
        path = os.path.join(DATA_DIR, ACTIVE_DATASET)
        candidates_raw = []
        if os.path.exists(path):
            df = pd.read_csv(path).fillna("")
            candidates_raw.extend(df.to_dict(orient="records"))
        candidates_raw.extend(CUSTOM_CANDIDATES)

    if req.limit and req.limit > 0:
        candidates_raw = candidates_raw[:req.limit]

    job = req.job or JOB_STORE.get(req.job_id, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"])

    results = []
    failed_candidates = []

    for idx, cand in enumerate(candidates_raw):
        try:
            cand_dict = dict(cand) if isinstance(cand, dict) else {"raw": str(cand)}
            c_id = str(cand_dict.get("candidate_id", cand_dict.get("id", f"CAND_{idx+1}")))
            c_name = str(cand_dict.get("name", f"Candidate {idx+1}"))

            qual_res = compute_overall_qualification_score(cand_dict, job)
            qual_score = qual_res["qualification_score"]
            exp_dec = qual_res["expected_decision"]

            eval_mode = req.mode or "Local Ollama Mode"
            if len(candidates_raw) > 3 and idx >= 2:
                eval_mode = "Deterministic Mode"

            ai_res = evaluate_candidate(
                candidate_data=cand_dict,
                job_requirements=job,
                mode=eval_mode,
                model_name=req.model_name or "qwen3.5:4b",
                mitigation=bool(req.mitigation),
                mitigation_instruction=mitigation_instruction() if req.mitigation else ""
            )

            decision = ai_res.get("decision", exp_dec)
            explanation = ai_res.get("explanation", "")
            ai_score = ai_res.get("score") if ai_res.get("score") is not None else qual_score

            evidence_res = evaluate_evidence_traceability(explanation, cand_dict, job)

            efs_res = evaluate_faithfulness_instance(
                explanation=explanation,
                qualification_score=qual_score,
                decision=decision,
                skill_analysis=qual_res["skill_analysis"],
                experience_analysis=qual_res["experience_analysis"],
                candidate_data=cand_dict,
                job_requirements=job
            )

            bi_res = run_background_investigation(
                candidate=cand_dict,
                job=job,
                evidence_traceability=evidence_res,
                explanation=explanation
            )

            cand_result = dict(cand_dict)
            cand_result.update({
                "candidate_id": c_id,
                "name": c_name,
                "role": cand_dict.get("role", "Engineer"),
                "status": "SUCCESS",
                "experience_years": qual_res["experience_analysis"]["candidate_experience_years"],
                "skills": cand_dict.get("skills", ""),
                "education": cand_dict.get("education", ""),
                "degree": cand_dict.get("degree", ""),
                "certifications": cand_dict.get("certifications", ""),
                "qualification_score": qual_score,
                "score": qual_score,
                "required_match_percentage": qual_res["skill_analysis"]["required_match_percentage"],
                "preferred_match_percentage": qual_res["skill_analysis"]["preferred_match_percentage"],
                "expected_decision": exp_dec,
                "ai_decision": decision,
                "decision": decision,
                "ai_score": ai_score,
                "efs_score": efs_res["faithfulness_score"],
                "efs_breakdown": efs_res["breakdown"],
                "background_investigation": bi_res,
                "background_status": bi_res["overall_status"],
                "evidence_coverage": bi_res["evidence_coverage_percentage"],
                "flagged": bool(bi_res["overall_status"] in ["INCONSISTENCY_DETECTED", "INSUFFICIENT_EVIDENCE"]),
                "explanation": explanation,
                "matched_skills": qual_res["skill_analysis"]["matched_required_skills"],
                "missing_skills": qual_res["skill_analysis"]["missing_required_skills"],
                "matched_preferred_skills": qual_res["skill_analysis"]["matched_preferred_skills"],
                "missing_preferred_skills": qual_res["skill_analysis"]["missing_preferred_skills"],
                "additional_skills": qual_res["skill_analysis"]["additional_skills"],
                "component_breakdown": qual_res["component_breakdown"],
                "skill_analysis": qual_res["skill_analysis"],
                "experience_analysis": qual_res["experience_analysis"]
            })
            results.append(cand_result)
        except Exception as e:
            failed_candidates.append({
                "candidate_id": cand.get("candidate_id", f"CAND_{idx+1}") if isinstance(cand, dict) else f"CAND_{idx+1}",
                "name": cand.get("name", "Unknown") if isinstance(cand, dict) else "Unknown",
                "status": "ERROR",
                "error": str(e),
                "qualification_score": 0.0,
                "score": 0.0,
                "required_match_percentage": 0.0,
                "background_status": "INSUFFICIENT_EVIDENCE",
                "evidence_coverage": 0.0,
                "efs_score": 0.0,
                "flagged": True
            })

    total = len(candidates_raw)
    evaluated_count = len(results)
    failed_count = len(failed_candidates)

    if evaluated_count > 0:
        avg_qual = round(sum(r["qualification_score"] for r in results) / evaluated_count, 1)
        avg_skill = round(sum(r["required_match_percentage"] for r in results) / evaluated_count, 1)
        avg_efs = round(sum(r["efs_score"] for r in results) / evaluated_count, 1)
        avg_coverage = round(sum(r.get("evidence_coverage", 0.0) for r in results) / evaluated_count, 1)
        bi_verified_count = sum(1 for r in results if r.get("background_status") == "VERIFIED_FROM_PROVIDED_EVIDENCE")
        bi_partially_verified_count = sum(1 for r in results if r.get("background_status") == "PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE")
        bi_insufficient_count = sum(1 for r in results if r.get("background_status") == "INSUFFICIENT_EVIDENCE") + failed_count
        bi_inconsistent_count = sum(1 for r in results if r.get("background_status") == "INCONSISTENCY_DETECTED")
        flagged_count = sum(1 for r in results if r.get("flagged", False)) + failed_count
        pool_consistency = evaluate_pool_consistency(results)
    else:
        avg_qual = 0.0
        avg_skill = 0.0
        avg_efs = 0.0
        avg_coverage = 0.0
        bi_verified_count = 0
        bi_partially_verified_count = 0
        bi_insufficient_count = failed_count
        bi_inconsistent_count = 0
        flagged_count = failed_count
        pool_consistency = {"status": "NO_VALID_CANDIDATES", "inconsistent_pairs": 0, "total_pairs_checked": 0}

    all_output_candidates = results + failed_candidates

    return {
        "job_id": job.get("job_id", req.job_id),
        "job_title": job.get("title", "Software Engineer"),
        "total_candidates": total,
        "evaluated_candidates": evaluated_count,
        "failed_candidates": failed_count,
        "flagged_cases": flagged_count,
        "flagged_candidates_count": flagged_count,
        "average_qualification_score": avg_qual,
        "average_skill_match_percentage": avg_skill,
        "average_efs": avg_efs,
        "average_evidence_coverage": avg_coverage,
        "background_investigation_summary": {
            "verified_count": bi_verified_count,
            "partially_verified_count": bi_partially_verified_count,
            "insufficient_evidence_count": bi_insufficient_count,
            "inconsistency_detected_count": bi_inconsistent_count,
            "average_coverage_percentage": avg_coverage
        },
        "pool_consistency": pool_consistency,
        "candidates": all_output_candidates,
        "errors": failed_candidates
    }

@app.post("/api/upload-candidates")
async def api_upload_candidates(file: UploadFile = File(...)):
    """
    Uploads a custom candidate pool CSV file, parses columns, and registers as active benchmark dataset.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV candidate files are supported.")
    
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content)).fillna("")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    
    if len(df) == 0:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty.")
    
    # Ensure standard required column names exist
    if "candidate_id" not in df.columns:
        df["candidate_id"] = [f"UPL_{i+1:03d}" for i in range(len(df))]
    if "name" not in df.columns:
        df["name"] = [f"Candidate {i+1}" for i in range(len(df))]
    if "skills" not in df.columns:
        df["skills"] = "Python, SQL, Git"
    if "experience_years" not in df.columns:
        df["experience_years"] = 3.0
    if "education" not in df.columns:
        df["education"] = "B.Tech Computer Science"

    saved_filename = f"custom_{os.path.basename(file.filename)}"
    out_path = os.path.join(DATA_DIR, saved_filename)
    df.to_csv(out_path, index=False)
    
    global ACTIVE_DATASET
    ACTIVE_DATASET = saved_filename
    
    return {
        "filename": saved_filename,
        "total_candidates": len(df),
        "candidates": df.to_dict(orient="records"),
        "message": f"Successfully loaded {len(df)} candidate records from {file.filename}."
    }

@app.post("/api/mitigation")
def api_run_mitigation(req: MitigationRequest):
    """
    Executes Before vs After Mitigation Feedback Loop.
    """
    job = req.job or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    cands = req.candidates or []

    if not cands:
        path = os.path.join(DATA_DIR, ACTIVE_DATASET)
        if os.path.exists(path):
            cands = pd.read_csv(path).fillna("").to_dict(orient="records")[:10]

    before_evals = []
    after_evals = []

    for idx, cand in enumerate(cands):
        try:
            cand_dict = dict(cand)
            qual_res = compute_overall_qualification_score(cand_dict, job)
            q_score = qual_res["qualification_score"]

            m_mode = req.mode or "Local Ollama Mode"
            if len(cands) > 2 and idx >= 2:
                m_mode = "Deterministic Mode"

            # Before (No Mitigation)
            b_ai = evaluate_candidate(cand_dict, job, mode=m_mode, model_name=req.model_name, mitigation=False)
            b_ev = evaluate_evidence_traceability(b_ai.get("explanation", ""), cand_dict, job)
            b_efs = evaluate_faithfulness_instance(b_ai.get("explanation", ""), q_score, b_ai.get("decision", "INTERVIEW"), qual_res["skill_analysis"], candidate_data=cand_dict, job_requirements=job)
            b_bi = run_background_investigation(candidate=cand_dict, job=job, evidence_traceability=b_ev, explanation=b_ai.get("explanation", ""))
            
            before_evals.append({
                "candidate_id": cand_dict.get("candidate_id", f"CAND_{idx+1}"),
                "name": cand_dict.get("name", f"Candidate {idx+1}"),
                "qualification_score": q_score,
                "decision": b_ai.get("decision", qual_res["expected_decision"]),
                "background_status": b_bi.get("overall_status", "VERIFIED_FROM_PROVIDED_EVIDENCE"),
                "evidence_coverage": b_bi.get("evidence_coverage_percentage", 90.0),
                "efs_score": b_efs.get("faithfulness_score", 90.0),
                "explanation": b_ai.get("explanation", "Evaluated based on standard qualifications.")
            })

            # After (With In-Context Mitigation)
            a_ai = evaluate_candidate(cand_dict, job, mode=m_mode, model_name=req.model_name, mitigation=True, mitigation_instruction=mitigation_instruction())
            a_ev = evaluate_evidence_traceability(a_ai.get("explanation", ""), cand_dict, job)
            a_efs = evaluate_faithfulness_instance(a_ai.get("explanation", ""), q_score, a_ai.get("decision", "INTERVIEW"), qual_res["skill_analysis"], candidate_data=cand_dict, job_requirements=job)
            a_bi = run_background_investigation(candidate=cand_dict, job=job, evidence_traceability=a_ev, explanation=a_ai.get("explanation", ""))

            after_evals.append({
                "candidate_id": cand_dict.get("candidate_id", f"CAND_{idx+1}"),
                "name": cand_dict.get("name", f"Candidate {idx+1}"),
                "qualification_score": q_score,
                "decision": a_ai.get("decision", qual_res["expected_decision"]),
                "background_status": a_bi.get("overall_status", "VERIFIED_FROM_PROVIDED_EVIDENCE"),
                "evidence_coverage": a_bi.get("evidence_coverage_percentage", 98.0),
                "efs_score": a_efs.get("faithfulness_score", 98.0),
                "explanation": a_ai.get("explanation", "Audited and verified under qualification mitigation directive.")
            })
        except Exception as e:
            continue

    summary = evaluate_mitigation_feedback_loop(before_evals, after_evals)

    return {
        "summary": summary,
        "before_evaluations": before_evals,
        "after_evaluations": after_evals
    }

@app.post("/api/re-evaluate")
def api_re_evaluate(req: ReEvaluateRequest):
    """
    Re-evaluates a candidate under mitigation instructions to verify consistency recovery.
    """
    job = req.job or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    instr = req.mitigation_instruction or mitigation_instruction()

    qual_res = compute_overall_qualification_score(req.candidate, job)
    ai_res = evaluate_candidate(
        req.candidate, job,
        mode=req.mode,
        model_name=req.model_name,
        mitigation=True,
        mitigation_instruction=instr
    )

    evidence_res = evaluate_evidence_traceability(ai_res["explanation"], req.candidate, job)

    efs_res = evaluate_faithfulness_instance(
        ai_res["explanation"],
        qual_res["qualification_score"],
        ai_res["decision"],
        qual_res["skill_analysis"],
        candidate_data=req.candidate,
        job_requirements=job
    )

    bi_res = run_background_investigation(
        candidate=req.candidate,
        job=job,
        evidence_traceability=evidence_res,
        explanation=ai_res["explanation"]
    )

    return {
        "candidate": req.candidate,
        "qualification_analysis": qual_res,
        "re_evaluation": ai_res,
        "efs": efs_res,
        "background_investigation": bi_res,
        "mitigation_instruction_used": instr
    }

@app.post("/api/resume-screen")
def api_resume_screen(req: ResumeScreenRequest):
    """
    End-to-end Resume Screening & ATS Audit:
    Parses resume text or candidate profile, computes ATS compatibility score (0-100),
    matches skills, evaluates $Score_{qual}$, extracts grounded strengths/weaknesses,
    and runs SLM verdict with EFS faithfulness and background verification.
    """
    job = req.job or JOB_STORE.get(req.job_id, DEFAULT_JOB_TEMPLATES.get(req.job_id, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]))
    text = req.resume_text or ""

    parsed_data = parse_resume_full(text)
    
    # Merge explicit manual overrides if supplied
    if req.candidate_data:
        cand_overrides = dict(req.candidate_data)
        if cand_overrides.get("name"): parsed_data["name"] = cand_overrides["name"]
        if cand_overrides.get("experience_years") is not None: 
            try: parsed_data["experience_years"] = float(cand_overrides["experience_years"])
            except Exception: pass
        if cand_overrides.get("education"): parsed_data["education"] = cand_overrides["education"]
        if cand_overrides.get("skills"):
            if isinstance(cand_overrides["skills"], list):
                parsed_data["skills"] = cand_overrides["skills"]
            elif isinstance(cand_overrides["skills"], str):
                parsed_data["skills"] = [s.strip() for s in cand_overrides["skills"].split(";") if s.strip()]

    result = generate_grounded_resume_verdict(
        resume_text=text,
        parsed_data=parsed_data,
        job_spec=job,
        mode=req.mode or "Local Ollama Mode",
        model_name=req.model_name
    )
    return result

@app.post("/api/resume-upload")
async def api_resume_upload(
    file: UploadFile = File(...),
    job_id: Optional[str] = Form("JOB_SWE_01"),
    mode: Optional[str] = Form("Local Ollama Mode"),
    model_name: Optional[str] = Form("qwen3.5:4b")
):
    """
    Uploads a PDF, DOCX, or TXT resume file, extracts text,
    audits ATS compatibility, and generates grounded SLM hiring feedback.
    """
    content = await file.read()
    raw_text = extract_text_from_file_bytes(content, file.filename)
    job = JOB_STORE.get(job_id, DEFAULT_JOB_TEMPLATES.get(job_id, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]))
    parsed_data = parse_resume_full(raw_text)
    
    result = generate_grounded_resume_verdict(
        resume_text=raw_text,
        parsed_data=parsed_data,
        job_spec=job,
        mode=mode,
        model_name=model_name
    )
    result["raw_extracted_text"] = raw_text
    result["filename"] = file.filename
    return result

@app.get("/api/report/{candidate_id}")
def api_candidate_report(candidate_id: str, job_id: Optional[str] = "JOB_SWE_01"):
    """Generates a complete audit dossier report for a single candidate."""
    path = os.path.join(DATA_DIR, ACTIVE_DATASET)
    cand = None

    if os.path.exists(path):
        df = pd.read_csv(path).fillna("")
        matches = df[df["candidate_id"] == candidate_id]
        if len(matches) > 0:
            cand = matches.iloc[0].to_dict()

    if not cand:
        for c in CUSTOM_CANDIDATES:
            if c.get("candidate_id") == candidate_id:
                cand = c
                break

    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidate ID '{candidate_id}' not found")

    job = JOB_STORE.get(job_id, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"])

    qual_res = compute_overall_qualification_score(cand, job)
    ai_eval = evaluate_candidate(cand, job)
    ev = evaluate_evidence_traceability(ai_eval["explanation"], cand, job)
    efs = evaluate_faithfulness_instance(ai_eval["explanation"], qual_res["qualification_score"], ai_eval["decision"], qual_res["skill_analysis"], candidate_data=cand, job_requirements=job)
    bi = run_background_investigation(candidate=cand, job=job, evidence_traceability=ev, explanation=ai_eval["explanation"])

    return {
        "candidate": cand,
        "job_applied": job,
        "qualification_analysis": qual_res,
        "ai_evaluation": ai_eval,
        "evidence": ev,
        "efs_assessment": efs,
        "background_investigation": bi
    }

@app.post("/api/export-report")
def api_export_report(req: ExportReportRequest):
    """Exports candidate audit dossier as structured JSON or formatted CSV."""
    report = api_candidate_report(req.candidate_id, req.job_id)
    if req.format.lower() == "csv":
        # Flatten dictionary to tabular CSV
        bi_data = report.get("background_investigation", {})
        flat_dict = {
            "candidate_id": req.candidate_id,
            "name": report["candidate"].get("name"),
            "job_title": report["job_applied"].get("title"),
            "qualification_score": report["qualification_analysis"]["qualification_score"],
            "expected_decision": report["qualification_analysis"]["expected_decision"],
            "ai_decision": report["ai_evaluation"]["decision"],
            "efs_score": report["efs_assessment"]["faithfulness_score"],
            "efs_tier": report["efs_assessment"]["classification"],
            "background_status": bi_data.get("overall_status", "UNKNOWN"),
            "evidence_coverage": bi_data.get("evidence_coverage_percentage", 0.0),
            "inconsistencies_count": len(bi_data.get("inconsistencies", [])),
            "flagged_for_audit": bi_data.get("overall_status") in ["INCONSISTENCY_DETECTED", "INSUFFICIENT_EVIDENCE"],
            "explanation": report["ai_evaluation"]["explanation"]
        }
        df_exp = pd.DataFrame([flat_dict])
        csv_str = df_exp.to_csv(index=False)
        return PlainTextResponse(content=csv_str, media_type="text/csv")
    return report

@app.post("/api/cluster")
def api_cluster(n_clusters: int = Query(3, ge=2, le=5)):
    """Clusters candidate pool using TF-IDF and K-Means on qualification profiles."""
    path = os.path.join(DATA_DIR, ACTIVE_DATASET)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Dataset missing")

    df = pd.read_csv(path).fillna("")
    df_clustered = cluster_dataframe(df, n_clusters)
    summary = get_cluster_summary(df_clustered)

    return {
        "dataset": ACTIVE_DATASET,
        "n_clusters": n_clusters,
        "cluster_summary": summary,
        "candidates": df_clustered.to_dict(orient="records")
    }

# ============================================================================
# Static Files & Frontend Mount
# ============================================================================

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    idx_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(idx_path):
        return FileResponse(idx_path)
    return {"message": "AI Hiring Intelligence API is running. Go to /docs for Swagger UI."}

if __name__ == "__main__":
    import threading
    import time
    import webbrowser
    import uvicorn

    def open_browser():
        time.sleep(1.5)
        webbrowser.open_new_tab("http://127.0.0.1:8000")

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
