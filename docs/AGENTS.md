# Agent Architecture Guide

CV Chacha — by Mayank Batra orchestrates **12 specialized agents** in a sequential LangGraph `StateGraph` pipeline. Each agent receives the full shared state, contributes structured outputs, and is wrapped in try/except error isolation — no single agent failure can crash the pipeline. Agent progress is tracked via an in-memory progress store so the frontend can poll for incremental results.

---

## Pipeline Overview

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

### Execution Order

The pipeline is strictly sequential — each agent runs after the previous one completes. This design choice (over parallel execution) enables each agent to read results from prior agents, producing richer, context-aware outputs.

---

## AgentState (TypedDict)

Defined in `agents/graph.py`, the shared state passed between all nodes:

```python
class AgentState(TypedDict):
    resume_id: Optional[int]
    jd_id: Optional[int]
    resume_text: str
    jd_text: Optional[str]
    parsed_skills: list
    parsed_experience: list
    parsed_projects: list
    parsed_education: list
    parsed_achievements: list

    ats_result: Optional[dict]
    recruiter_result: Optional[dict]
    hiring_manager_result: Optional[dict]
    simulator_results: Optional[dict]
    skill_gap_result: Optional[dict]
    truthfulness_result: Optional[dict]
    company_result: Optional[dict]
    salary_result: Optional[dict]
    rewrite_result: Optional[dict]
    interview_result: Optional[dict]
    famous_questions_result: Optional[dict]
    selection_probability: Optional[dict]

    errors: list[str]
    status: str
    run_id: Optional[str]
```

Each agent writes to its corresponding `Optional[dict]` field and may append to `errors`. The `status` field tracks pipeline progress. The `run_id` field is set by `run_analysis_with_progress()` so the `_track()` wrapper can report progress per agent node.

---

## LLM Fallback Chain

The system uses a 3-provider priority chain:

1. **Groq Cloud** (tried first if `GROQ_API_KEY` is set) — llama-3.3-70b-versatile, 30 RPM, free
2. **Hugging Face Inference API** (fallback when Groq is unavailable)
3. **Ollama local inference** (last resort, after HF; `PREFER_OLLAMA=false`)
4. **Graceful degradation** — agent returns `llm_scored: False` with a user-facing `fallback_note`

Ollama models are loaded from `settings.ollama_model` (default: `qwen2.5:3b`). Supported sizes: 0.5B (fast), 1.5B (balanced), 3B (best quality). With `PREFER_OLLAMA=false`, Ollama is only tried after HF fails. Set `PREFER_OLLAMA=true` to promote Ollama to the first fallback.

### GPU Acceleration

Partial GPU offloading is supported via `OLLAMA_GPU_LAYERS` in `.env`. For 2GB VRAM GPUs (MX150, GTX 1050), use `OLLAMA_GPU_LAYERS=20` and the CUDA v12 backend. See `SETUP.md` for detailed GPU configuration.

---

## Agent 1: ATS Scoring Engine

**File:** `agents/ats_agent.py`

| Attribute | Detail |
|---|---|
| **Engine** | Rule-based (zero API cost, fully deterministic) |
| **Purpose** | Score resume against job description across 7 weighted categories |
| **Weights** | Keyword Match 30%, Skill Match 20%, Experience 15%, Project 15%, Achievements 10%, Education 5%, Formatting 5% |
| **Output** | `overall_score` (0-100), `category_label` (Poor/Average/Good/Strong/Exceptional), per-category `breakdown`, `evidence` array with itemized deductions |
| **Inputs read** | `resume_text`, `jd_text`, `parsed_skills`, `parsed_experience`, `parsed_projects`, `parsed_education`, `parsed_achievements` |
| **Outputs written** | `ats_result` |

**How it works:** Each category is scored independently using string matching and simple heuristics (e.g., keyword presence in lowercase text, number of experience entries, project count). The weighted average produces the final score. Every deduction includes the exact missing keyword, the JD context it appeared in, and the reason it was weighted.

**Error handling:** Returns `overall_score: 0` with error message in the result. The pipeline checks for errors and optionally routes to END (though current implementation continues through).

---

## Agent 2: Recruiter Review

**File:** `agents/recruiter_agent.py`

| Attribute | Detail |
|---|---|
| **Engine** | LLM (Groq → Ollama → HF) |
| **Purpose** | Evaluate resume from a recruiter's perspective — readability, impact, action-verb density, leadership signals, communication clarity |
| **Output** | `recruiter_score` (0-100), `decision` (PASS/REJECT), `confidence` (0-100), `reasoning` |
| **Inputs read** | `resume_text`, `jd_text` |
| **Outputs written** | `recruiter_result` |

**Error handling:** Returns `recruiter_score: 0` with error string on failure.

---

## Agent 3: Hiring Manager Review

**File:** `agents/hiring_manager_agent.py`

| Attribute | Detail |
|---|---|
| **Engine** | LLM |
| **Purpose** | Assess technical depth, project complexity, domain-specific expertise, and growth trajectory |
| **Output** | `hiring_manager_score` (0-100), `decision` (PASS/REJECT), `reasoning` |
| **Inputs read** | `resume_text`, `jd_text` |
| **Outputs written** | `hiring_manager_result` |

