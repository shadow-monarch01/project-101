import pytest
from modules.variations import make_qualification_variation, generate_counterfactual_pair

def test_skill_ablation():
    cand = {
        "candidate_id": "SWE_001",
        "name": "Priya",
        "skills": "Python; SQL; REST API; Git; FastAPI",
        "experience_years": 6.0,
        "education": "B.Tech CS"
    }
    twin = make_qualification_variation(cand, "skills", "Remove Core Skill")
    assert "SQL" in twin["skills"]
    assert twin["experience_years"] == 6.0
    assert twin["education"] == "B.Tech CS"

def test_experience_scaling():
    cand = {"candidate_id": "SWE_001", "experience_years": 6.0, "education": "B.Tech"}
    twin = make_qualification_variation(cand, "experience_years", "1.5")
    assert twin["experience_years"] == 1.5
    assert twin["education"] == "B.Tech"

def test_combined_skill_and_experience_perturbation():
    cand = {
        "candidate_id": "SWE_001",
        "name": "Alex",
        "skills": "Python; SQL; Git; FastAPI",
        "experience_years": 5.0,
        "education": "B.Tech CS"
    }
    twin = make_qualification_variation(cand, "skills_and_experience", "Remove Core Skill")
    assert "SQL" in twin["skills"]
    assert twin["education"] == "B.Tech CS"




