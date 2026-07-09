# CV Chacha — Multi-Agent Resume Analyzer Wiki

## Overview

CV Chacha is a multi-agent resume intelligence platform that uses 12 specialized LangGraph agents to analyze resumes against job descriptions. It provides ATS scoring, recruiter & hiring manager reviews, skill gap analysis, truthfulness validation, resume rewriting, interview preparation, and selection probability estimation — all with a 3-tier LLM fallback system (Groq → HuggingFace → Ollama).

---

## Architecture

### System Architecture

![System Architecture](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/diagrams/System%20Architecture%20-%20White%20Background.png)

*High-level overview of the backend, frontend, agent pipeline, and database layers.*

### LangGraph Workflow

![LangGraph Workflow](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/diagrams/Langgraph%20workflow%20-%20white%20background.png)

*Sequential 12-agent pipeline with typed state passing and error isolation.*

### Agent Communication

![Agent Communication](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/diagrams/Agent%20Communication.png)

*How agents read from and write to the shared AgentState during execution.*

```
Resume + JD
    |
    v
+-------+--------+--------+---------+--------+-----------+---------+---------+--------+---------+---------+---------+
|  ATS  | Recr.  |   HM   |  Sim.   |  Skill | Truthful | Company | Salary | Rewrite|  Intrv. | Famous | Select. |
|Score  | Review | Review | 3 Pers. |  Gap   | -ness    |Research | Est.   |  STAR  |  Prep   |  Qs    | Prob.   |
|(Rule) | (LLM)  | (LLM)  | (LLM)   | (LLM)  | (LLM)    | (LLM)   | (LLM)  | (LLM)  | (LLM)   | (LLM)  | (LLM)   |
+-------+--------+--------+---------+--------+-----------+---------+---------+--------+---------+---------+---------+
```

### Key Design Decisions

- **Sequential execution** — each agent reads results from prior agents for richer context
- **Error isolation** — every agent is wrapped in try/except; one failure never crashes the pipeline
- **Typed state passing** — `AgentState` TypedDict shared across all nodes
- **Progress tracking** — in-memory store (`services/progress_store.py`) allows frontend to poll incremental results

---

## Login & Dashboard

| | |
|---|---|
| ![Main Login Page](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Main%20Login%20Page.png) | ![Login Page after login](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Login%20Page%20after%20login.png) |

The app uses JWT-based authentication with bcrypt password hashing. Users register, log in, and receive access + refresh tokens. The super admin can manage users from the admin panel.

| | |
|---|---|
| ![Dashboard](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Dashboard%20Page.png) | ![Sidebar](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Sidebar.png) |

The dashboard shows model capabilities, agent pipeline status, and quick action buttons. The sidebar provides navigation to all 16 pages.

---

## Agent Breakdown

### 1. ATS Scoring Engine (`agents/ats_agent.py`)
- **Type:** Rule-based (zero API cost, deterministic)
- **Scales:** 7 weighted categories — Keyword Match (30%), Skill Match (20%), Experience (15%), Projects (15%), Achievements (10%), Education (5%), Formatting (5%)
- **Output:** `overall_score` (0-100), `category_label`, per-category `breakdown`, `evidence` array

### 2. ATS Analysis

![ATS Analysis](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/ATS%20Analysis.png)

![ATS Analysis - Part 2](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/ATS%20Analysis%20-%20Part-2.png)

The ATS page displays the overall score with a gauge chart, per-category breakdown with evidence trail, and animated score reveal.

### 3. Recruiter Review (`agents/recruiter_agent.py`)
- **Type:** LLM
- **Evaluates:** Readability, impact, action-verb density, leadership signals, communication clarity
- **Output:** `recruiter_score` (0-100), `decision` (PASS/REJECT), `confidence`, `reasoning`

![Recruiter Review](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Recruiter%20Review.png)

### 4. Hiring Manager Review (`agents/hiring_manager_agent.py`)
- **Type:** LLM
- **Evaluates:** Technical depth, project complexity, domain expertise, growth trajectory
- **Output:** `hiring_manager_score` (0-100), `decision` (PASS/REJECT), `reasoning`

| | |
|---|---|
| ![Hiring Manager Part 1](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Hiring%20Manger%20Part-1.png) | ![Hiring Manager Part 2](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Hiring%20Manager%20Part%202.png) |

### 5. Recruiter Simulator (`agents/simulator_agent.py`)
- **Type:** 3 LLM calls in one node
- **Personas:** ATS (keyword compliance), HR (communication/leadership), Engineering Manager (technical depth)
- **Output:** Per-persona `decision` + `confidence`, aggregated `overall_decision`

| | |
|---|---|
| ![Simulator Part 1](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Recruiter%20Simulator-Part-1.png) | ![Simulator Part 2](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Recruiter%20Simulator%20-2.png) |
| ![Simulator Part 3](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Recruiter%20Simulator%20-3.png) | |

