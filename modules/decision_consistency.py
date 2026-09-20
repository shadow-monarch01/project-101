"""
AI Hiring Intelligence - Decision Consistency & Monotonicity Engine
Audits whether AI hiring recommendations follow rank-order monotonicity
and qualification alignment across candidate pairs and controlled variations.
"""

from typing import Dict, List, Any, Optional
from modules.bgi import get_decision_tier_rank, check_decision_consistency

def check_monotonicity(
    orig_score: float,
    mod_score: float,
    orig_decision: str,
    mod_decision: str
) -> Dict[str, Any]:
    """Checks whether AI decision responds monotonically to qualification shifts."""
    return check_decision_consistency(
        original_qual_score=orig_score,
        modified_qual_score=mod_score,
        original_decision=orig_decision,
        modified_decision=mod_decision
    )

def check_pairwise_consistency(
    cand_a_data: Dict[str, Any],
    cand_b_data: Dict[str, Any],
    eval_a: Dict[str, Any],
    eval_b: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Checks pairwise rank-order consistency between two candidates.
    Flags potential qualification-decision inconsistencies (e.g. Candidate A has score 90 and Rejected,
    while Candidate B has score 60 and Hired).
    """
    score_a = float(eval_a.get("qualification_score", cand_a_data.get("qualification_score", 0.0)))
    score_b = float(eval_b.get("qualification_score", cand_b_data.get("qualification_score", 0.0)))

    dec_a = str(eval_a.get("decision", "REJECT")).upper()
    dec_b = str(eval_b.get("decision", "REJECT")).upper()

    rank_a = get_decision_tier_rank(dec_a)
    rank_b = get_decision_tier_rank(dec_b)

    score_diff = round(score_a - score_b, 1)
    rank_diff = rank_a - rank_b

    is_consistent = True
    flagged = False
    inconsistency_reason = "Pairwise ranking is consistent with qualification differentials."

    if score_diff >= 15.0 and rank_diff < 0:
        is_consistent = False
        flagged = True
        inconsistency_reason = (
            f"Potential Qualification-Decision Inconsistency: {cand_a_data.get('name', 'Candidate A')} "
            f"has significantly higher qualification score ({score_a} vs {score_b}), yet received "
            f"lower recommendation ('{dec_a}' vs '{dec_b}')."
        )
    elif score_diff <= -15.0 and rank_diff > 0:
        is_consistent = False
        flagged = True
        inconsistency_reason = (
            f"Potential Qualification-Decision Inconsistency: {cand_b_data.get('name', 'Candidate B')} "
            f"has significantly higher qualification score ({score_b} vs {score_a}), yet received "
            f"lower recommendation ('{dec_b}' vs '{dec_a}')."
        )
    elif abs(score_diff) <= 2.0 and abs(rank_diff) >= 2:
        is_consistent = False
        flagged = True
        inconsistency_reason = (
            f"Potential Invariance Anomaly: Candidates have nearly identical qualification scores "
            f"({score_a} vs {score_b}), but diverged significantly in recommendation ('{dec_a}' vs '{dec_b}')."
        )

    return {
        "candidate_a_id": cand_a_data.get("candidate_id", "A"),
        "candidate_b_id": cand_b_data.get("candidate_id", "B"),
        "candidate_a_score": score_a,
        "candidate_b_score": score_b,
        "candidate_a_decision": dec_a,
        "candidate_b_decision": dec_b,
        "is_consistent": is_consistent,
        "flagged_for_review": flagged,
        "reason": inconsistency_reason,
        "score_difference": score_diff,
        "rank_difference": rank_diff
    }

def evaluate_pool_consistency(evaluated_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Audits rank-order monotonicity across a batch candidate pool.
    Calculates pairwise inversion rate and identifies anomalous pairs.
    """
    n = len(evaluated_candidates)
    if n < 2:
        return {
            "total_pairs_evaluated": 0,
            "inversion_pairs_count": 0,
            "consistency_rate": 100.0,
            "flagged_inversions": []
        }

    total_pairs = 0
    inversions = []

    for i in range(n):
        for j in range(i + 1, n):
            c_a = evaluated_candidates[i]
            c_b = evaluated_candidates[j]
            res = check_pairwise_consistency(c_a, c_b, c_a, c_b)
            total_pairs += 1
            if res["flagged_for_review"]:
                inversions.append(res)

    inversion_cnt = len(inversions)
    consistency_rate = round(((total_pairs - inversion_cnt) / max(1, total_pairs)) * 100.0, 1)

    return {
        "total_pairs_evaluated": total_pairs,
        "inversion_pairs_count": inversion_cnt,
        "consistency_rate": consistency_rate,
        "flagged_inversions": inversions[:15]  # Top 15 flagged pairs
    }
