# ⚖️ AI Hiring Intelligence System
### Qualification-Based Candidate Assessment, Evidence Grounding & Decision Auditing

[![Python](https://img.shields.io/badge/Python-3.11%20|%203.12%20|%203.13%20|%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Pytest-77%2F77%20Passed-brightgreen.svg)](tests/)
[![Architecture](https://img.shields.io/badge/Architecture-Demographic--Free%20Audit-orange.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

---

## 📌 1. Project Overview & Pivot Rationale
In AI-driven applicant tracking systems (ATS) and recruitment pipelines, Large Language Models (LLMs) are increasingly deployed to screen resumes and justify hiring recommendations. However, standard AI evaluations often suffer from:
1. **Unverified Credentials & Inconsistent Data**: Profiles containing timeline anomalies, uncorroborated skills, or duration contradictions.
2. **Unfaithful Post-Hoc Explanations**: AI justifications that hallucinate missing qualifications, claim non-existent deficiencies, or contradict candidate records.
3. **Black-Box Decision Drift**: Lack of transparent, mathematically grounded alignment between candidate merit and AI recommendations.

Following academic review and panel feedback, this project operates strictly as an objective, ethical, and mathematically grounded **Qualification-Based Assessment, Evidence Grounding, Explanation Faithfulness (EFS), and Candidate Background Investigation (BI)** framework.

### 🛡️ Core Ethical Standard & Background Investigation Framing
> **The system evaluates candidates strictly on verified job qualifications, required technical skills, domain experience, education, certifications, and technical projects. Sensitive demographic attributes (gender, religion, ethnicity, age, nationality) are entirely excluded from the evaluation pipeline.**
>
> **Background Investigation Disclaimer**: Candidate Background Investigation (BI) evaluates whether candidate claims are supported, internally consistent, or contradictory based on provided profile facts. This is an internal evidence grounding analysis and does not constitute an external official background check.

---

## 🚀 2. System Architecture & Processing Pipeline

```
[ Job Description / Requirements ]          [ Candidate Resume / Profile ]
        │                                                   │
        └───────────────────────┬───────────────────────────┘
                                │
                                ▼
        ┌──────────────────────────────────────────────────┐
        │  1. Canonical Skill Normalization & Alias Engine  │
        │  - 50+ Synonyms (e.g. k8s -> Kubernetes)         │
        │  - Case/Format Agnostic Token Matching           │
        └───────────────────────┬──────────────────────────┘
                                │
                                ▼
        ┌──────────────────────────────────────────────────┐
        │  2. Qualification & Multi-Component Engine       │
        │  - Required (40%) & Preferred (10%) Skills Match  │
        │  - Experience (25%), Education (15%), Certs (5%) │
        │  - Independent Projects Score (5%)               │
        │  - Separate Technical Interview Score (0-100)    │
        │  - Deterministic Benchmark: Score_qual (0-100%)  │
        └───────────────────────┬──────────────────────────┘
                                │
                                ▼
        ┌──────────────────────────────────────────────────┐
        │  3. AI / LLM Hiring Evaluator & Explainer        │
        │  - Local Ollama (Qwen 2.5 / 3.5, Llama 3)        │
        │  - Fallback Deterministic Qualification Engine   │
        │  - Generates: Recommendation, Score, Reason      │
        └───────────────────────┬──────────────────────────┘
                                │
                                ▼
        ┌──────────────────────────────────────────────────┐
        │  4. Evidence Grounding & Factuality Verifier     │
        │  - Extract discrete verifiable claims from text  │
        │  - Classify: SUPPORTED, PARTIAL, UNSUPPORTED,    │
        │              or CONTRADICTED                     │
        │  - 6 Grounding Dimensions (Skills, Exp, Edu, etc)│
        └───────────────────────┬──────────────────────────┘
                                │
                                ▼
        ┌──────────────────────────────────────────────────┐
        │  5. Background Investigation (BI) Engine         │
        │  - 6 Credential Dimensions: Edu, Exp, Certs,     │
        │    Skills, Projects, Employment History          │
        │  - Internal Consistency & Anomaly Checker        │
        │  - Status: VERIFIED, PARTIAL, INCONSISTENT       │
        │  - Monotonic & Pairwise Decision Consistency     │
        └───────────────────────┬──────────────────────────┘
                                │
                                ▼
        ┌──────────────────────────────────────────────────┐
        │  6. Mitigation Loop & Re-Evaluation              │
        │  - Affirmative Qualification Directives          │
        │  - Empirical Before vs After Gap Recovery        │
        └──────────────────────────────────────────────────┘
```

---

## 🔬 3. Core Mathematical Formulations & Auditing Metrics

### 1. Transparent Qualification Score ($Score_{qual}$)
A multi-criteria weighted composite ensuring candidate benchmark scores are anchored strictly in verified qualifications:
$$Score_{qual} = w_s \cdot \text{ReqSkills} + w_p \cdot \text{PrefSkills} + w_e \cdot \text{Exp} + w_d \cdot \text{Edu} + w_c \cdot \text{Certs} + w_r \cdot \text{Projects}$$

* **Default Weighting**:
  * Required Skills ($\text{ReqSkills}$): **40%**
  * Preferred Skills ($\text{PrefSkills}$): **10%**
  * Domain Experience ($\text{Exp}$): **25%**
  * Education Level ($\text{Edu}$): **15%**
  * Professional Certifications ($\text{Certs}$): **5%**
  * Practical Projects Portfolio ($\text{Projects}$): **5%**
* **Technical Interview Score**: Handled as an independent post-screening evaluation dimension (0–100) and not conflated with candidate project credentials.

---

### 2. Evidence Grounding & Traceability Framework
Extracts verifiable factual assertions from AI justification text and classifies each claim against the candidate record:

| Claim Verification Status | Definition | Faithfulness Impact |
| :--- | :--- | :---: |
| `SUPPORTED` | Claim matches candidate record and requirements | $0$ Penalty |
| `PARTIALLY_SUPPORTED` | Claim is plausibly aligned but lacks direct explicit evidence | $-3$ Penalty |
| `UNSUPPORTED` | AI mentions credentials not found in candidate profile | $-8$ Penalty |
| `CONTRADICTED` | AI claims candidate lacks a skill they demonstrably possess | $-20$ Penalty |

$$\text{Grounding Score} = \max\left(0, \min\left(100, 100 - 20 \cdot N_{\text{contradicted}} - 8 \cdot N_{\text{unsupported}} - 3 \cdot N_{\text{partial}}\right)\right)$$

---

### 3. Enhanced Explanation Faithfulness Score (EFS)
Quantifies whether the AI's natural language justification accurately reflects candidate merits across 6 grounding dimensions:
$$\text{EFS} = \text{clamp}\left(100 - \sum \text{Penalties}_{\text{Hallucinated Missing Skills}} - \sum \text{Penalties}_{\text{Evidence Violations}}, 0, 100\right)$$

#### 6 Grounding Dimensions Evaluated:
1. `skill_grounding`: Accuracy of matched/missing skill citations against verified resume skills.
2. `experience_grounding`: Alignment of experience evaluation with actual years in domain.
3. `education_grounding`: Correct reflection of degree requirements (Bachelors/Masters/PhD).
4. `certification_grounding`: Factual verification of active industry certifications.
5. `project_grounding`: Assessment grounded in actual project count, scope, and technologies.
6. `decision_grounding`: Internal coherence between stated reasoning and assigned recommendation.

---

### 4. Evidence-Based Candidate Background Investigation (BI)
Evaluates whether candidate credentials across 6 dimensions are supported, internally consistent, or contradictory based on provided profile facts:

$$\text{Evidence Coverage} = 0.25(\text{Edu}) + 0.25(\text{Exp}) + 0.25(\text{Skills}) + 0.10(\text{Certs}) + 0.10(\text{Projects}) + 0.05(\text{History})$$

* **6 Investigation Dimensions**:
  1. `Education`: Degree level, institution, major field relevance.
  2. `Experience`: Claimed years vs itemized employment records.
  3. `Certifications`: Professional credentials documented in profile.
  4. `Skills`: Canonical normalized skills corroborated by projects/experience.
  5. `Projects`: Practical portfolio projects and technologies.
  6. `Employment History`: Itemized roles, companies, and tenure continuity.
* **Overall Status Categories**:
  * `VERIFIED_FROM_PROVIDED_EVIDENCE`: All primary credentials supported with zero contradictions.
  * `PARTIALLY_VERIFIED_FROM_PROVIDED_EVIDENCE`: Primary credentials supported with minor non-critical gaps.
  * `INSUFFICIENT_EVIDENCE`: Core qualification fields missing from profile.
  * `INCONSISTENCY_DETECTED`: Contradictory duration, timeline anomalies, or conflicting records identified.

---

### 5. Monotonic & Pairwise Decision Consistency
* **Monotonicity**: If candidate $A$ strictly dominates candidate $B$ in all qualification dimensions ($Score_{qual}(A) > Score_{qual}(B)$), then $Score_{AI}(A) \ge Score_{AI}(B)$.
* **Violation Flag**: When $Score_{qual}(A) \ge Score_{qual}(B) + 10$ but $Score_{AI}(A) < Score_{AI}(B)$, a monotonicity violation is recorded.

---

## 🔤 4. Canonical Skill Normalization Dictionary

The normalization engine resolves aliases, abbreviations, casing, and typos to canonical skill names:

| Category | Canonical Skill | Resolved Aliases / Synonyms |
| :--- | :--- | :--- |
| **Languages** | `Python` | `python`, `py`, `python3`, `python 3` |
| | `JavaScript` | `javascript`, `js`, `es6`, `ecmascript` |
| | `TypeScript` | `typescript`, `ts` |
| | `C++` | `cpp`, `c plus plus` |
| | `C#` | `csharp`, `c sharp`, `cs` |
| | `Golang` | `go`, `golang` |
| **Databases** | `PostgreSQL` | `postgres`, `postgresql`, `psql`, `pg` |
| | `MongoDB` | `mongo`, `mongodb` |
| | `MySQL` | `mysql` |
| | `Redis` | `redis`, `redis cache` |
| **Frameworks** | `FastAPI` | `fastapi`, `fast api` |
| | `Django` | `django`, `django rest framework`, `drf` |
| | `Flask` | `flask` |
| | `React` | `react`, `reactjs`, `react.js` |
| | `Node.js` | `node`, `nodejs`, `node.js` |
| **Cloud & DevOps** | `Kubernetes` | `k8s`, `kubernetes`, `kube` |
| | `Docker` | `docker`, `containerization`, `containers` |
| | `AWS` | `aws`, `amazon web services`, `ec2`, `s3` |
| | `GCP` | `gcp`, `google cloud`, `google cloud platform` |
| | `Azure` | `azure`, `microsoft azure` |
| | `CI/CD` | `cicd`, `ci/cd`, `github actions`, `gitlab ci` |
| **AI / ML** | `PyTorch` | `pytorch`, `torch` |
| | `TensorFlow` | `tf`, `tensorflow` |
| | `Scikit-Learn` | `scikit-learn`, `sklearn` |
| | `NLP` | `nlp`, `natural language processing` |
| | `Computer Vision` | `cv`, `computer vision` |
| **Architecture** | `REST API` | `rest`, `rest api`, `restful`, `restful api` |
| | `GraphQL` | `graphql`, `gql` |
| | `Microservices` | `microservices`, `microservice architecture` |

---

## 🛠️ 5. Technology Stack

* **Backend Framework**: Python 3.11 – 3.14, FastAPI 0.115+, Uvicorn, Pydantic v2
* **Machine Learning & NLP**: Scikit-Learn (TF-IDF Vectorization, K-Means Clustering $k=3$)
* **Data Processing**: Pandas, NumPy
* **Statistical Auditing**: SciPy (`scipy.stats.binomtest`, `scipy.stats.chi2_contingency`, `scipy.stats.ttest_rel`)
* **AI Evaluators**: Local Ollama (`qwen2.5`, `qwen3.5`, `llama3`), Cloud API endpoints, Deterministic Simulator
* **Frontend**: Vanilla HTML5, Modern CSS3 (Dark/Light Mode), Vanilla ES6+ JavaScript (Zero React / npm build dependencies)
* **Testing Suite**: Pytest (77 automated unit and integration tests)

---

## 📡 6. Complete REST API Reference (24 Endpoints)

All endpoints accept JSON payloads and return structured responses.

| # | Endpoint | Method | Description | Sample Request | Sample Response |
| :---: | :--- | :---: | :--- | :--- | :--- |
| 1 | `/api/health` | `GET` | Health status and Ollama availability | `GET /api/health` | `{"status":"healthy","ollama_available":true}` |
| 2 | `/api/jobs` | `GET` | Retrieve job role profiles | `GET /api/jobs` | `[{"id":"backend_dev","title":"...","required_skills":[...]}]` |
| 3 | `/api/jobs` | `POST` | Create or update job profile | `{"id":"ml_eng","title":"ML Engineer",...}` | `{"status":"created","job":{...}}` |
| 4 | `/api/candidates` | `GET` | Retrieve candidate pool | `GET /api/candidates?job_id=backend_dev` | `{"count":10,"candidates":[...]}` |
| 5 | `/api/candidates` | `POST` | Add custom candidate | `{"id":"C_99","name":"Alex",...}` | `{"status":"created","candidate":{...}}` |
| 6 | `/api/candidates/{id}` | `GET` | Fetch single candidate | `GET /api/candidates/SWE_001` | `{"id":"SWE_001","name":"Priya Sharma",...}` |
| 7 | `/api/skill-analysis` | `POST` | Skill gap analysis & matching | `{"candidate_skills":["py","postgres"],"required_skills":["Python","PostgreSQL"]}` | `{"matched_required":["Python","PostgreSQL"],"skill_gap_percentage":0.0}` |
| 8 | `/api/skill-normalization` | `POST` | Normalize raw skill aliases | `{"skills":["k8s","js","postgres","fast api"]}` | `{"normalized_skills":["Kubernetes","JavaScript","PostgreSQL","FastAPI"]}` |
| 9 | `/api/qualification-score` | `POST` | Deterministic qualification score | `{"candidate":{...},"job":{...}}` | `{"qualification_score":88.5,"breakdown":{...}}` |
| 10 | `/api/evaluate` | `POST` | Primary AI candidate evaluation | `{"candidate":{...},"job":{...}}` | `{"recommendation":"STRONG_HIRE","score":90,"efs":96.0,"background_investigation":{...}}` |
| 11 | `/api/background-investigation` | `POST` | Candidate Background Investigation | `{"candidate":{...},"job":{...}}` | `{"overall_status":"VERIFIED_FROM_PROVIDED_EVIDENCE","evidence_coverage_percentage":95.0,...}` |
| 12 | `/api/efs` | `POST` | Compute 6-dimension EFS | `{"justification":"Strong Python skills...","candidate":{...},"job":{...}}` | `{"efs":95.0,"grounding_breakdown":{...}}` |
| 13 | `/api/evidence` | `POST` | Extract & verify factual claims | `{"justification":"Candidate has 5 yrs exp and knows Python.","candidate":{...}}` | `{"claims":[{"claim":"...","status":"SUPPORTED"}],"evidence_grounding_score":100}` |
| 14 | `/api/decision-consistency`| `POST`| Monotonic & pairwise checks | `{"candidates_with_evaluations":[{"candidate":{...},"evaluation":{...}}]}` | `{"is_monotonic":true,"violations":[],"consistency_score":100}` |
| 15 | `/api/counterfactual` | `POST` | Causal perturbation evaluation | `{"candidate":{...},"job":{...},"intervention_type":"remove_core_skill"}` | `{"original_eval":{...},"counterfactual_eval":{...},"is_monotonic":true}` |
| 16 | `/api/mitigation` | `POST` | Affirmative prompt mitigation | `{"candidate":{...},"job":{...}}` | `{"before":{...},"after":{...},"consistency_restored":true}` |
| 17 | `/api/batch-evaluate` | `POST` | Full candidate pool audit | `{"job_id":"backend_dev"}` | `{"total_candidates":10,"average_evidence_coverage":92.5,"average_efs":92.8,"candidates":[...]}` |
| 18 | `/api/cluster` | `POST` | TF-IDF + K-Means clustering | `{"candidates":[...]}` | `{"clusters":[{"cluster_id":0,"top_terms":["python","sql"],"candidates":[...]}]}` |
| 19 | `/api/statistics` | `POST` | Statistical disparity tests | `{"group_a":[...],"group_b":[...]}` | `{"mcnemar_p_value":0.45,"chi_square_p_value":0.62,"disparity_detected":false}` |
| 20 | `/api/re-evaluate` | `POST` | Re-evaluate with modified criteria| `{"candidate_id":"SWE_001","adjusted_weights":{"skills":0.5}}` | `{"candidate_id":"SWE_001","updated_score":91.2}` |
| 21 | `/api/resume-screen` | `POST` | Resume text parsing & match | `{"resume_text":"Experienced Python developer with Django and AWS..."}` | `{"parsed_skills":["Python","Django","AWS"],"suggested_roles":[...]}` |
| 22 | `/api/export-report` | `POST` | Export JSON/CSV audit report | `{"candidates":[...],"format":"json"}` | `{"export_url":"/reports/audit_2026.json","summary":{...}}` |
| 23 | `/api/upload_dataset` | `POST` | Upload custom candidate dataset | `FormData: file=@candidates.csv` | `{"status":"success","rows_imported":50}` |
| 24 | `/api/report/{id}` | `GET` | Individual Candidate Audit Dossier| `GET /api/report/SWE_001` | `{"candidate_id":"SWE_001","dossier":{...}}` |

---

### Sample cURL Commands

#### 1. Evaluate Candidate with Evidence Traceability & Grounding
```bash
curl -X POST "http://127.0.0.1:8000/api/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate": {
      "id": "SWE_001",
      "name": "Priya Sharma",
      "skills": ["Python", "PostgreSQL", "FastAPI", "Docker", "Git"],
      "experience_years": 5,
      "education": "B.Tech Computer Science",
      "certifications": ["AWS Certified Developer"],
      "projects_score": 88.0,
      "technical_interview_score": 90.0
    },
    "job": {
      "id": "backend_dev",
      "title": "Senior Python Backend Engineer",
      "required_skills": ["Python", "SQL", "REST API", "Git", "PostgreSQL"],
      "preferred_skills": ["Docker", "FastAPI", "AWS", "CI/CD"],
      "min_experience_years": 4,
      "min_education_level": "Bachelors"
    }
  }'
```

#### 2. Evidence Traceability Claim Verification
```bash
curl -X POST "http://127.0.0.1:8000/api/evidence" \
  -H "Content-Type: application/json" \
  -d '{
    "justification": "Candidate has 5 years of Python experience, knows FastAPI and Docker, but lacks required Rust experience.",
    "candidate": {
      "id": "SWE_001",
      "skills": ["Python", "FastAPI", "Docker"],
      "experience_years": 5
    },
    "job": {
      "id": "backend_dev",
      "required_skills": ["Python", "PostgreSQL"]
    }
  }'
```

#### 3. Canonical Skill Normalization
```bash
curl -X POST "http://127.0.0.1:8000/api/skill-normalization" \
  -H "Content-Type: application/json" \
  -d '{
    "skills": ["postgres", "k8s", "js", "fast api", "aws", "py"]
  }'
```

---

## 💻 7. Installation & Quick Start

### 1. Windows 1-Click Launch
Double-click `run_complete_system.bat` or `launch_hiring_system.bat`.
This automatically launches the FastAPI server and opens your default browser at `http://127.0.0.1:8000`.

### 2. Manual Setup
```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run all 52 automated unit & integration tests
python -m pytest

# 4. Run CLI demonstration pipeline
python main.py all

# 5. Start FastAPI application server
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🧪 8. Test Suite Summary (52/52 Tests Passing)

The project includes 52 automated tests across 8 test suites:

| Test Module | Tests | Description | Status |
| :--- | :---: | :--- | :---: |
| `test_priority1_features.py` | 29 | Evidence traceability, EFS 6-dim, BGI 3-comp, Skill normalizer, API endpoints | ✅ Passed |
| `test_api.py` | 7 | REST API status codes, schema validation, and health checks | ✅ Passed |
| `test_bgi.py` | 3 | BGI calculation, component decomposition, and rank gap calculations | ✅ Passed |
| `test_faithfulness.py` | 2 | EFS calculation, hallucination penalty, and grounding checks | ✅ Passed |
| `test_qualifications.py` | 3 | Multi-component qualification scoring, weights, and normalization | ✅ Passed |
| `test_statistics.py` | 4 | McNemar test, Chi-square, and paired regression statistical checks | ✅ Passed |
| `test_variations.py` | 2 | Qualification counterfactual perturbations and causal consistency | ✅ Passed |
| `test_clustering.py` | 2 | TF-IDF candidate skill vectorization and K-Means clustering ($k=3$) | ✅ Passed |
| **Total** | **52** | **100% Passing Test Suite** | **✅ All 52 Passed** |

---

## 🎬 9. 5-Minute Viva / Project Demonstration Walkthrough

1. **Step 1: System Overview & KPI Dashboard (Tab 1)**
   - Open `http://127.0.0.1:8000` in browser.
   - Show active role: `Senior Python Backend Engineer` with required skills (`Python`, `SQL`, `REST API`, `Git`, `PostgreSQL`).
   - Highlight KPI cards: **Mean Qualification Score (84.5%)**, **Mean EFS (92.4)**, **Mean BGI (14.8)**.
2. **Step 2: Candidate Pool, Semantic Clustering & Evidence Card (Tab 2)**
   - Click **"Semantic Clustering (TF-IDF + K-Means)"** to showcase skill-based candidate grouping.
   - Select candidate `SWE_001` (Priya Sharma).
   - Show the **Evidence Traceability Claims Table**: verified claims (`SUPPORTED`), claim status badges, and 6-dimension EFS breakdown meter.
3. **Step 3: Qualification Counterfactual Playground (Tab 3)**
   - Select `SWE_001` and choose **"Remove Core Skill: Python"**.
   - Click **"Execute Causal Evaluation"**.
   - Show the monotonic decision transition (`STRONG_HIRE` $\to$ `INTERVIEW`), demonstrating causal sensitivity to true qualifications.
4. **Step 4: Mitigation Feedback Loop (Tab 4)**
   - Click **"Execute Mitigation & Re-evaluation"**.
   - Highlight the Before vs After comparison and empirical BGI reduction ($82.8\%$ gap improvement).
5. **Step 5: Interactive REST API Console (Tab 6)**
   - Select `/api/evidence` or `/api/bgi` in the dropdown.
   - Click **"Send API Request"** to show live JSON request/response execution for external ATS integration.

---

## 📄 10. License & Ethics Statement
This project is licensed under the MIT License. It is intended for academic research, recruitment auditing, and transparency verification. The system is designed to audit AI decision drift and ensure merit-based hiring practices.
