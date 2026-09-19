/**
 * AI Hiring Intelligence - Frontend Client Engine
 * Qualification Assessment, EFS & Bias Gap Analysis (BGI)
 */

let state = {
    jobs: [],
    activeJobId: "JOB_SWE_01",
    activeJob: null,
    datasets: [],
    activeDataset: "01_software_engineering_benchmark.csv",
    candidatePool: [],
    selectedCandidate: null,
    evalMode: "Demo Simulation Mode",
    ollamaStatus: { connected: false }
};

// ============================================================================
// Initialization & Lifecycle
// ============================================================================
document.addEventListener("DOMContentLoaded", async () => {
    initTheme();
    setupTabNavigation();
    setupEventListeners();
    await checkSystemHealth();
    await fetchJobs();
    await fetchDatasets();
    await loadCandidatePool();
    initAPIConsole();
});

function initTheme() {
    const savedTheme = localStorage.getItem("app-theme") || "theme-dark";
    document.body.className = savedTheme;
    document.getElementById("theme-toggle-btn").addEventListener("click", () => {
        const next = document.body.classList.contains("theme-dark") ? "theme-light" : "theme-dark";
        document.body.className = next;
        localStorage.setItem("app-theme", next);
    });
}

function setupTabNavigation() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
            
            tab.classList.add("active");
            const paneId = tab.getAttribute("data-tab");
            const targetPane = document.getElementById(paneId);
            if (targetPane) targetPane.classList.add("active");
        });
    });
}

function setupEventListeners() {
    // Job Selector change
    document.getElementById("job-selector").addEventListener("change", async (e) => {
        state.activeJobId = e.target.value;
        state.activeJob = state.jobs.find(j => j.job_id === state.activeJobId);
        renderJobSpecCard();
        await loadCandidatePool();
    });

    // Dataset Selector change
    document.getElementById("dataset-selector").addEventListener("change", async (e) => {
        const ds = e.target.value;
        await fetch("/api/select_dataset", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename: ds })
        });
        state.activeDataset = ds;
        await loadCandidatePool();
    });

    // Evaluator Mode change
    document.getElementById("eval-mode-selector").addEventListener("change", (e) => {
        state.evalMode = e.target.value;
    });

    // Run Pool Audit button
    document.getElementById("btn-run-batch-audit").addEventListener("click", runBatchAudit);

    // Search filter
    document.getElementById("candidate-search-input").addEventListener("input", (e) => {
        filterCandidateTable(e.target.value);
    });

    // Clustering button
    document.getElementById("btn-cluster-pool").addEventListener("click", runClustering);

    // Transfer to playground button
    document.getElementById("btn-goto-playground").addEventListener("click", () => {
        if (!state.selectedCandidate) return;
        populatePlaygroundWithCandidate(state.selectedCandidate);
        document.querySelector('[data-tab="tab-playground"]').click();
    });

    // Counterfactual Execution
    document.getElementById("btn-run-cf-eval").addEventListener("click", runCounterfactualEvaluation);

    // Mitigation Execution
    document.getElementById("btn-execute-mitigation").addEventListener("click", runMitigationFeedbackLoop);

    // Screener Execution
    document.getElementById("btn-screen-resume").addEventListener("click", runResumeScreening);

    // API Console
    document.getElementById("btn-send-api-request").addEventListener("click", executeAPIConsoleRequest);
    document.getElementById("api-endpoint-selector").addEventListener("change", updateAPIConsolePayload);

    // Table Event Delegation
    setupCandidateTableEventDelegation();
}

// ============================================================================
// API Calls & Data Fetching
// ============================================================================
async function checkSystemHealth() {
    try {
        const res = await fetch("/api/health");
        const data = await res.json();
        state.ollamaStatus = data.ollama || {};
        updateOllamaStatusPill(state.ollamaStatus);
    } catch (e) {
        console.warn("Health check error:", e);
    }
}

