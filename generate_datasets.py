"""
AI Hiring Intelligence - Qualification Benchmark Dataset Generator
Generates realistic, qualification-rich candidate profiles across multiple technical domains
(Software Engineering, Cloud & DevOps, Data Science/AI, Full Stack Web Development).
Zero demographic attributes.
"""

import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

SWE_BENCHMARK = [
    {
        "candidate_id": "SWE_001",
        "name": "Priya Sharma",
        "role": "Senior Backend Engineer",
        "expected_role": "Senior Python Backend Engineer",
        "experience_years": 6.0,
        "skills": "Python; SQL; PostgreSQL; REST API; Git; FastAPI; Docker; Microservices",
        "education": "B.Tech Computer Science",
        "degree": "B.Tech",
        "certifications": "AWS Certified Cloud Practitioner",
        "certifications_count": 1,
        "projects": "High-Throughput Payment Microservices; Distributed Cache Architecture",
        "interview_score": 90.0,
        "previous_salary": 120000
    },
    {
        "candidate_id": "SWE_002",
        "name": "Alexander Wright",
        "role": "Backend Engineer",
        "expected_role": "Senior Python Backend Engineer",
        "experience_years": 5.0,
        "skills": "Python; SQL; REST API; Git; Docker; PostgreSQL",
        "education": "B.Tech Computer Science",
        "degree": "B.Tech",
        "certifications": "AWS Solutions Architect",
        "certifications_count": 1,
        "projects": "Inventory Management API; Distributed Data Pipeline",
        "interview_score": 88.0,
        "previous_salary": 115000
    },
    {
        "candidate_id": "SWE_003",
        "name": "Elena Rostova",
        "role": "Staff Software Architect",
        "expected_role": "Senior Python Backend Engineer",
        "experience_years": 10.0,
        "skills": "Python; SQL; PostgreSQL; REST API; Git; FastAPI; Kubernetes; Distributed Systems; Kafka",
        "education": "M.S. Software Engineering",
        "degree": "M.S.",
        "certifications": "AWS Solutions Architect; CKA",
        "certifications_count": 2,
        "projects": "Enterprise Multi-Region Microservices; Event Streaming Engine",
        "interview_score": 94.0,
        "previous_salary": 160000
    },
    {
        "candidate_id": "SWE_004",
        "name": "James Sterling",
        "role": "Junior Python Developer",
        "expected_role": "Senior Python Backend Engineer",
        "experience_years": 1.5,
        "skills": "Python; Git; SQLite; HTML/CSS",
        "education": "B.S. Information Technology",
        "degree": "B.S.",
        "certifications": "",
        "certifications_count": 0,
        "projects": "Personal Blog API; Scraping Utility",
        "interview_score": 68.0,
        "previous_salary": 65000
    },
    {
        "candidate_id": "SWE_005",
        "name": "Carlos Delgado",
        "role": "Mid Backend Developer",
        "expected_role": "Senior Python Backend Engineer",
        "experience_years": 4.0,
        "skills": "Python; SQL; REST API; Git; Django; MySQL",
        "education": "B.Tech Information Technology",
        "degree": "B.Tech",
        "certifications": "Python Certified Developer",
        "certifications_count": 1,
        "projects": "E-commerce Order API; Search Index Service",
        "interview_score": 82.0,
        "previous_salary": 98000
    },
    {
        "candidate_id": "SWE_006",
        "name": "Arthur Pendelton",
        "role": "Software Engineer (Non-Degree)",
        "expected_role": "Senior Python Backend Engineer",
        "experience_years": 4.5,
        "skills": "Python; SQL; PostgreSQL; REST API; Git; FastAPI; Redis",
        "education": "Bootcamp Certificate in Fullstack Development",
        "degree": "Certificate",
        "certifications": "AWS Certified Developer",
        "certifications_count": 1,
        "projects": "Real-Time Chat Microservice; Open Source Contributor",
        "interview_score": 86.0,
        "previous_salary": 95000
    },
    {
        "candidate_id": "SWE_007",
        "name": "Amina Diallo",
        "role": "Backend Engineer",
        "expected_role": "Senior Python Backend Engineer",
        "experience_years": 3.5,
        "skills": "Python; REST API; Git; Flask; MongoDB",
        "education": "B.S. Computer Engineering",
        "degree": "B.S.",
        "certifications": "",
        "certifications_count": 0,
        "projects": "Auth Token Microservice; Telemetry Collector",
        "interview_score": 76.0,
        "previous_salary": 88000
    },
    {
        "candidate_id": "SWE_008",
        "name": "Hunter Reed",
        "role": "Systems Programmer",
        "expected_role": "Senior Python Backend Engineer",
        "experience_years": 6.0,
        "skills": "C++; Linux; Bash; Python (Basic); Git",
        "education": "B.S. Computer Science",
        "degree": "B.S.",
        "certifications": "Linux Foundation Certified Engineer",
        "certifications_count": 1,
        "projects": "Kernel Driver Interface; Low Latency Socket Server",
        "interview_score": 78.0,
        "previous_salary": 110000
    }
]

