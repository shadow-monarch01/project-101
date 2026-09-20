"""
AI Hiring Intelligence - Qualification Engine (Module Alias)
Provides singular module alias for qualification scoring functions.
"""

from modules.qualifications import (
    DEFAULT_JOB_TEMPLATES,
    DEFAULT_SCORING_WEIGHTS,
    match_skills,
    parse_skills_list,
    normalize_skill_string,
    evaluate_experience_match,
    evaluate_education_relevance,
    evaluate_projects_score,
    compute_overall_qualification_score
)