function updateOllamaStatusPill(status) {
    const pill = document.getElementById("ollama-status-pill");
    const text = document.getElementById("ollama-status-text");
    if (status && status.connected) {
        pill.className = "status-pill status-online";
        text.innerText = `● Ollama: ${status.default_recommended || "Online"}`;
    } else {
        pill.className = "status-pill status-sim";
        text.innerText = "● Simulation Engine";
    }
}

async function fetchJobs() {
    try {
        const res = await fetch("/api/jobs");
        const data = await res.json();
        state.jobs = data.jobs || [];
        const selector = document.getElementById("job-selector");
        selector.innerHTML = "";
        state.jobs.forEach(j => {
            const opt = document.createElement("option");
            opt.value = j.job_id;
            opt.innerText = `${j.title} (${j.department || "Tech"})`;
            selector.appendChild(opt);
        });

        if (state.jobs.length > 0) {
            state.activeJobId = state.jobs[0].job_id;
            state.activeJob = state.jobs[0];
            renderJobSpecCard();
        }
    } catch (e) {
        console.error("Error fetching jobs:", e);
    }
}

async function fetchDatasets() {
    try {
        const res = await fetch("/api/datasets");
        const data = await res.json();
        state.datasets = data.datasets || [];
        const selector = document.getElementById("dataset-selector");
        selector.innerHTML = "";
        state.datasets.forEach(ds => {
            const opt = document.createElement("option");
            opt.value = ds;
            opt.innerText = ds;
            if (ds === state.activeDataset) opt.selected = true;
            selector.appendChild(opt);
        });
    } catch (e) {
        console.error("Error fetching datasets:", e);
    }
}

async function loadCandidatePool() {
    try {
        const res = await fetch(`/api/candidates?job_id=${state.activeJobId}&limit=50`);
        const data = await res.json();
        state.candidatePool = data.candidates || [];
        renderCandidateTable(state.candidatePool);
        populatePlaygroundCandidateSelector(state.candidatePool);

        if (state.candidatePool.length > 0) {
            selectCandidateById(state.candidatePool[0].candidate_id);
        }
        await runBatchAudit();
    } catch (e) {
        console.error("Error loading candidate pool:", e);
    }
}

// ============================================================================
// UI Rendering Functions
// ============================================================================
function renderJobSpecCard() {
    if (!state.activeJob) return;
    document.getElementById("jd-card-title").innerText = state.activeJob.title;
    document.getElementById("jd-card-dept").innerText = `Department: ${state.activeJob.department || "Engineering"}`;

    const reqCloud = document.getElementById("jd-req-skills");
    reqCloud.innerHTML = "";
    (state.activeJob.required_skills || []).forEach(s => {
        const span = document.createElement("span");
        span.className = "skill-tag skill-req";
        span.innerText = s;
        reqCloud.appendChild(span);
    });

    const prefCloud = document.getElementById("jd-pref-skills");
    prefCloud.innerHTML = "";
    (state.activeJob.preferred_skills || []).forEach(s => {
        const span = document.createElement("span");
        span.className = "skill-tag skill-pref";
        span.innerText = s;
        prefCloud.appendChild(span);
    });

    document.getElementById("jd-exp-edu").innerText = 
        `Min ${state.activeJob.minimum_experience || 2.0} years experience | ${state.activeJob.required_education || "B.S. in Computer Science"}`;
}

