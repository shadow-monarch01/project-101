"""
AI Hiring Intelligence - LLM Client & Qualification Inference Engine
Integrates Ollama (Qwen 3.5 4B), cloud APIs, and a deterministic qualification evaluation simulator.
Handles structured JSON parsing and <think> reasoning token removal.
"""

import os
import re
import json
import requests
from typing import Dict, Any, Optional
from modules.qualifications import compute_overall_qualification_score, DEFAULT_JOB_TEMPLATES

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

def check_ollama_connectivity(url: str = DEFAULT_OLLAMA_URL) -> Dict[str, Any]:
    base_url = (url or DEFAULT_OLLAMA_URL).rstrip("/")
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            return {
                "connected": True,
                "url": base_url,
                "models": models,
                "total_models": len(models),
                "default_recommended": "qwen3.5:4b" if "qwen3.5:4b" in models else (models[0] if models else "qwen3.5:4b")
            }
        return {"connected": False, "url": base_url, "models": [], "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"connected": False, "url": base_url, "models": [], "error": "Ollama service not detected."}

def clean_think_tags(text: str) -> str:
    cleaned = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE)
    return cleaned.strip()

def parse_llm_output(raw_output: str, decision_type: str = "multiclass") -> Dict[str, Any]:
    cleaned = clean_think_tags(raw_output)

    json_match = re.search(r'\{[\s\S]*\}', cleaned)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            dec = str(data.get("decision", data.get("recommendation", "INTERVIEW"))).strip().upper()
            expl = str(data.get("explanation", data.get("reasoning", cleaned)))
            score = data.get("score", data.get("qualification_score", None))
            strengths = data.get("strengths", [])
            gaps = data.get("skill_gaps", data.get("gaps", []))

            return {
                "decision": dec,
                "recommendation": dec,
                "explanation": expl,
                "score": float(score) if score is not None else None,
                "strengths": strengths if isinstance(strengths, list) else [str(strengths)],
                "skill_gaps": gaps if isinstance(gaps, list) else [str(gaps)],
                "confidence": float(data.get("confidence", 0.90)),
                "raw_response": cleaned
            }
        except Exception:
            pass

    dec_upper = cleaned.upper()
    if "STRONG HIRE" in dec_upper or "STRONG_HIRE" in dec_upper:
        dec = "STRONG_HIRE"
    elif "HIRE" in dec_upper or "SELECT" in dec_upper:
        dec = "HIRE"
    elif "REJECT" in dec_upper or "NOT RECOMMENDED" in dec_upper:
        dec = "REJECT"
    else:
        dec = "INTERVIEW"

    return {
        "decision": dec,
        "recommendation": dec,
        "explanation": cleaned[:350] if cleaned else "Candidate profile assessed against role qualifications.",
        "score": None,
        "strengths": [],
        "skill_gaps": [],
        "confidence": 0.85,
        "raw_response": cleaned
    }

def _demo_qualification_inference(
    candidate: Dict[str, Any],
    job: Dict[str, Any],
    decision_type: str = "multiclass",
    mitigation: bool = False
) -> Dict[str, Any]:
    res = compute_overall_qualification_score(candidate, job)
    qual_score = res["qualification_score"]
    exp_dec = res["expected_decision"]
    matched = res["skill_analysis"]["matched_required_skills"]
    missing = res["skill_analysis"]["missing_required_skills"]
    exp_years = res["experience_analysis"]["candidate_experience_years"]

    if mitigation:
        decision = exp_dec
        score = qual_score
        expl = (
            f"Candidate is recommended for {decision} with an objective qualification score of {qual_score}/100. "
            f"Possesses {len(matched)} verified required skills ({', '.join(matched[:3])}) and {exp_years} years relevant experience."
        )
    else:
        decision = exp_dec
        score = qual_score
        if decision in ["STRONG_HIRE", "HIRE"]:
            expl = f"Strong alignment with role requirements. Demonstrated competence in {', '.join(matched[:3])} with {exp_years} years domain background."
        elif decision == "INTERVIEW":
            expl = f"Candidate meets baseline requirements ({exp_years}y experience) but shows minor gaps in {', '.join(missing[:2]) if missing else 'specialized areas'}. Recommend technical interview."
        else:
            expl = f"Profile does not meet core qualification threshold ({qual_score}/100). Lacks essential skills in {', '.join(missing[:2]) if missing else 'required stack'}."

    return {
        "decision": decision,
        "recommendation": decision,
        "score": score,
        "qualification_score": qual_score,
        "explanation": expl,
        "strengths": matched[:4],
        "skill_gaps": missing,
        "confidence": 0.92,
        "expected_decision": exp_dec
    }

