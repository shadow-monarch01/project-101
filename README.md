# ⚖️ AI Hiring Intelligence System
### Qualification-Based Candidate Assessment, Explanation Faithfulness (EFS) & Bias Gap Analysis (BGI)

---

## 📌 1. Project Overview & Pivot Rationale
In AI-driven applicant tracking systems (ATS) and recruitment pipelines, Large Language Models (LLMs) are increasingly deployed to screen resumes and justify hiring recommendations. However, standard AI evaluations often suffer from **unexplained behavioral gaps** (where highly qualified candidates are unfairly rejected) and **unfaithful post-hoc explanations** (where the AI fabricates missing competencies).

Following academic review and panel feedback, this project pivots from sensitive demographic testing to an objective, ethical, and mathematically grounded **Qualification-Based Assessment, Explanation Faithfulness (EFS), and Bias/Behavioral Gap Analysis (BGI)** framework.

### 🛡️ Ethical Standard
> **The system evaluates candidates strictly on verified job qualifications, required technical skills, domain experience, and certifications. Sensitive demographic attributes (gender, religion, ethnicity, age, nationality) are entirely excluded from the evaluation criteria.**

---

## 🚀 2. System Architecture & Core Pipeline

```
[ Job Description / Requirements ]          [ Candidate Resume / Profile ]
        │                                                   │
        └───────────────────────┬───────────────────────────┘
                                │
                                ▼
        ┌──────────────────────────────────────────────────┐
        │  Qualification & Skill Gap Engine                │
        │  - Matched, Missing & Additional Skills          │
        │  - Weighted Qualification Score (0-100%)         │
        └───────────────────────┬──────────────────────────┘
                                │
                                ▼
        ┌──────────────────────────────────────────────────┐
        │  AI / LLM Decision & Justification Engine       │
        │  (Ollama Qwen 3.5 4B / Fallback Simulator)       │
        └───────────────────────┬──────────────────────────┘
                                │
                                ▼
        ┌──────────────────────────────────────────────────┐
        │  Auditing Engine: EFS + BGI                      │
        │  - Explanation Faithfulness Score (EFS)          │
        │  - Bias / Behavioral Gap Index (BGI)             │
        │  - Controlled Qualification Counterfactuals      │
        └───────────────────────┬──────────────────────────┘
                                │
                                ▼
        ┌──────────────────────────────────────────────────┐
        │  Mitigation Feedback Loop & Re-evaluation        │
        │  - Affirmative Qualification Prompt Directives   │
        │  - Empirical Before vs After Gap Recovery        │
        └──────────────────────────────────────────────────┘
```

---

## 🔬 3. Core Mathematical Formulations & Metrics

### 1. Transparent Qualification Score ($Score_{qual}$)
A multi-criteria weighted composite ensuring decisions are anchored strictly in job-relevant qualifications:
$$Score_{qual} = w_s \cdot \text{ReqSkills} + w_p \cdot \text{PrefSkills} + w_e \cdot \text{Exp} + w_d \cdot \text{Edu} + w_c \cdot \text{Certs} + w_r \cdot \text{Projects}$$
*Default Weights:* Required Skills ($40\%$), Preferred Skills ($10\%$), Experience ($25\%$), Education ($15\%$), Certifications ($5\%$), Projects ($5\%$).

### 2. Bias / Behavioral Gap Index (BGI)
A normalized index ($0-100$) measuring the discrepancy between expected merit-based performance and observed AI recommendation:
$$\text{BGI} = 0.40 \cdot |\text{Score}_{qual} - \text{Score}_{AI}| + 0.35 \cdot \text{RankGap}_{norm} + 0.15 \cdot (100 - \text{EFS}) + 0.10 \cdot \text{SkillGapPenalty}$$
* **0–20:** Very Low Gap *(High Consistency)*
* **21–40:** Low Gap *(Minor Variance)*
* **41–60:** Moderate Gap *(Noticeable Divergence)*
* **61–80:** High Gap *(Audit Flagged)*
* **81–100:** Very High Gap *(Severe Inconsistency)*

### 3. Explanation Faithfulness Score (EFS)
Quantifies whether the AI's natural language justification grounds accurately on verified candidate skills or hallucinates non-existent deficits:
$$\text{EFS} = 100 - \text{Penalties}_{\text{Hallucinated Missing Skills}} - \text{Penalties}_{\text{Grounding Inconsistencies}}$$

---

## 🛠️ 4. Technology Stack