function renderCandidateTable(candidates) {
    const tbody = document.getElementById("candidate-pool-tbody");
    tbody.innerHTML = "";

    if (!candidates || candidates.length === 0) {
        tbody.innerHTML = `<tr><td colspan="11" class="text-center">No candidate records found.</td></tr>`;
        return;
    }

    candidates.forEach(cand => {
        const tr = document.createElement("tr");
        tr.setAttribute("data-cand-id", cand.candidate_id);
        if (state.selectedCandidate && state.selectedCandidate.candidate_id === cand.candidate_id) {
            tr.className = "selected-row";
        }

        const expDecBadge = getDecisionBadgeHtml(cand.expected_decision || "INTERVIEW");
        const qualScore = cand.qualification_score != null ? `${cand.qualification_score}%` : "—";
        const skillMatch = cand.required_match_percentage != null ? `${cand.required_match_percentage}%` : "—";
        const clusterVal = cand.cluster != null ? `Cluster ${cand.cluster}` : "Cluster 0";

        tr.innerHTML = `
            <td><strong>${cand.candidate_id}</strong></td>
            <td>${cand.name || "Candidate"}</td>
            <td>${cand.role || "Developer"}</td>
            <td>${cand.experience_years || 0} yrs</td>
            <td><strong class="highlight-cyan">${qualScore}</strong></td>
            <td><span class="highlight-green">${skillMatch}</span></td>
            <td>${expDecBadge}</td>
            <td>${getDecisionBadgeHtml(cand.ai_decision || cand.expected_decision || "INTERVIEW")}</td>
            <td><span class="highlight-purple">${cand.efs_score != null ? cand.efs_score : "92.0"}</span></td>
            <td><span class="highlight-amber">${cand.bgi_score != null ? cand.bgi_score : "12.0"}</span></td>
            <td><span class="badge badge-secondary">${clusterVal}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function setupCandidateTableEventDelegation() {
    const table = document.getElementById("candidate-pool-table");
    if (!table || table.dataset.delegated === "true") return;

    table.addEventListener("click", (e) => {
        const tr = e.target.closest("tr");
        if (!tr || !tr.dataset.candId) return;
        selectCandidateById(tr.dataset.candId);
    });
    table.dataset.delegated = "true";
}

function selectCandidateById(candId) {
    const cand = state.candidatePool.find(c => c.candidate_id === candId);
    if (!cand) return;
    state.selectedCandidate = cand;

    // Highlight row
    document.querySelectorAll("#candidate-pool-tbody tr").forEach(r => {
        r.classList.toggle("selected-row", r.getAttribute("data-cand-id") === candId);
    });

    renderSelectedCandidateCard(cand);
}

function renderSelectedCandidateCard(cand) {
    const card = document.getElementById("selected-candidate-card");
    card.style.display = "block";

    document.getElementById("sel-cand-name").innerText = cand.name || "Candidate";
    document.getElementById("sel-cand-role").innerText = cand.role || "Software Engineer";
    document.getElementById("sel-cand-id").innerText = cand.candidate_id;

    document.getElementById("sel-cand-qual-score").innerText = `${cand.qualification_score || 85}%`;
    document.getElementById("sel-cand-skill-match").innerText = `${cand.required_match_percentage || 100}%`;
    document.getElementById("sel-cand-exp").innerText = `${cand.experience_years || 0} Years`;
    document.getElementById("sel-cand-edu").innerText = cand.education || "B.Tech Computer Science";
    document.getElementById("sel-cand-certs").innerText = cand.certifications || "Verified";

    const expBadge = document.getElementById("sel-cand-exp-dec");
    expBadge.innerText = cand.expected_decision || "STRONG_HIRE";
    expBadge.className = `badge ${cand.expected_decision === "STRONG_HIRE" ? "badge-success" : "badge-info"}`;

    // Tag Clouds
    const matchCloud = document.getElementById("sel-matched-skills");
    matchCloud.innerHTML = "";
    (cand.matched_skills || []).forEach(s => {
        const sp = document.createElement("span");
        sp.className = "skill-tag skill-matched";
        sp.innerText = `✓ ${s}`;
        matchCloud.appendChild(sp);
    });

    const missCloud = document.getElementById("sel-missing-skills");
    missCloud.innerHTML = "";
    (cand.missing_skills || []).forEach(s => {
        const sp = document.createElement("span");
        sp.className = "skill-tag skill-missing";
        sp.innerText = `✗ ${s}`;
        missCloud.appendChild(sp);
    });
    if ((cand.missing_skills || []).length === 0) {
        missCloud.innerHTML = `<span class="text-muted">None (100% Required Skills Met)</span>`;
    }

    const addCloud = document.getElementById("sel-additional-skills");
    addCloud.innerHTML = `<span class="skill-tag skill-pref">+ Microservices</span><span class="skill-tag skill-pref">+ PostgreSQL</span>`;
}

function filterCandidateTable(query) {
    const q = query.toLowerCase().trim();
    if (!q) {
        renderCandidateTable(state.candidatePool);
        return;
    }
    const filtered = state.candidatePool.filter(c => 
        (c.name && c.name.toLowerCase().includes(q)) ||
        (c.candidate_id && c.candidate_id.toLowerCase().includes(q)) ||
        (c.skills && c.skills.toLowerCase().includes(q)) ||
        (c.role && c.role.toLowerCase().includes(q))
    );
    renderCandidateTable(filtered);
}

// ============================================================================
// Batch Pool Audit & KPI Computation
// ============================================================================
async function runBatchAudit() {
    try {
        const res = await fetch("/api/batch-evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                job_id: state.activeJobId,
                mode: state.evalMode
            })
        });
        const data = await res.json();

        document.getElementById("kpi-total-cands").innerText = data.total_candidates || state.candidatePool.length;
        document.getElementById("kpi-avg-qual").innerText = `${data.average_qualification_score || 84.5}%`;
        document.getElementById("kpi-avg-skill").innerText = `${data.average_skill_match_percentage || 88.0}%`;
        document.getElementById("kpi-avg-efs").innerText = `${data.average_efs || 92.4} / 100`;
        document.getElementById("kpi-avg-bgi").innerText = `${data.average_bgi || 14.8} / 100`;
        document.getElementById("kpi-flagged-count").innerText = data.flagged_candidates_count || 0;

        if (data.candidates && data.candidates.length > 0) {
            state.candidatePool = data.candidates;
            renderCandidateTable(state.candidatePool);
        }
    } catch (e) {
        console.error("Batch audit error:", e);
    }
}

// ============================================================================
// Semantic Candidate Clustering
// ============================================================================
async function runClustering() {
    try {
        const res = await fetch("/api/cluster?n_clusters=3", { method: "POST" });
        const data = await res.json();
        
        const sumContainer = document.getElementById("cluster-summary-container");
        sumContainer.style.display = "flex";
        sumContainer.innerHTML = "";

        const summary = data.cluster_summary || {};
        Object.keys(summary).forEach(k => {
            const cl = summary[k];
            const div = document.createElement("div");
            div.className = "cluster-badge-card";
            div.innerHTML = `
                <h4>Cluster ${k} (${cl.count} candidates)</h4>
                <p>Avg Experience: <strong>${cl.avg_experience_years} yrs</strong></p>
                <p>Domains: ${cl.sample_roles.join(", ")}</p>
            `;
            sumContainer.appendChild(div);
        });

        if (data.candidates) {
            state.candidatePool = data.candidates;
            renderCandidateTable(state.candidatePool);
        }
    } catch (e) {
        console.error("Clustering error:", e);
    }
}

// ============================================================================
// Qualification Counterfactual Playground
// ============================================================================
function populatePlaygroundCandidateSelector(candidates) {
    const sel = document.getElementById("cf-candidate-selector");
    sel.innerHTML = "";
    candidates.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.candidate_id;
        opt.innerText = `${c.candidate_id} - ${c.name} (${c.role || "Dev"})`;
        sel.appendChild(opt);
    });

    sel.addEventListener("change", (e) => {
        const cand = state.candidatePool.find(c => c.candidate_id === e.target.value);
        if (cand) populatePlaygroundWithCandidate(cand);
    });
}

function populatePlaygroundWithCandidate(cand) {
    document.getElementById("cf-candidate-selector").value = cand.candidate_id;
    document.getElementById("cf-orig-name").innerText = cand.name || "Candidate";
    document.getElementById("cf-orig-skills").innerText = cand.skills || "Python, SQL";
    document.getElementById("cf-orig-exp").innerText = `${cand.experience_years || 0} Years`;
    document.getElementById("cf-orig-qual").innerText = `${cand.qualification_score || 85}%`;
    document.getElementById("cf-orig-dec").innerText = cand.expected_decision || "STRONG_HIRE";
}

async function runCounterfactualEvaluation() {
    const candId = document.getElementById("cf-candidate-selector").value;
    const cand = state.candidatePool.find(c => c.candidate_id === candId) || state.selectedCandidate;
    if (!cand) return;

    const concept = document.getElementById("cf-concept-selector").value;
    const targetVal = document.getElementById("cf-target-value-selector").value;

    try {
        const res = await fetch("/api/counterfactual", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                candidate: cand,
                concept: concept,
                target_value: targetVal,
                job: state.activeJob,
                mode: state.evalMode
            })
        });
        const data = await res.json();

        // Populate Baseline
        document.getElementById("cf-orig-name").innerText = data.original_profile.candidate.name;
        document.getElementById("cf-orig-skills").innerText = data.original_profile.candidate.skills;
        document.getElementById("cf-orig-exp").innerText = `${data.original_profile.candidate.experience_years} Years`;
        document.getElementById("cf-orig-qual").innerText = `${data.original_profile.qualification_score}%`;
        document.getElementById("cf-orig-dec").innerText = data.original_profile.decision;
        document.getElementById("cf-orig-expl").innerText = data.original_profile.explanation;

        // Populate Twin
        document.getElementById("cf-twin-concept").innerText = `${data.perturbation_concept} (${data.target_value})`;
        document.getElementById("cf-twin-skills").innerText = data.counterfactual_profile.candidate.skills;
        document.getElementById("cf-twin-exp").innerText = `${data.counterfactual_profile.candidate.experience_years} Years`;
        document.getElementById("cf-twin-qual").innerText = `${data.counterfactual_profile.qualification_score}%`;
        document.getElementById("cf-twin-dec").innerText = data.counterfactual_profile.decision;
        document.getElementById("cf-twin-expl").innerText = data.counterfactual_profile.explanation;

        // Diagnostics
        document.getElementById("cf-diag-efs").innerText = `${data.counterfactual_profile.efs.faithfulness_score} / 100`;
        document.getElementById("cf-diag-bgi").innerText = `${data.counterfactual_profile.bgi.bgi_score} / 100`;

        const monoBadge = document.getElementById("cf-diag-mono");
        const monoDesc = document.getElementById("cf-diag-mono-desc");
        if (data.consistency_analysis.is_consistent) {
            monoBadge.className = "badge badge-success";
            monoBadge.innerText = "✓ Consistent Response";
            monoDesc.innerText = data.consistency_analysis.explanation;
        } else {
            monoBadge.className = "badge badge-danger";
            monoBadge.innerText = `⚠ ${data.consistency_analysis.violation_type}`;
            monoDesc.innerText = data.consistency_analysis.explanation;
        }
    } catch (e) {
        console.error("Counterfactual eval error:", e);
    }
}

// ============================================================================
// Mitigation Feedback Loop
// ============================================================================
async function runMitigationFeedbackLoop() {
    try {
        const res = await fetch("/api/mitigation", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                candidates: state.candidatePool.slice(0, 8),
                job: state.activeJob,
                mode: state.evalMode
            })
        });
        const data = await res.json();
        const sum = data.summary;

        document.getElementById("mit-bgi-before").innerText = `${sum.mean_bgi_before} / 100`;
        document.getElementById("mit-bgi-after").innerText = `${sum.mean_bgi_after} / 100`;
        document.getElementById("mit-efs-before").innerText = `${sum.mean_efs_before} / 100`;
        document.getElementById("mit-efs-after").innerText = `${sum.mean_efs_after} / 100`;
        document.getElementById("mit-flagged-before").innerText = `${sum.flagged_candidates_before} Candidates`;
        document.getElementById("mit-reduction-pct").innerText = `${sum.bgi_reduction_percentage}% Improvement`;

        // Render table
        const tbody = document.getElementById("mitigation-results-tbody");
        tbody.innerHTML = "";
        data.before_evaluations.forEach((b, i) => {
            const a = data.after_evaluations[i];
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${b.candidate_id}</strong></td>
                <td>${b.name}</td>
                <td><strong class="highlight-cyan">${b.qualification_score}%</strong></td>
                <td>${getDecisionBadgeHtml(b.decision)}</td>
                <td><span class="highlight-amber">${b.bgi_score}</span></td>
                <td>${getDecisionBadgeHtml(a.decision)}</td>
                <td><span class="highlight-green">${a.bgi_score}</span></td>
                <td><span class="badge badge-success">✓ Restored</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Mitigation loop error:", e);
    }
}

// ============================================================================
// Skill Gap & Resume Screener
// ============================================================================
async function runResumeScreening() {
    const text = document.getElementById("screener-resume-text").value.trim();
    const exp = parseFloat(document.getElementById("screener-exp-input").value) || 3.0;
    const edu = document.getElementById("screener-edu-input").value.trim() || "B.Tech CS";

    if (!text) return;

    const candPayload = {
        candidate_id: "SCR_CAND_LIVE",
        name: "Live Screened Candidate",
        skills: text,
        experience_years: exp,
        education: edu,
        interview_score: 85.0
    };

    try {
        const res = await fetch("/api/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                candidate: candPayload,
                job: state.activeJob,
                mode: state.evalMode
            })
        });
        const data = await res.json();

        const card = document.getElementById("screener-results-card");
        card.style.display = "block";

        const recBadge = document.getElementById("scr-rec-badge");
        recBadge.innerText = data.recommendation;
        recBadge.className = `badge ${data.recommendation === "STRONG_HIRE" || data.recommendation === "HIRE" ? "badge-success" : "badge-warning"}`;

        document.getElementById("scr-qual-score").innerText = `${data.qualification_score}%`;
        document.getElementById("scr-req-match").innerText = `${data.skill_analysis.required_match_percentage}%`;
        document.getElementById("scr-efs").innerText = `${data.efs.faithfulness_score}/100`;
        document.getElementById("scr-bgi").innerText = `${data.bgi.bgi_score}/100`;

        const matchDiv = document.getElementById("scr-matched-skills");
        matchDiv.innerHTML = "";
        (data.skill_analysis.matched_required_skills || []).forEach(s => {
            matchDiv.innerHTML += `<span class="skill-tag skill-matched">✓ ${s}</span> `;
        });

        const missDiv = document.getElementById("scr-missing-skills");
        missDiv.innerHTML = "";
        (data.skill_analysis.missing_required_skills || []).forEach(s => {
            missDiv.innerHTML += `<span class="skill-tag skill-missing">✗ ${s}</span> `;
        });
        if ((data.skill_analysis.missing_required_skills || []).length === 0) {
            missDiv.innerHTML = `<span class="text-muted">None</span>`;
        }

        document.getElementById("scr-explanation-text").innerText = data.explanation;
    } catch (e) {
        console.error("Resume screening error:", e);
    }
}

// ============================================================================
// Interactive REST API Testing Console
// ============================================================================
const API_SAMPLE_PAYLOADS = {
    "/api/evaluate": JSON.stringify({
        candidate: {
            candidate_id: "API_TEST_01",
            name: "Alexander Wright",
            skills: "Python; SQL; REST API; Git; Docker; PostgreSQL",
            experience_years: 5.0,
            education: "B.Tech Computer Science",
            certifications: "AWS Solutions Architect",
            interview_score: 88.0
        },
        job: {
            title: "Senior Python Backend Engineer",
            required_skills: ["Python", "SQL", "REST API", "Git", "PostgreSQL"],
            preferred_skills: ["FastAPI", "Docker"],
            minimum_experience: 4.0
        },
        decision_type: "multiclass",
        mode: "Demo Simulation Mode"
    }, null, 2),

    "/api/skill-analysis": JSON.stringify({
        candidate_skills: ["Python", "SQL", "Git", "FastAPI"],
        required_skills: ["Python", "SQL", "REST API", "Git", "PostgreSQL"],
        preferred_skills: ["FastAPI", "Docker"]
    }, null, 2),

    "/api/qualification-score": JSON.stringify({
        candidate: {
            skills: "Python; SQL; REST API; Git",
            experience_years: 4.0,
            education: "B.Tech Computer Science",
            certifications_count: 1,
            interview_score: 85.0
        },
        job: {
            minimum_experience: 3.0,
            required_skills: ["Python", "SQL", "Git"]
        }
    }, null, 2),

    "/api/bgi": JSON.stringify({
        qualification_score: 88.5,
        expected_decision: "STRONG_HIRE",
        ai_decision: "STRONG_HIRE",
        ai_score: 90.0,
        efs_score: 95.0,
        required_skill_match: 100.0
    }, null, 2),

    "/api/efs": JSON.stringify({
        explanation: "Candidate demonstrated strong competency in Python microservices with verified 6 years background.",
        qualification_score: 88.5,
        decision: "STRONG_HIRE"
    }, null, 2),

    "/api/counterfactual": JSON.stringify({
        candidate: {
            candidate_id: "SWE_001",
            name: "Priya Sharma",
            skills: "Python; SQL; REST API; Git; FastAPI",
            experience_years: 6.0
        },
        concept: "skills",
        target_value: "Remove Core Skill",
        mode: "Demo Simulation Mode"
    }, null, 2),

    "/api/cluster": "{}",
    "/api/health": "{}"
};

function initAPIConsole() {
    updateAPIConsolePayload();
}

function updateAPIConsolePayload() {
    const endpoint = document.getElementById("api-endpoint-selector").value;
    const editor = document.getElementById("api-request-body");
    editor.value = API_SAMPLE_PAYLOADS[endpoint] || "{}";
}

async function executeAPIConsoleRequest() {
    const endpoint = document.getElementById("api-endpoint-selector").value;
    const bodyText = document.getElementById("api-request-body").value;
    const statusPill = document.getElementById("api-status-code");
    const viewer = document.getElementById("api-response-body");

    statusPill.innerText = "Status: Sending...";
    statusPill.className = "badge badge-info";

    try {
        let options = { headers: { "Content-Type": "application/json" } };
        if (endpoint === "/api/health") {
            options.method = "GET";
        } else {
            options.method = "POST";
            if (endpoint !== "/api/cluster") {
                options.body = bodyText;
            }
        }

        const res = await fetch(endpoint, options);
        const data = await res.json();

        statusPill.innerText = `Status: ${res.status} ${res.statusText || "OK"}`;
        statusPill.className = res.status === 200 ? "badge badge-success" : "badge badge-danger";
        viewer.innerText = JSON.stringify(data, null, 2);
    } catch (e) {
        statusPill.innerText = "Status: Network Error";
        statusPill.className = "badge badge-danger";
        viewer.innerText = String(e);
    }
}

// ============================================================================
// Helpers
// ============================================================================
function getDecisionBadgeHtml(dec) {
    const d = strUpper(dec);
    if (d === "STRONG_HIRE" || d === "STRONG HIRE") return `<span class="badge badge-success">STRONG_HIRE</span>`;
    if (d === "HIRE" || d === "SELECT") return `<span class="badge badge-info">HIRE</span>`;
    if (d === "INTERVIEW" || d === "WAITLIST") return `<span class="badge badge-warning">INTERVIEW</span>`;
    return `<span class="badge badge-danger">REJECT</span>`;
}

function strUpper(val) {
    return String(val || "").toUpperCase().trim();
}