def evaluate_candidate(
    candidate_data: Dict[str, Any],
    job_requirements: Optional[Dict[str, Any]] = None,
    decision_type: str = "multiclass",
    mode: str = "Demo Simulation Mode",
    model_name: str = "qwen3.5:4b",
    mitigation: bool = False,
    mitigation_instruction: str = "",
    api_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    job = job_requirements or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]

    if mode == "Demo Simulation Mode" or not mode:
        return _demo_qualification_inference(candidate_data, job, decision_type, mitigation)

    base_prompt = (
        f"You are an expert, objective AI Technical Hiring Evaluator.\n"
        f"Evaluate the candidate strictly based on job-related qualifications, skills, and experience.\n"
        f"Do NOT use any personal or irrelevant factors.\n\n"
        f"JOB REQUIREMENTS:\n"
        f"Title: {job.get('title')}\n"
        f"Required Skills: {', '.join(job.get('required_skills', []))}\n"
        f"Preferred Skills: {', '.join(job.get('preferred_skills', []))}\n"
        f"Minimum Experience: {job.get('minimum_experience', 2.0)} years\n"
        f"Education Requirement: {job.get('required_education', 'B.S. in CS')}\n\n"
        f"CANDIDATE PROFILE:\n"
        f"{json.dumps(candidate_data, default=str, indent=2)}\n\n"
        f"Return a valid JSON object with keys:\n"
        f"- 'decision': One of 'STRONG_HIRE', 'HIRE', 'INTERVIEW', 'REJECT'\n"
        f"- 'score': Numeric score from 0.0 to 100.0\n"
        f"- 'explanation': 2-sentence rationale grounded on skills and experience\n"
        f"- 'strengths': List of matched skills and strengths\n"
        f"- 'skill_gaps': List of missing or weak skills\n"
    )

    if mitigation and mitigation_instruction:
        base_prompt += f"\nCRITICAL MITIGATION DIRECTIVE: {mitigation_instruction}\n"

    if mode == "Local Ollama Mode":
        ollama_url = (api_url or DEFAULT_OLLAMA_URL).rstrip("/")
        try:
            payload = {
                "model": model_name or "qwen3.5:4b",
                "prompt": base_prompt,
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 250}
            }
            resp = requests.post(f"{ollama_url}/api/generate", json=payload, timeout=8)
            if resp.status_code == 200:
                raw_text = resp.json().get("response", "")
                if raw_text:
                    return parse_llm_output(raw_text, decision_type)
        except Exception:
            pass
        return _demo_qualification_inference(candidate_data, job, decision_type, mitigation)

    if mode == "Real LLM API Mode":
        url = api_url or "https://api.openai.com/v1/chat/completions"
        key = api_key or ""
        try:
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {
                "model": model_name or "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are an objective AI hiring assessment evaluator. Output strict JSON."},
                    {"role": "user", "content": base_prompt}
                ],
                "temperature": 0.0
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                raw_content = resp.json()["choices"][0]["message"]["content"]
                return parse_llm_output(raw_content, decision_type)
        except Exception:
            pass
        return _demo_qualification_inference(candidate_data, job, decision_type, mitigation)

    return _demo_qualification_inference(candidate_data, job, decision_type, mitigation)
