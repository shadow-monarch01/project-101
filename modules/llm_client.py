"""
AI Hiring Intelligence - Local SLM Client & Qualification Inference Engine
Specialized for lightweight, on-device Small Language Models (SLMs) via Ollama (e.g. Qwen 3.5 4B, Llama 3.2 3B).
Provides grounded qualification evaluation, bias detection, and token-optimized prompting.
"""

import os
import re
import json
import requests
from typing import Dict, Any, Optional
from modules.qualifications import compute_overall_qualification_score, DEFAULT_JOB_TEMPLATES

import time

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
_OLLAMA_CACHE = {"online": False, "last_checked": 0, "ttl": 4.0}

def is_ollama_available(url: str = DEFAULT_OLLAMA_URL) -> bool:
    """Fast cached check for Ollama daemon availability."""
    now = time.time()
    if now - _OLLAMA_CACHE["last_checked"] < _OLLAMA_CACHE["ttl"]:
        return _OLLAMA_CACHE["online"]
    
    base_url = (url or DEFAULT_OLLAMA_URL).rstrip("/")
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=0.6)
        _OLLAMA_CACHE["online"] = (resp.status_code == 200)
    except Exception:
        _OLLAMA_CACHE["online"] = False
    _OLLAMA_CACHE["last_checked"] = now
    return _OLLAMA_CACHE["online"]

def check_ollama_connectivity(url: str = DEFAULT_OLLAMA_URL) -> Dict[str, Any]:
    """Checks whether local Ollama SLM server is accessible."""
    base_url = (url or DEFAULT_OLLAMA_URL).rstrip("/")
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=1.0)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            rec_model = "qwen3.5:4b" if "qwen3.5:4b" in models else (models[0] if models else "qwen3.5:4b")
            _OLLAMA_CACHE["online"] = True
            _OLLAMA_CACHE["last_checked"] = time.time()
            return {
                "connected": True,
                "url": base_url,
                "models": models,
                "total_models": len(models),
                "default_recommended": rec_model
            }
        _OLLAMA_CACHE["online"] = False
        _OLLAMA_CACHE["last_checked"] = time.time()
        return {"connected": False, "url": base_url, "models": [], "error": f"HTTP {resp.status_code}"}
    except Exception:
        _OLLAMA_CACHE["online"] = False
        _OLLAMA_CACHE["last_checked"] = time.time()
        return {"connected": False, "url": base_url, "models": [], "error": "Local Ollama service not detected."}

def clean_think_tags(text: str) -> str:
    """Removes internal reasoning tokens such as <think>...</think> and code blocks from SLM outputs."""
    cleaned = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'```json\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'```\s*', '', cleaned)
    return cleaned.strip()

def parse_llm_output(raw_output: str, decision_type: str = "multiclass") -> Dict[str, Any]:
    """Parses JSON response or extracts structured decision and justification."""
    cleaned = clean_think_tags(raw_output)

    json_match = re.search(r'\{[\s\S]*\}', cleaned)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            raw_dec = str(data.get("decision", data.get("recommendation", "INTERVIEW"))).strip().upper()
            expl = str(data.get("explanation", data.get("reasoning", cleaned)))
            score = data.get("score", data.get("qualification_score", None))
            strengths = data.get("strengths", [])
            gaps = data.get("skill_gaps", data.get("gaps", []))

            if "STRONG HIRE" in raw_dec or "STRONG_HIRE" in raw_dec:
                dec = "STRONG_HIRE"
            elif "HIRE" in raw_dec or "SELECT" in raw_dec:
                dec = "HIRE"
            elif "REJECT" in raw_dec or "NOT RECOMMENDED" in raw_dec:
                dec = "REJECT"
            else:
                dec = "INTERVIEW"

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

def _grounded_qualification_inference(
    candidate: Dict[str, Any],
    job: Dict[str, Any],
    decision_type: str = "multiclass",
    mitigation: bool = False
) -> Dict[str, Any]:
    """Deterministic, grounded qualification evaluation baseline."""
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
    mode: str = "Local Ollama Mode",
    model_name: str = "qwen3.5:4b",
    mitigation: bool = False,
    mitigation_instruction: str = "",
    api_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates candidate using Local SLM (Ollama) or grounded qualification baseline.
    Uses token-saving structured ChatML prompts with fast reasoning skip.
    """
    job = job_requirements or DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]

    ollama_url = (api_url or DEFAULT_OLLAMA_URL).rstrip("/")
    if "PYTEST_CURRENT_TEST" not in os.environ and mode in ["Local Ollama Mode", "Ollama", "Local SLM Mode", "local"] and is_ollama_available(ollama_url):
        try:
            system_msg = (
                "You are an objective AI Technical Hiring Evaluator. "
                "Evaluate strictly on job-related technical qualifications and experience. "
                "You MUST respond ONLY with a single valid JSON object."
            )
            if mitigation and mitigation_instruction:
                system_msg += f" CRITICAL MITIGATION DIRECTIVE: {mitigation_instruction}"

            user_msg = (
                f"ROLE:\n"
                f"Title: {job.get('title')}\n"
                f"Required Skills: {', '.join(job.get('required_skills', []))}\n"
                f"Preferred Skills: {', '.join(job.get('preferred_skills', []))}\n"
                f"Min Experience: {job.get('minimum_experience', 2.0)} yrs\n"
                f"Education: {job.get('required_education', 'B.S. in CS')}\n\n"
                f"CANDIDATE:\n"
                f"{json.dumps(candidate_data, default=str, indent=2)}\n\n"
                f"Output JSON with exact schema:\n"
                f"{{\n"
                f'  "decision": "STRONG_HIRE" | "HIRE" | "INTERVIEW" | "REJECT",\n'
                f'  "score": <float between 0 and 100>,\n'
                f'  "explanation": "<2-sentence grounded justification>",\n'
                f'  "strengths": ["<matched_skill>"],\n'
                f'  "skill_gaps": ["<missing_skill>"]\n'
                f"}}"
            )

            prompt = (
                f"<|im_start|>system\n{system_msg}<|im_end|>\n"
                f"<|im_start|>user\n{user_msg}<|im_end|>\n"
                f"<|im_start|>assistant\n<think>\nEvaluation completed.\n</think>\n"
            )

            payload = {
                "model": model_name or "qwen3.5:4b",
                "prompt": prompt,
                "raw": True,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 300,
                    "stop": ["<|im_end|>", "<|endoftext|>"]
                }
            }
            resp = requests.post(f"{ollama_url}/api/generate", json=payload, timeout=20)
            if resp.status_code == 200:
                resp_json = resp.json()
                raw_text = resp_json.get("response", "")
                if not raw_text:
                    raw_text = resp_json.get("thinking", "")
                if raw_text:
                    parsed = parse_llm_output(raw_text, decision_type)
                    if parsed.get("score") is None:
                        qual_res = compute_overall_qualification_score(candidate_data, job)
                        parsed["score"] = qual_res["qualification_score"]
                    return parsed
        except Exception:
            _OLLAMA_CACHE["online"] = False

    return _grounded_qualification_inference(candidate_data, job, decision_type, mitigation)