### 6. Skill Gap Analysis (`agents/skill_gap_agent.py`)
- **Type:** LLM
- **Compares:** Resume skills against JD requirements
- **Output:** Required/preferred skills (present/missing), `gap_severity`, `suggested_additions`

| | |
|---|---|
| ![Skill Gap 1](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Skill%20Gap%20-1.png) | ![Skill Gap 2](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Skill%20Gap%20-2.png) |
| ![Skill Gap 3](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Skill%20Gap%20-3.png) | ![Skill Gap After Fix](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Skill%20Gap%20Analysis%20-%20After%20Fixing%20Resume%20according%20to%20some%20recommendation.png) |

### 7. Truthfulness Validation (`agents/truthfulness_agent.py`)
- **Type:** LLM
- **Checks:** Exaggerated or fabricated claims
- **Output:** `truthfulness_score`, `flagged_items` with classification (Safe / Needs Verification / Potentially Misleading)

### 8. Company Research (`agents/company_agent.py`)
- **Type:** LLM
- **Provides:** Culture fit, growth opportunities, red flags, employee review perspective (Glassdoor-style)
- **Output:** `culture_score`, `overall_suitability`, `pros`/`cons`, `work_life_balance`, `career_growth`

| | |
|---|---|
| ![Company Insights 1](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Company%20insights%20-1.png) | ![Company Insights 2](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Company%20insights%20-2.png) |

### 9. Salary Estimation (`agents/salary_agent.py`)
- **Type:** LLM
- **Estimates:** Expected salary range based on role × company × location
- **Output:** `salary_range`, `currency`, `confidence` (Low/Medium/High), `factors`

### 10. Resume Rewrite (STAR) (`agents/rewrite_agent.py`)
- **Type:** LLM
- **Purpose:** Generate optimized bullet points using STAR methodology
- **Output:** `rewritten_resume`, `suggestions_summary`
- **Constraint:** Content-only changes; never fabricates skills or experience

![Resume Optimizer](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Resume%20Optimizer.png)

### 11. Interview Prep (`agents/interview_agent.py`)
- **Type:** LLM
- **Coverage:** 6 categories — Technical, Management, Communication, Behavioral, Project, HR
- **Output:** Personalized `questions` array with `difficulty` levels

| | |
|---|---|
| ![Interview Prep](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Interview%20Preparation.png) | ![Interview with Project Link](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Interview%20Prep%20-%20with%20a%20project%20link.png) |

### 12. Famous Questions (`agents/famous_questions_agent.py`)
- **Type:** LLM
- **Purpose:** Company-specific famous interview questions (Amazon LPs, Google system design, etc.)
- **Output:** `questions` with `source`, `difficulty`, `round`

### 13. Selection Probability (`agents/selection_agent.py`)
- **Type:** LLM
- **Estimates:** Hiring likelihood across each funnel stage
- **Output:** `overall_probability`, `stage_probabilities`, `key_factors`, `recommendations`

---

## LLM Fallback Chain

![LLM Fallback Chain](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/diagrams/LLM%20Fallback.png)

1. **Groq Cloud** (tried first if `GROQ_API_KEY` is set) — llama-3.3-70b-versatile, free tier
2. **Hugging Face Inference API** (fallback when Groq unavailable)
3. **Ollama local** (last resort; default `qwen2.5:3b`, supports 0.5B/1.5B/3B)
4. **Graceful degradation** — agent returns `llm_scored: False` with `fallback_note`

Set `PREFER_OLLAMA=true` to promote Ollama to first fallback. GPU offloading via `OLLAMA_GPU_LAYERS`.

---

## AI Insights & Analytics

| | |
|---|---|
| ![AI Engineering Insights](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/AI%20engnieering%20insights.png) | ![Insights 2](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/insights-2.png) |
| ![Insights 3](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/insights-3.png) | ![Insights 4](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/insights-4.png) |

---

## Resume Tools

### Resume Generator

![Resume Generator](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Resume%20Generator.png)

### Resume Library (Encrypted Storage)

![Resume Library](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Resume%20Library.png)

Files uploaded to the resume library are encrypted at rest using Fernet symmetric encryption.

### Resume Vault (Saved Analysis Sessions)

| | |
|---|---|
| ![Resume Vault](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Resume%20Vault.png) | ![Vault Analytics](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Vault%20Analytics.png) |
| ![Vault Analytics 2](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/vault%20analytics%20-2.png) | ![Vault Analytics 3](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/vault%20analytics%20-3.png) |

### Resume Version Comparison

| | |
|---|---|
| ![Resume Version](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Resume%20Version.png) | ![Resume Version 1](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/resume%20version-1.png) |
| ![Resume Version 2](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/resume%20version%20-2.png) | ![Version Comparison](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Resumer%20Version%20Comparison.png) |
| ![Manual Compare](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Resum%20Version-Manual%20Compare.png) | |