DEVOPS_BENCHMARK = [
    {
        "candidate_id": "OPS_001",
        "name": "Marcus Vance",
        "role": "Senior DevOps Engineer",
        "expected_role": "Cloud DevOps & Platform Engineer",
        "experience_years": 5.5,
        "skills": "AWS; Terraform; Docker; Kubernetes; CI/CD; Linux; Prometheus; Python",
        "education": "B.Tech Computer Science",
        "degree": "B.Tech",
        "certifications": "AWS Solutions Architect Professional; CKA",
        "certifications_count": 2,
        "projects": "Multi-Region Terraform Infrastructure; Automated Zero-Downtime Pipeline",
        "interview_score": 92.0,
        "previous_salary": 135000
    },
    {
        "candidate_id": "OPS_002",
        "name": "Chloe Chen",
        "role": "Cloud Engineer",
        "expected_role": "Cloud DevOps & Platform Engineer",
        "experience_years": 3.0,
        "skills": "AWS; Docker; CI/CD; Linux; Bash; Git",
        "education": "B.S. Information Systems",
        "degree": "B.S.",
        "certifications": "AWS Certified SysOps",
        "certifications_count": 1,
        "projects": "Container Migration; Jenkins Automated Build Cluster",
        "interview_score": 84.0,
        "previous_salary": 105000
    },
    {
        "candidate_id": "OPS_003",
        "name": "Liam O'Connor",
        "role": "Junior Infrastructure Admin",
        "expected_role": "Cloud DevOps & Platform Engineer",
        "experience_years": 1.0,
        "skills": "Linux; Bash; Git; Docker (Basic)",
        "education": "Associate Degree in Network Administration",
        "degree": "Associate",
        "certifications": "CompTIA Linux+",
        "certifications_count": 1,
        "projects": "Internal Server Monitoring Script; Backup Automation",
        "interview_score": 65.0,
        "previous_salary": 58000
    }
]

DATA_SCIENCE_BENCHMARK = [
    {
        "candidate_id": "DS_001",
        "name": "Dr. Sophia Lindqvist",
        "role": "Senior Data Scientist",
        "expected_role": "Data Scientist & Machine Learning Engineer",
        "experience_years": 6.0,
        "skills": "Python; Machine Learning; SQL; Pandas; Scikit-learn; PyTorch; NLP; Deep Learning",
        "education": "Ph.D. in Computational Statistics",
        "degree": "Ph.D.",
        "certifications": "TensorFlow Developer Certificate",
        "certifications_count": 1,
        "projects": "Customer Churn Prediction Neural Network; LLM Fine-Tuning Pipeline",
        "interview_score": 95.0,
        "previous_salary": 150000
    },
    {
        "candidate_id": "DS_002",
        "name": "Rohan Mehta",
        "role": "Machine Learning Engineer",
        "expected_role": "Data Scientist & Machine Learning Engineer",
        "experience_years": 3.5,
        "skills": "Python; Machine Learning; SQL; Pandas; Scikit-learn; Docker; FastAPI",
        "education": "M.S. in Data Science",
        "degree": "M.S.",
        "certifications": "Azure Data Scientist Associate",
        "certifications_count": 1,
        "projects": "Recommendation Engine Microservice; Automated Feature Store",
        "interview_score": 87.0,
        "previous_salary": 115000
    }
]

