"""
AI Hiring Intelligence - Semantic Candidate Clustering Module
Uses TF-IDF Vectorization and K-Means Clustering (k=3) on job-relevant candidate attributes
(technical skills, experience, education, projects, and target role) to cluster similar candidates.
"""

import pandas as pd
from typing import Dict, Any, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

def prepare_qualification_text(row: Dict[str, Any]) -> str:
    skills = str(row.get("skills", row.get("technical_skills", "")))
    role = str(row.get("role", row.get("expected_role", "Software Engineer")))
    edu = str(row.get("education", row.get("degree", "")))
    exp = str(row.get("experience_years", row.get("experience", 3)))
    certs = str(row.get("certifications", ""))
    projects = str(row.get("projects", ""))

    return f"{role} {skills} {skills} {edu} {exp} years experience {certs} {projects}"

def cluster_dataframe(df: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:
    df_out = df.copy()
    if len(df_out) == 0:
        df_out["cluster"] = []
        return df_out

    k = min(n_clusters, len(df_out))
    if k <= 1:
        df_out["cluster"] = 0
        return df_out

    text_corpus = [prepare_qualification_text(row.to_dict()) for _, row in df_out.iterrows()]

    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=100)
        X = vectorizer.fit_transform(text_corpus)
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        df_out["cluster"] = kmeans.fit_predict(X)
    except Exception:
        df_out["cluster"] = [i % k for i in range(len(df_out))]

    return df_out

def get_cluster_summary(df_clustered: pd.DataFrame) -> Dict[str, Any]:
    if "cluster" not in df_clustered.columns:
        return {}

    summary = {}
    for cl_id, group in df_clustered.groupby("cluster"):
        roles = group["expected_role"].tolist() if "expected_role" in group.columns else group.get("role", []).tolist()
        exp_col = "experience_years" if "experience_years" in group.columns else "experience"
        avg_exp = round(group[exp_col].astype(float).mean(), 1) if exp_col in group.columns else 0.0

        summary[str(cl_id)] = {
            "count": len(group),
            "avg_experience_years": avg_exp,
            "sample_roles": list(set(roles))[:3]
        }

    return summary