---

## Resume Chatbot (RAG)

| | |
|---|---|
| ![Chatbot 1](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/resume%20chatbot%20-1.png) | ![Chatbot 2](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/resume%20chatbot%20-2.png) |
| ![Chatbot 3](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Resume%20Chatbot-3.png) | |

The chatbot uses a RAG pipeline — ChromaDB vector store + BGE embeddings + cross-encoder reranking — to answer questions about the analyzed resume.

---

## Admin Dashboard

| | |
|---|---|
| ![Admin Dashboard](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Admin%20Dashboard.png) | ![Security Status](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/screenshots/Admin%20Dashboard%20-%20Security%20Status.png) |

The admin panel provides user management (create, disable, delete), audit log viewer, rate-limit monitoring, and security status overview.

---

## Tech Stack

![RAG Pipeline](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/diagrams/Rag%20Pipeline.png)

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit (16 pages, custom warm-canvas theme) |
| Agent Framework | LangGraph (StateGraph) |
| Vector Store | ChromaDB + BGE embeddings + cross-encoder reranking |
| Authentication | JWT (python-jose) + bcrypt |
| Database | SQLAlchemy + SQLite (aiosqlite) |
| LLM Providers | Groq, HuggingFace, Ollama |
| OCR | Tesseract + PyMuPDF |
| Visualization | Plotly, Streamlit-Aggrid |

---

## Quick Start

![Resume Analysis Flow](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/diagrams/Resume%20Analysis%20FLow.png)

```bash
git clone https://github.com/batramayank106/Multi-Agent-Resume-Analyzer.git
cd Multi-Agent-Resume-Analyzer
pip install -r requirements.txt
cp .env.example .env

# Start backend
python run.py backend

# Start frontend (separate terminal)
python run.py frontend
```

Open **http://localhost:8501**.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HF_API_KEY` | No | — | HuggingFace Inference API key |
| `GROQ_API_KEY` | No | — | Groq Cloud API key |
| `PREFER_OLLAMA` | No | `false` | Promote Ollama before HF |
| `OLLAMA_GPU_LAYERS` | No | `0` | GPU offloading layers |
| `JWT_SECRET` | No | auto-generated | JWT signing secret |
| `DATABASE_URL` | No | `sqlite:///cv_chacha.db` | Database connection |

---

## API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Current user info |
| POST | `/api/auth/logout` | Invalidate session |

### Analysis
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/analysis/full` | Run full 12-agent analysis |
| POST | `/api/analysis/stream` | Stream analysis with progress |
| GET | `/api/analysis/status/{run_id}` | Poll analysis progress |

### Vault
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/vault/sessions` | List saved sessions |
| DELETE | `/api/vault/sessions/{id}` | Delete session |

### Other
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/compare/resumes` | Compare two resume versions |
| POST | `/api/llm/chat` | Chat with CV Chacha assistant |
| POST | `/api/llm/rag-chat` | RAG-enhanced chat |
| POST | `/api/library/upload` | Upload resume file |
| GET | `/api/library/files` | List library files |

---

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Overview, quick actions |
| ATS Analysis | `/ats` | Upload resume + JD, run analysis |
| Recruiter Review | `/recruiter` | Recruiter score details |
| HM Review | `/hm` | Hiring manager score details |
| Simulator | `/simulator` | 3-persona review simulation |
| Skill Gap | `/skill-gap` | Missing skills analysis |
| Truthfulness | `/truthfulness` | Claim validation results |
| Company Insights | `/company` | Company research & culture |
| Salary Estimator | `/salary` | Salary range estimation |
| Rewrite | `/rewrite` | STAR-optimized resume |
| Interview Prep | `/interview` | Generated interview questions |
| AI Insights | `/ai-insights` | Agent confidence & reasoning |
| Vault | `/vault` | Saved analysis sessions |
| Analytics | `/analytics` | Cross-session trends & averages |
| Versions | `/versions` | Resume version history |
| Generator | `/generator` | Export reports (TXT, DOCX, LaTeX) |

---

## Database Schema

![ER Diagram](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/diagrams/ER%20Diagram.png)

![Database Design](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/diagrams/Database%20Design.png)

---

## Security Architecture

![Security Middleware](https://raw.githubusercontent.com/batramayank106/Multi-Agent-Resume-Analyzer/main/diagrams/Security%20Middlewarw.png)

---

## Run Commands

```bash
python run.py all         # Start both services in separate windows
python run.py backend     # Start backend only (same terminal)
python run.py frontend    # Start frontend only (same terminal)
python run.py kill        # Stop both services
python run.py status      # Check running services
```

Or use Docker:
```bash
docker compose up --build
```

---

## License

MIT License — see [LICENSE](LICENSE).

---

*Generated by CV Chacha — https://github.com/batramayank106/Multi-Agent-Resume-Analyzer*