def generate_hiring_master():
    """Generates 40 diverse qualification candidate profiles across multiple tech disciplines."""
    np.random.seed(42)
    first_names = ["Aarav", "Liam", "Sophia", "Emma", "Noah", "Zoe", "Ethan", "Mia", "Mateo", "Ava", "Leo", "Isabella", "Kavya", "Lucas", "Amara", "Owen", "Maya", "Daniel", "Hannah", "Gabriel"]
    last_names = ["Patel", "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson"]
    
    roles = [
        ("Senior Python Backend Engineer", ["Python", "SQL", "REST API", "Git", "PostgreSQL", "FastAPI", "Docker"], 4.0, 10.0),
        ("Full Stack Web Developer", ["JavaScript", "React", "Node.js", "SQL", "HTML/CSS", "TypeScript", "TailwindCSS"], 2.0, 8.0),
        ("Cloud DevOps & Platform Engineer", ["AWS", "Terraform", "Docker", "CI/CD", "Linux", "Kubernetes", "Jenkins"], 3.0, 9.0),
        ("Data Scientist & Machine Learning Engineer", ["Python", "Machine Learning", "SQL", "Pandas", "Scikit-learn", "PyTorch"], 3.0, 8.0)
    ]
    
    degrees = ["B.Tech Computer Science", "M.S. Software Engineering", "B.S. Information Systems", "Ph.D. in Computer Science", "Bootcamp Certificate"]
    certs_pool = ["AWS Solutions Architect", "CKA Kubernetes Administrator", "Python Certified Professional", "TensorFlow Developer", "Azure Fundamentals"]

    records = []
    for i in range(40):
        c_id = f"CAND_{i+1:03d}"
        name = f"{np.random.choice(first_names)} {np.random.choice(last_names)}"
        target_role, skill_pool, min_e, max_e = roles[i % len(roles)]
        
        tier = i % 4
        if tier == 0:
            exp = round(float(np.random.uniform(min_e + 2.0, max_e)), 1)
            cand_skills = skill_pool[:np.random.randint(5, len(skill_pool) + 1)]
            score = round(float(np.random.uniform(88, 98)), 1)
            deg = degrees[0]
            n_certs = int(np.random.randint(1, 3))
        elif tier == 1:
            exp = round(float(np.random.uniform(min_e, min_e + 2.5)), 1)
            cand_skills = skill_pool[:np.random.randint(4, len(skill_pool))]
            score = round(float(np.random.uniform(78, 87)), 1)
            deg = degrees[0]
            n_certs = 1
        elif tier == 2:
            exp = round(float(np.random.uniform(max(1.0, min_e - 1.0), min_e + 1.0)), 1)
            cand_skills = skill_pool[:3] + ["Git"]
            score = round(float(np.random.uniform(68, 77)), 1)
            deg = degrees[2]
            n_certs = 0
        else:
            exp = round(float(np.random.uniform(0.5, 2.0)), 1)
            cand_skills = [skill_pool[0], "HTML/CSS"]
            score = round(float(np.random.uniform(55, 67)), 1)
            deg = degrees[4]
            n_certs = 0

        cert_str = "; ".join(np.random.choice(certs_pool, n_certs, replace=False)) if n_certs > 0 else ""

        records.append({
            "candidate_id": c_id,
            "name": name,
            "role": target_role.split()[0] + " Developer",
            "expected_role": target_role,
            "experience_years": exp,
            "skills": "; ".join(cand_skills),
            "education": deg,
            "degree": deg.split()[0],
            "certifications": cert_str,
            "certifications_count": n_certs,
            "projects": f"{target_role.split()[0]} Application Pipeline; Performance Optimization Project",
            "interview_score": score,
            "previous_salary": int(exp * 15000 + 50000)
        })

    return records

if __name__ == "__main__":
    print("[*] Generating Qualification-Based Benchmark Datasets...")
    
    # 1. 01_software_engineering_benchmark.csv
    df_swe = pd.DataFrame(SWE_BENCHMARK)
    swe_path = os.path.join(DATA_DIR, "01_software_engineering_benchmark.csv")
    df_swe.to_csv(swe_path, index=False)
    print(f"[OK] Created {swe_path} ({len(df_swe)} records)")

    # 2. 02_cloud_devops_benchmark.csv
    df_devops = pd.DataFrame(DEVOPS_BENCHMARK)
    devops_path = os.path.join(DATA_DIR, "02_cloud_devops_benchmark.csv")
    df_devops.to_csv(devops_path, index=False)
    print(f"[OK] Created {devops_path} ({len(df_devops)} records)")

    # 3. 03_data_science_ai_benchmark.csv
    df_ds = pd.DataFrame(DATA_SCIENCE_BENCHMARK)
    ds_path = os.path.join(DATA_DIR, "03_data_science_ai_benchmark.csv")
    df_ds.to_csv(ds_path, index=False)
    print(f"[OK] Created {ds_path} ({len(df_ds)} records)")

    # 4. hiring_master_qualifications.csv
    master_records = generate_hiring_master()
    df_master = pd.DataFrame(master_records)
    master_path = os.path.join(DATA_DIR, "hiring_master_qualifications.csv")
    df_master.to_csv(master_path, index=False)
    print(f"[OK] Created {master_path} ({len(df_master)} records)")

    # 5. Overwrite legacy high_bias dataset with pure qualification benchmarks
    high_bias_path = os.path.join(DATA_DIR, "high_bias_hiring_dataset.csv")
    df_master.to_csv(high_bias_path, index=False)
    print(f"[OK] Updated {high_bias_path}")

    print("[*] All Qualification Datasets Successfully Created!")