* **Backend:** Python 3.11 – 3.14, FastAPI, Uvicorn, Pydantic
* **Machine Learning & NLP:** Scikit-learn (TF-IDF Vectorization, K-Means Clustering $k=3$)
* **Data Processing:** Pandas, NumPy
* **Statistical Testing:** SciPy (`scipy.stats.binomtest`, `scipy.stats.chi2_contingency`, `scipy.stats.ttest_rel`)
* **AI Evaluators:** Local Ollama (`qwen3.5:4b` / `llama3`), Cloud API endpoints, and Deterministic Qualification Simulator
* **Frontend:** HTML5, CSS3 (Dark/Light Themes), Vanilla JavaScript (ES6+)

---

## 📡 5. REST API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/health` | `GET` | System health check and Ollama service discovery |
| `/api/jobs` | `GET/POST` | List standard job templates or register custom requirements |
| `/api/candidates` | `GET/POST` | Fetch candidate pool with precomputed qualification scores |
| `/api/skill-analysis` | `POST` | Calculate matched, missing, additional skills and skill gap % |
| `/api/qualification-score`| `POST` | Calculate weighted multi-component qualification score |
| `/api/evaluate` | `POST` | Run AI hiring recommendation, explanation, EFS, and BGI |
| `/api/bgi` | `POST` | Compute Bias/Behavioral Gap Index |
| `/api/efs` | `POST` | Compute Explanation Faithfulness Score |
| `/api/counterfactual` | `POST` | Execute controlled qualification intervention & invariance check |
| `/api/mitigation` | `POST` | Execute Before vs After Prompt Mitigation Feedback Loop |
| `/api/batch-evaluate` | `POST` | Audit complete candidate pool against target job requirements |
| `/api/cluster` | `POST` | Cluster candidates using TF-IDF + K-Means on skill vectors |
| `/api/report/{candidate_id}` | `GET` | Generate full individual candidate audit dossier |

---

## 💻 6. Installation & Execution

### 1. Quick Start (Windows Batch)
Double-click `run_complete_system.bat` or `launch_hiring_system.bat` to launch the server and open the web dashboard at `http://127.0.0.1:8000`.

### 2. Manual Command Line
```powershell
# Activate Python virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Automated Test Suite (23/23 Tests)
python -m pytest

# Run Complete CLI Demonstration Pipeline
python main.py all

# Start FastAPI Application
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🎬 7. 5-Minute Project Demonstration Script (For Viva / Panel)

1. **Step 1: Dashboard Overview (Tab 1)**
   - Show the active Job Role (`Senior Python Backend Engineer`), required/preferred skills cloud, and real-time KPI cards (Avg Qual Score: 84.5%, Mean EFS: 92.4, Mean BGI: 14.8).
2. **Step 2: Candidate Pool & Semantic Clustering (Tab 2)**
   - Click **"Semantic Clustering (TF-IDF + K-Means)"** to show skill-based candidate partitioning.
   - Click candidate `SWE_001` (Priya Sharma). Show the detailed **Selected Candidate Card** with matched required skills (Python, SQL, REST API, Git, PostgreSQL) and 89.8% qualification score.
3. **Step 3: Qualification Counterfactual Playground (Tab 3)**
   - Click **"Test in Qualification Counterfactual Playground"**.
   - Ablate a core skill (`Remove Core Skill: Python`).
   - Click **"Execute Causal Evaluation"**. Show how the AI adjusts decision from `STRONG_HIRE` to `INTERVIEW` with **Monotonic Consistency** and $100\%$ Explanation Faithfulness.
4. **Step 4: Mitigation Feedback Loop (Tab 4)**
   - Click **"Execute Mitigation & Re-evaluation"**. Show the Before vs After comparison and empirical BGI reduction ($82.8\%$ gap improvement).
5. **Step 5: Interactive API Console (Tab 6)**
   - Select `/api/evaluate` or `/api/skill-analysis` and click **"Send API Request"** to showcase the live REST API response for external ATS integration.

---

## ⚖️ 8. Academic & Research Contribution
* **Decoupled Qualification Grounding:** Eliminates subjective or demographic bias by evaluating resumes against formal job requirement criteria.
* **Explanation Faithfulness (EFS):** Quantifies whether AI justifications truthfully reflect candidate merits rather than generating deceptive post-hoc excuses.
* **Behavioral Gap Index (BGI):** Establishes an empirical metric to audit, detect, and mitigate inconsistencies in AI decision-making.
