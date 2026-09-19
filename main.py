"""
AI Hiring Intelligence System - Command-Line Interface Runner & Automated Test Harness
"""

import sys
import os
import subprocess
import pandas as pd

from modules.qualifications import (
    DEFAULT_JOB_TEMPLATES,
    compute_overall_qualification_score,
    match_skills
)
from modules.bgi import compute_bgi
from modules.faithfulness import evaluate_faithfulness_instance
from modules.variations import make_qualification_variation
from modules.llm_client import evaluate_candidate, check_ollama_connectivity
from modules.mitigation import evaluate_mitigation_feedback_loop

def run_cli_demo():
    print("=" * 70)
    print("AI HIRING INTELLIGENCE & QUALIFICATION AUDITING SYSTEM")
    print("=" * 70)

    # 1. Check Ollama
    ollama_status = check_ollama_connectivity()
    rec_model = ollama_status.get("default_recommended", "qwen3.5:4b")
    status_str = f"Online ({rec_model})" if ollama_status.get("connected") else "Simulation Mode (Offline)"
    print(f"[*] Evaluator Engine Status: {status_str}")

    # 2. Load benchmark candidate
    job = DEFAULT_JOB_TEMPLATES["JOB_SWE_01"]
    print(f"\n[1] Target Job Role: {job['title']}")
    print(f"    Required Skills: {', '.join(job['required_skills'])}")
    print(f"    Min Experience : {job['minimum_experience']} years")

    cand = {
        "candidate_id": "SWE_001",
        "name": "Priya Sharma",
        "role": "Senior Backend Engineer",
        "experience_years": 6.0,
        "skills": "Python; SQL; PostgreSQL; REST API; Git; FastAPI; Docker",
        "education": "B.Tech Computer Science",
        "certifications_count": 1,
        "interview_score": 90.0
    }
    print(f"\n[2] Candidate Profile: {cand['name']} ({cand['candidate_id']})")
    print(f"    Skills: {cand['skills']}")
    print(f"    Experience: {cand['experience_years']} years | Education: {cand['education']}")

    # 3. Qualification Assessment
    qual_res = compute_overall_qualification_score(cand, job)
    print(f"\n[3] Qualification Assessment:")
    print(f"    Overall Qualification Score: {qual_res['qualification_score']}%")
    print(f"    Required Skill Match: {qual_res['skill_analysis']['required_match_percentage']}%")
    print(f"    Matched Skills: {', '.join(qual_res['skill_analysis']['matched_required_skills'])}")
    print(f"    Expected Decision Tier: {qual_res['expected_decision']}")

    # 4. AI Evaluation
    ai_eval = evaluate_candidate(cand, job, mode="Demo Simulation Mode")
    print(f"\n[4] AI Evaluator Output:")
    print(f"    Recommendation: {ai_eval['decision']}")
    print(f"    Explanation: {ai_eval['explanation']}")

    # 5. EFS & BGI
    efs = evaluate_faithfulness_instance(ai_eval['explanation'], qual_res['qualification_score'], ai_eval['decision'], qual_res['skill_analysis'])
    bgi = compute_bgi(qual_res['qualification_score'], qual_res['expected_decision'], ai_eval['decision'], efs_score=efs['faithfulness_score'])
    print(f"\n[5] Auditing Metrics:")
    print(f"    Explanation Faithfulness Score (EFS): {efs['faithfulness_score']} / 100 ({efs['classification']})")
    print(f"    Bias/Behavioral Gap Index (BGI)      : {bgi['bgi_score']} / 100 ({bgi['classification']})")
    print(f"    Flagged For Inconsistency           : {bgi['flagged_for_audit']}")

    # 6. Qualification Counterfactual
    twin = make_qualification_variation(cand, "skills", "Remove Core Skill")
    twin_qual = compute_overall_qualification_score(twin, job)
    twin_eval = evaluate_candidate(twin, job, mode="Demo Simulation Mode")
    print(f"\n[6] Qualification Counterfactual Intervention (Ablate Core Skill):")
    print(f"    Twin Skills: {twin['skills']}")
    print(f"    Twin Qual Score: {twin_qual['qualification_score']}% (vs {qual_res['qualification_score']}%)")
    print(f"    Twin Recommendation: {twin_eval['decision']} (vs {ai_eval['decision']})")

    print("\n" + "=" * 70)
    print("[OK] Pipeline Demonstration Completed Successfully!")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        sys.exit(subprocess.call([sys.executable, "-m", "pytest"]))
    elif len(sys.argv) > 1 and sys.argv[1] == "all":
        run_cli_demo()
        print("\n[*] Running pytest suite...")
        sys.exit(subprocess.call([sys.executable, "-m", "pytest"]))
    else:
        run_cli_demo()
