"""
AI Hiring Intelligence - FastAPI REST API Gateway
Exposes qualification-based candidate assessment, skill gap analysis,
Explanation Faithfulness Scoring (EFS), Bias/Behavioral Gap Index (BGI),
qualification counterfactual testing, mitigation feedback loops, and semantic clustering.
"""

import os
import glob
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from modules.qualifications import (
    DEFAULT_JOB_TEMPLATES,
    DEFAULT_SCORING_WEIGHTS,
    match_skills,
    compute_overall_qualification_score,
    parse_skills_list
)
from modules.bgi import compute_bgi, check_decision_consistency
from modules.faithfulness import evaluate_faithfulness_instance
from modules.variations import make_qualification_variation, get_available_qualification_concepts
from modules.llm_client import evaluate_candidate, check_ollama_connectivity
from modules.clustering import cluster_dataframe, get_cluster_summary
from modules.mitigation import mitigation_instruction, evaluate_mitigation_feedback_loop
from modules.statistics import mcnemar_test, multiclass_chi_square, paired_regression_test

app = FastAPI(
    title="AI Hiring Intelligence & Qualification Auditing API",
    description="REST API for qualification-based hiring assessment, EFS faithfulness scoring, BGI behavioral gap auditing, and debiasing mitigation.",
    version="2.0.0"
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
    candidate_id: Optional[str] = "CAND_TEST_01"
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
    interview_score: Optional[float] = 85.0
    previous_salary: Optional[int] = 100000

class EvaluateRequest(BaseModel):
    candidate: Dict[str, Any]
    job: Optional[Dict[str, Any]] = None
    decision_type: Optional[str] = "multiclass"
    mode: Optional[str] = "Demo Simulation Mode"
    model_name: Optional[str] = "qwen3.5:4b"
    mitigation: Optional[bool] = False
    mitigation_instruction: Optional[str] = ""

class SkillAnalysisRequest(BaseModel):
    candidate_skills: Union[List[str], str]
    required_skills: List[str]
    preferred_skills: Optional[List[str]] = None

class QualScoreRequest(BaseModel):
    candidate: Dict[str, Any]
    job: Optional[Dict[str, Any]] = None
    weights: Optional[Dict[str, float]] = None

class BGIRequest(BaseModel):
    qualification_score: float
    expected_decision: str
    ai_decision: str
    ai_score: Optional[float] = None
    efs_score: Optional[float] = 90.0
    required_skill_match: Optional[float] = 100.0

class EFSRequest(BaseModel):
    explanation: str
    qualification_score: float
    decision: str
    skill_analysis: Optional[Dict[str, Any]] = None
    experience_analysis: Optional[Dict[str, Any]] = None

class CounterfactualRequest(BaseModel):
    candidate: Dict[str, Any]
    concept: str = "skills"
    target_value: Any = "Remove Core Skill"
    job: Optional[Dict[str, Any]] = None
    mode: Optional[str] = "Demo Simulation Mode"
    model_name: Optional[str] = "qwen3.5:4b"

class MitigationRequest(BaseModel):
    candidates: List[Dict[str, Any]]
    job: Optional[Dict[str, Any]] = None
    mode: Optional[str] = "Demo Simulation Mode"
    model_name: Optional[str] = "qwen3.5:4b"

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/health")
def api_health():
    """System health check and loaded modules summary."""
    return {
        "status": "healthy",
        "system": "AI Hiring Intelligence & Qualification Auditing API",
        "version": "2.0.0",
        "active_dataset": ACTIVE_DATASET,
        "ollama": check_ollama_connectivity()
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
        raise HTTPException(status_code=404, detail="Dataset not found")
    ACTIVE_DATASET = filename
    return {"message": f"Active dataset set to {filename}", "active_dataset": filename}

@app.get("/api/concept_options")
def get_concept_options(dataset_name: Optional[str] = None, concept: str = "gender"):
    filename = dataset_name or os.path.basename(session_cache["active_dataset"])
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        filepath = os.path.join(DATA_DIR, "high_bias_hiring_dataset.csv")
    df = pd.read_csv(filepath)
    
    col = resolve_column_for_concept(df, concept)
    values = get_available_values(df, col) if col else []
    pair = default_pair(df, concept)
    
    return {
        "concept": concept,
        "resolved_column": col,
        "available_values": values,
        "default_pair": {"val_a": pair[1] if pair else (values[0] if len(values)>0 else None), "val_b": pair[2] if pair else (values[1] if len(values)>1 else None)} if (pair or len(values)>=2) else None
    }

@app.get("/api/candidates")
def api_get_candidates(
    search: Optional[str] = None,
    job_id: Optional[str] = "JOB_SWE_01",
    page: int = 1,
    limit: int = 20
):
    """
    Returns candidate profiles from active dataset with precomputed qualification scores and skill match %.
    """
    path = os.path.join(DATA_DIR, ACTIVE_DATASET)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Dataset file missing")

    df = pd.read_csv(path).fillna("")
    if search:
        s = search.lower()
        df = df[df.apply(lambda r: s in str(r.to_dict()).lower(), axis=1)]

    job = JOB_STORE.get(job_id, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"])

    records = []
    for _, row in df.iterrows():
        cand = row.to_dict()
        q_res = compute_overall_qualification_score(cand, job)
        cand["qualification_score"] = q_res["qualification_score"]
        cand["expected_decision"] = q_res["expected_decision"]
        cand["required_match_percentage"] = q_res["skill_analysis"]["required_match_percentage"]
        cand["matched_skills"] = q_res["skill_analysis"]["matched_required_skills"]
        cand["missing_skills"] = q_res["skill_analysis"]["missing_required_skills"]
        records.append(cand)

    total = len(records)
    start = (page - 1) * limit
    paginated = records[start : start + limit]

    return {
        "candidates": paginated,
        "total_count": total,
        "page": page,
        "limit": limit,
        "job_applied": job.get("title", "Software Engineer")
    }

@app.post("/api/skill-analysis")
def api_skill_analysis(req: SkillAnalysisRequest):
    """Evaluates matched, missing, and additional skills with skill gap metrics."""
    c_skills = parse_skills_list(req.candidate_skills)
    result = match_skills(c_skills, req.required_skills, req.preferred_skills)
    return result

@app.post("/api/qualification-score")
def api_qualification_score(req: QualScoreRequest):
    """Computes a multi-component qualification score breakdown."""
    job = req.job or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    result = compute_overall_qualification_score(req.candidate, job, req.weights)
    return result

@app.post("/api/evaluate")
def api_evaluate(req: EvaluateRequest):
    """
    Evaluates candidate against job requirements:
    Generates AI Recommendation, Explanation, Qual Score, EFS, and BGI.
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

    # 3. Explanation Faithfulness Score (EFS)
    efs_res = evaluate_faithfulness_instance(
        explanation=explanation,
        qualification_score=qual_score,
        decision=decision,
        skill_analysis=skill_analysis,
        experience_analysis=exp_analysis,
        candidate_data=req.candidate,
        job_requirements=job
    )

    # 4. Bias/Behavioral Gap Index (BGI)
    bgi_res = compute_bgi(
        qualification_score=qual_score,
        expected_decision=exp_decision,
        ai_decision=decision,
        ai_score=ai_score,
        efs_score=efs_res["faithfulness_score"],
        required_skill_match=skill_analysis["required_match_percentage"],
        experience_match=exp_analysis["experience_match_percentage"]
    )

    return {
        "candidate_id": req.candidate.get("candidate_id", "CAND_01"),
        "candidate_name": req.candidate.get("name", "Candidate"),
        "job_title": job.get("title", "Software Engineer"),
        "qualification_score": qual_score,
        "expected_decision": exp_decision,
        "decision": decision,
        "recommendation": decision,
        "ai_score": ai_score,
        "explanation": explanation,
        "confidence": ai_eval.get("confidence", 0.90),
        "strengths": ai_eval.get("strengths", skill_analysis["matched_required_skills"]),
        "skill_gaps": ai_eval.get("skill_gaps", skill_analysis["missing_required_skills"]),
        "efs": efs_res,
        "bgi": bgi_res,
        "skill_analysis": skill_analysis,
        "experience_analysis": exp_analysis,
        "mitigation_applied": bool(req.mitigation)
    }

@app.post("/api/bgi")
def api_calculate_bgi(req: BGIRequest):
    """Calculates the Bias/Behavioral Gap Index (BGI)."""
    return compute_bgi(
        qualification_score=req.qualification_score,
        expected_decision=req.expected_decision,
        ai_decision=req.ai_decision,
        ai_score=req.ai_score,
        efs_score=req.efs_score or 90.0,
        required_skill_match=req.required_skill_match or 100.0
    )

@app.post("/api/efs")
def api_calculate_efs(req: EFSRequest):
    """Calculates the Explanation Faithfulness Score (EFS)."""
    return evaluate_faithfulness_instance(
        explanation=req.explanation,
        qualification_score=req.qualification_score,
        decision=req.decision,
        skill_analysis=req.skill_analysis,
        experience_analysis=req.experience_analysis
    )

@app.get("/api/counterfactual_concepts")
def api_cf_concepts():
    """Returns supported qualification perturbation concepts."""
    return {"concepts": get_available_qualification_concepts()}

@app.post("/api/counterfactual")
def api_counterfactual(req: CounterfactualRequest):
    """
    Executes controlled qualification counterfactual intervention.
    Evaluates original candidate vs twin and computes consistency delta.
    """
    job = req.job or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]

    # 1. Generate Twin
    twin = make_qualification_variation(req.candidate, req.concept, req.target_value, job)

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

    # 5. EFS and BGI for Twin
    twin_efs = evaluate_faithfulness_instance(
        explanation=twin_eval["explanation"],
        qualification_score=twin_qual["qualification_score"],
        decision=twin_eval["decision"],
        skill_analysis=twin_qual["skill_analysis"]
    )
    twin_bgi = compute_bgi(
        qualification_score=twin_qual["qualification_score"],
        expected_decision=twin_qual["expected_decision"],
        ai_decision=twin_eval["decision"],
        efs_score=twin_efs["faithfulness_score"]
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
            "bgi": twin_bgi
        },
        "perturbation_concept": req.concept,
        "target_value": req.target_value,
        "decision_changed": orig_eval["decision"] != twin_eval["decision"],
        "consistency_analysis": consistency
    }

@app.post("/api/batch-evaluate")
def api_batch_evaluate(
    job_id: Optional[str] = "JOB_SWE_01",
    mode: Optional[str] = "Demo Simulation Mode",
    model_name: Optional[str] = "qwen3.5:4b",
    mitigation: Optional[bool] = False
):
    """
    Audits the complete active candidate pool against selected job requirements.
    Calculates pool-wide averages for Qual Score, Skill Match, EFS, BGI, and flagged cases.
    """
    path = os.path.join(DATA_DIR, ACTIVE_DATASET)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Dataset missing")

    df = pd.read_csv(path).fillna("")
    job = JOB_STORE.get(job_id, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"])

    results = []
    for _, row in df.iterrows():
        cand = row.to_dict()
        qual_res = compute_overall_qualification_score(cand, job)
        qual_score = qual_res["qualification_score"]
        exp_dec = qual_res["expected_decision"]

        ai_res = evaluate_candidate(
            cand, job,
            mode=mode,
            model_name=model_name,
            mitigation=bool(mitigation),
            mitigation_instruction=mitigation_instruction() if mitigation else ""
        )

        efs_res = evaluate_faithfulness_instance(
            explanation=ai_res["explanation"],
            qualification_score=qual_score,
            decision=ai_res["decision"],
            skill_analysis=qual_res["skill_analysis"],
            experience_analysis=qual_res["experience_analysis"]
        )

        bgi_res = compute_bgi(
            qualification_score=qual_score,
            expected_decision=exp_dec,
            ai_decision=ai_res["decision"],
            efs_score=efs_res["faithfulness_score"]
        )

        results.append({
            "candidate_id": cand.get("candidate_id", "CAND"),
            "name": cand.get("name", "Candidate"),
            "role": cand.get("role", "Engineer"),
            "qualification_score": qual_score,
            "required_match_percentage": qual_res["skill_analysis"]["required_match_percentage"],
            "expected_decision": exp_dec,
            "ai_decision": ai_res["decision"],
            "efs_score": efs_res["faithfulness_score"],
            "bgi_score": bgi_res["bgi_score"],
            "flagged": bgi_res["flagged_for_audit"],
            "bgi_tier": bgi_res["classification"],
            "explanation": ai_res["explanation"],
            "matched_skills": qual_res["skill_analysis"]["matched_required_skills"],
            "missing_skills": qual_res["skill_analysis"]["missing_required_skills"]
        })

    total = len(results)
    avg_qual = round(sum(r["qualification_score"] for r in results) / max(1, total), 1)
    avg_skill = round(sum(r["required_match_percentage"] for r in results) / max(1, total), 1)
    avg_efs = round(sum(r["efs_score"] for r in results) / max(1, total), 1)
    avg_bgi = round(sum(r["bgi_score"] for r in results) / max(1, total), 1)
    flagged_count = sum(1 for r in results if r["flagged"])

    return {
        "job_title": job.get("title", "Software Engineer"),
        "total_candidates": total,
        "average_qualification_score": avg_qual,
        "average_skill_match_percentage": avg_skill,
        "average_efs": avg_efs,
        "average_bgi": avg_bgi,
        "flagged_candidates_count": flagged_count,
        "candidates": results
    }

@app.post("/api/mitigation")
def api_run_mitigation(req: MitigationRequest):
    """
    Executes Before vs After Mitigation Feedback Loop.
    """
    job = req.job or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    cands = req.candidates or []

    if not cands:
        # Load sample from active dataset
        path = os.path.join(DATA_DIR, ACTIVE_DATASET)
        if os.path.exists(path):
            cands = pd.read_csv(path).fillna("").to_dict(orient="records")[:10]

    before_evals = []
    after_evals = []

    for cand in cands:
        qual_res = compute_overall_qualification_score(cand, job)
        q_score = qual_res["qualification_score"]

        # Before (No Mitigation)
        b_ai = evaluate_candidate(cand, job, mode=req.mode, model_name=req.model_name, mitigation=False)
        b_efs = evaluate_faithfulness_instance(b_ai["explanation"], q_score, b_ai["decision"], qual_res["skill_analysis"])
        b_bgi = compute_bgi(q_score, qual_res["expected_decision"], b_ai["decision"], efs_score=b_efs["faithfulness_score"])
        
        before_evals.append({
            "candidate_id": cand.get("candidate_id"),
            "name": cand.get("name"),
            "qualification_score": q_score,
            "decision": b_ai["decision"],
            "bgi_score": b_bgi["bgi_score"],
            "efs_score": b_efs["faithfulness_score"],
            "explanation": b_ai["explanation"]
        })

        # After (With Mitigation)
        a_ai = evaluate_candidate(cand, job, mode=req.mode, model_name=req.model_name, mitigation=True, mitigation_instruction=mitigation_instruction())
        a_efs = evaluate_faithfulness_instance(a_ai["explanation"], q_score, a_ai["decision"], qual_res["skill_analysis"])
        a_bgi = compute_bgi(q_score, qual_res["expected_decision"], a_ai["decision"], efs_score=a_efs["faithfulness_score"])

        after_evals.append({
            "candidate_id": cand.get("candidate_id"),
            "name": cand.get("name"),
            "qualification_score": q_score,
            "decision": a_ai["decision"],
            "bgi_score": a_bgi["bgi_score"],
            "efs_score": a_efs["faithfulness_score"],
            "explanation": a_ai["explanation"]
        })

    summary = evaluate_mitigation_feedback_loop(before_evals, after_evals)

    return {
        "summary": summary,
        "before_evaluations": before_evals,
        "after_evaluations": after_evals
    }

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

@app.get("/api/report/{candidate_id}")
def api_candidate_report(candidate_id: str, job_id: Optional[str] = "JOB_SWE_01"):
    """Generates a complete audit dossier report for a single candidate."""
    path = os.path.join(DATA_DIR, ACTIVE_DATASET)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Dataset missing")

    df = pd.read_csv(path).fillna("")
    matches = df[df["candidate_id"] == candidate_id]
    if len(matches) == 0:
        raise HTTPException(status_code=404, detail="Candidate ID not found")

    cand = matches.iloc[0].to_dict()
    job = JOB_STORE.get(job_id, DEFAULT_JOB_TEMPLATES["JOB_SWE_01"])

    qual_res = compute_overall_qualification_score(cand, job)
    ai_eval = evaluate_candidate(cand, job)
    efs = evaluate_faithfulness_instance(ai_eval["explanation"], qual_res["qualification_score"], ai_eval["decision"], qual_res["skill_analysis"])
    bgi = compute_bgi(qual_res["qualification_score"], qual_res["expected_decision"], ai_eval["decision"], efs_score=efs["faithfulness_score"])

    return {
        "candidate": cand,
        "job_applied": job,
        "qualification_analysis": qual_res,
        "ai_evaluation": ai_eval,
        "efs_assessment": efs,
        "bgi_audit": bgi
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
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)