The prompt is engineered to mimic how actual hiring managers think — looking for specific technical signals rather than general polish.

**Error handling:** Returns `hiring_manager_score: 0` with error string.

---

## Agent 4: Recruiter Simulator (3 Personas)

**File:** `agents/simulator_agent.py`

| Attribute | Detail |
|---|---|
| **Engine** | LLM (3 independent calls in a single node) |
| **Purpose** | Simulate three distinct reviewers with different priorities |
| **Personas** | **ATS** (keyword compliance, formatting strictness), **HR** (communication, leadership, presentation), **Engineering Manager** (technical depth, project quality) |
| **Output** | Per-persona `decision` (PASS/CONDITIONAL/REJECT) and `confidence`, plus aggregated `overall_decision` and `overall_confidence` |
| **Inputs read** | `resume_text` |
| **Outputs written** | `simulator_results` |

**Aggregation logic:** If 2+ personas PASS, overall = PASS. If exactly 1 passes, overall = CONDITIONAL. Otherwise, REJECT.

**Error handling:** Returns error dict with `overall_decision: "REJECT"` and `overall_confidence: 0`.

---

## Agent 5: Skill Gap Analysis

**File:** `agents/skill_gap_agent.py`

| Attribute | Detail |
|---|---|
| **Engine** | LLM |
| **Purpose** | Compare resume skills against JD requirements and classify gaps |
| **Output** | Required skills present, required skills missing, preferred skills present, preferred skills missing, `gap_severity` (low/medium/high/critical), `priority_levels`, `suggested_additions` (2-3 complementary skills not in the JD) |
| **Inputs read** | `parsed_skills`, `jd_text` |
| **Outputs written** | `skill_gap_result` |

**Error handling:** Returns error dict; severity defaults to `"high"`.

- **suggested_additions**: Recommends 2-3 complementary skills not in the JD that would strengthen the candidate's profile.

---

## Agent 6: Truthfulness Validation

**File:** `agents/truthfulness_agent.py`

| Attribute | Detail |
|---|---|
| **Engine** | LLM |
| **Purpose** | Critically examine claims for exaggeration or fabrication |
| **Output** | `truthfulness_score` (0-100), `flagged_items` array with classification (Safe / Needs Verification / Potentially Misleading) and reasoning |
| **Inputs read** | `resume_text` |
| **Outputs written** | `truthfulness_result` |

**Critical constraint:** The prompt explicitly forbids the model from claiming any skill or project exists. It can only flag what is in the text — never invent skills, projects, or experience.

**Error handling:** Returns error dict; score defaults to `50`.

---

## Agent 7: Company Research

**File:** `agents/company_agent.py`

| Attribute | Detail |
|---|---|
| **Engine** | LLM |
| **Purpose** | Extract company name from resume/JD and analyze culture fit, growth opportunities, red flags, employee reviews |
| **Output** | `company_name`, `overview`, `culture_fit_indicators`, `growth_opportunities`, `red_flags`, `overall_suitability` (POOR/FAIR/GOOD/EXCELLENT), `culture_score` (0-100), `review_summary`, `pros`, `cons`, `work_life_balance`, `career_growth` |
| **Inputs read** | `jd_text` |
| **Outputs written** | `company_result` |

The agent provides a Glassdoor-like employee review perspective: `culture_score`, `review_summary` with pros/cons, and ratings for work-life balance and career growth.

**Error handling:** Returns error dict; suitability defaults to `"FAIR"`.

---

## Agent 8: Salary Estimation

**File:** `agents/salary_agent.py`

| Attribute | Detail |
|---|---|
| **Engine** | LLM (Groq → Ollama → HF) |
| **Purpose** | Estimate expected salary range for the role × company × location |
| **Output** | `salary_range` (string), `currency`, `confidence` (Low/Medium/High), `factors` (array), `source`, `llm_scored` |
| **Inputs read** | `company_name` (from CompanyAgent), `jd_text`, `parsed_skills` |
| **Outputs written** | `salary_result` |
| **Pipeline position** | After `company_agent`, before `rewrite_agent` |
| **Frontend** | Salary Estimate card on Company Insights page |

**Error handling:** Returns `salary_range: "N/A"` with `llm_scored: False` on failure.

---

## Agent 9: Resume Rewrite (STAR Optimization)

**File:** `agents/rewrite_agent.py`

| Attribute | Detail |
|---|---|
| **Engine** | LLM |
| **Purpose** | Generate optimized bullet points using STAR methodology without altering template, layout, fonts, or structure |
| **Output** | `rewritten_resume` (full updated text), `suggestions_summary` |
| **Inputs read** | `resume_text`, all prior agent results (ATS gaps, recruiter feedback, skill gaps) for context-grounded suggestions |
| **Outputs written** | `rewrite_result` |

**Protection:** The prompt explicitly forbids fabricating skills, projects, employment history, or achievements. Content-only changes.

**Error handling:** Returns error dict; `rewritten_resume` defaults to original resume text.

---

## Agent 10: Interview Prep

**File:** `agents/interview_agent.py`

| Attribute | Detail |
|---|---|
| **Engine** | LLM |
| **Purpose** | Generate personalized interview questions across 6 categories (Technical, Management, Communication, Behavioral, Project, HR) |
| **Output** | `questions` array with `category`, `question`, `difficulty` (Easy/Medium/Hard), and `question_count` |
| **Inputs read** | `resume_text`, `jd_text` (provides company name, role, requirements) |
| **Outputs written** | `interview_result` |

The prompt explicitly requires at least 1-2 questions per category, ensuring balanced coverage. Questions reference specific projects, skills, and experiences from the resume. The prompt receives GitHub/portfolio links and detected role for personalization.

**Error handling:** Returns empty `questions` array with `question_count: 0`.

---

## Agent 11: Famous Interview Questions

**File:** `agents/famous_questions_agent.py`

| Attribute | Detail |
|---|---|
| **Engine** | LLM (Groq → Ollama → HF) |
| **Purpose** | Retrieve well-known interview questions from the target company (Amazon LPs, Google system design, Meta behavioral, etc.) |
| **Output** | `company`, `questions` array with `question`, `source`, `difficulty`, `round`, `question_count`, `llm_scored` |
| **Inputs read** | `company_name` (from CompanyAgent), `jd_text` |
| **Outputs written** | `famous_questions_result` |
| **Pipeline position** | After `interview_agent`, before `selection_agent` |
| **Frontend** | "Famous Questions" tab on Interview Prep page |

**Error handling:** Returns empty `questions` array with `question_count: 0` on failure.

---

## Agent 12: Selection Probability

**File:** `agents/selection_agent.py`

| Attribute | Detail |
|---|---|
| **Engine** | LLM |
| **Purpose** | Estimate hiring likelihood across each stage of the funnel |
| **Output** | `overall_probability` (0-100), `stage_probabilities` (dict with ATS Screen, Recruiter Shortlist, Technical Interview, Onsite, Offer), `key_factors`, `recommendations` |
| **Inputs read** | All prior agent scores (`ats_result`, `recruiter_result`, `hiring_manager_result`, `skill_gap_result`, `truthfulness_result`) |
| **Outputs written** | `selection_probability` |

**Error handling:** Returns error dict; `overall_probability` defaults to `0`.

---

## Error Isolation & Graceful Degradation

Every agent node in `agents/graph.py` is wrapped via the `_track()` factory, which reports progress to the in-memory store and captures errors:

```python
def _track(node_name: str, func):
    def wrapper(state: AgentState) -> dict:
        run_id = state.get("run_id")
        update_progress(run_id, node_name)
        try:
            result = func(state)
            result_key = NODE_RESULT_KEYS[node_name]
            tracked = result.get(result_key) or result
            update_progress(run_id, node_name, tracked)
            return result
        except Exception as e:
            logger.error(f"{node_name} failed: {e}")
            update_progress(run_id, node_name, {"error": str(e)})
            return {NODE_RESULT_KEYS[node_name]: {"error": str(e)}, "errors": [str(e)]}
    return wrapper
```

This ensures:
- One failed agent never blocks the pipeline
- Progress is written to `services/progress_store.py` after each agent completes (keyed by `run_id`)
- Partial results are available to the frontend via `GET /api/analysis/status/{run_id}`
- All errors are collected in `state["errors"]` for downstream visibility
- The frontend displays partial results with clear error markers

---

## How to Add a New Agent

1. **Create the agent module** in `agents/your_agent.py` — extend `BaseAgent` and implement a `run(state: dict) -> dict` method

2. **Add its result field** to `AgentState` in `agents/graph.py` — add `your_result: Optional[dict]`

3. **Add its node name** to `NODE_NAMES` list and a mapping in `NODE_RESULT_KEYS` dict in `graph.py`

4. **Wrap via `_track()`** in `graph.py`:

    ```python
    your_agent_node = _track("your_agent", lambda s: your_agent.run(s))
    ```

5. **Register the node** in `create_graph()`:

    ```python
    workflow.add_node("your_agent", your_agent_node)
    ```

6. **Wire the edge** — add an edge from the previous agent to yours:

    ```python
    workflow.add_edge("previous_agent", "your_agent")
    workflow.add_edge("your_agent", "next_agent")
    ```

7. **Update the schema** — add `your_result: Optional[dict]` to `AnalysisResponse` in `schemas/analysis.py`

8. **Add display name** to `AGENT_DISPLAY_NAMES` in `services/progress_store.py`

9. **Handle in the API route** — read `your_result` from `result.get("your_result")` in `api/routes/analysis.py`

10. **Update the frontend** — add a page module and wire it into `frontend/app.py`

---

## Future Web Search Enhancement

The Salary and Culture agents currently rely on LLM training data. A planned enhancement will add optional web search (Brave Search API or SerpAPI) for real-time salary and review data enrichment.
