# API Reference

The CV Chacha — by Mayank Batra backend exposes a RESTful API at `http://localhost:8000`. Authentication is required for all `/api/` routes (except register and login). JWT bearer tokens with 30-minute access and 7-day refresh token rotation.

---

## Base URL

```
http://localhost:8000
```

All endpoints expect and return JSON. Dates use ISO 8601 format where applicable.

---

## Authentication

Authentication is implemented via **JWT bearer tokens** with bcrypt password hashing:

- **Access Tokens** (30-minute lifetime) — sent as `Authorization: Bearer <token>` header
- **Refresh Tokens** (7-day lifetime) — used via `POST /api/auth/refresh` to obtain new access tokens
- **RBAC** with three roles: `user`, `admin`, `super_admin`
- **Password policy**: 8+ characters, at least 1 uppercase, 1 lowercase, 1 digit, 1 special character
- **Login lockout**: 5 failed attempts triggers a 15-minute lockout
- **Rate limiting**: 60 requests per minute per IP (all `/api/` routes)
- **Prompt injection detection**: scored on all LLM routes (threshold ≥2 blocks the request)

### Auth Endpoints

| Method | Path | Auth | Role |
|--------|------|------|------|
| POST | `/api/auth/register` | No | — |
| POST | `/api/auth/login` | No | — |
| POST | `/api/auth/refresh` | No | — |
| GET | `/api/auth/me` | Yes | Any |
| POST | `/api/auth/logout` | No | — |
| GET | `/api/auth/users` | Yes | admin / super_admin |
| GET | `/api/auth/audit-logs` | Yes | admin / super_admin |
| PATCH | `/api/auth/users/{id}/role` | Yes | super_admin |
| PATCH | `/api/auth/users/{id}/toggle-active` | Yes | super_admin |

---

## Endpoints

### GET /health

Health check endpoint. Use this to verify the backend is running.

**Response `200 OK`:**

```json
{
  "status": "ok",
  "app": "CV Chacha",
  "version": "1.0.0"
}
```

**Example:**

```bash
curl http://localhost:8000/health
```

---

### POST /api/analysis/full

Runs the full 12-agent LangGraph pipeline against a resume and optional job description.

**Request Body:**

```json
{
  "resume_text": "John Doe\nSoftware Engineer with Python, FastAPI, React...",
  "jd_text": "Looking for a Senior Software Engineer with Python, FastAPI...",
  "parsed_skills": ["Python", "FastAPI", "React"],
  "parsed_experience": [
    {
      "title": "Senior Engineer",
      "company": "TechCorp",
      "bullets": ["Built microservices"]
    }
  ],
  "parsed_projects": [
    {
      "name": "E-Commerce Platform",
      "description": "Full stack app"
    }
  ],
  "parsed_education": [
    {
      "degree": "B.S. Computer Science",
      "institution": "University"
    }
  ],
  "parsed_achievements": ["Published 2 blog posts"]
}
```

**Schema (`AnalysisRequest`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `resume_text` | string | Yes | Full resume content as plain text |
| `jd_text` | string | No | Job description text |
| `parsed_skills` | string[] | No | Extracted skill list |
| `parsed_experience` | object[] | No | Work experience entries |
| `parsed_projects` | object[] | No | Project entries |
| `parsed_education` | object[] | No | Education entries |
| `parsed_achievements` | string[] | No | Achievement list |

**Response `200 OK`:**

```json
{
  "status": "completed",
  "ats_result": {
    "overall_score": 85,
    "category_label": "Strong",
    "breakdown": { ... },
    "evidence": [ ... ],
    "missing_keywords": ["kubernetes"],
    "matched_keywords": ["python", "fastapi", "react"]
  },
  "recruiter_result": {
    "recruiter_score": 78,
    "decision": "PASS",
    "confidence": 82,
    "reasoning": "..."
  },
  "hiring_manager_result": { ... },
  "simulator_results": {
    "overall_decision": "PASS",
    "overall_confidence": 80,
    "persona_results": {
      "ATS": { "decision": "PASS", "confidence": 85 },
      "HR": { "decision": "PASS", "confidence": 78 },
      "Engineering Manager": { "decision": "CONDITIONAL", "confidence": 72 }
    }
  },
  "skill_gap_result": { ... },
  "truthfulness_result": { ... },
  "company_result": {
    "company_name": "TechCorp",
    "overall_suitability": "GOOD",
    "culture_score": 72,
    "review_summary": "Employees appreciate the work culture...",
    "pros": ["Good benefits", "Smart colleagues"],
    "cons": ["Long hours", "Slow promotion"],
    "work_life_balance": "Average",
    "career_growth": "Good"
  },
  "salary_result": {
    "salary_range": "$120K - $160K",
    "currency": "USD",
    "confidence": "Medium",
    "factors": ["Senior role", "Tech hub location"],
    "source": "LLM Knowledge"
  },
  "rewrite_result": { ... },
  "interview_result": { ... },
  "famous_questions_result": {
    "company": "Google",
    "questions": [
      {
        "question": "Design a URL shortening service...",
        "source": "Google SD",
        "difficulty": "Hard",
        "round": "System Design"
      }
    ],
    "question_count": 1
  },
  "selection_probability": { ... },
  "errors": []
}
```

**Error Response `200 OK` (pipeline failure):**

```json
{
  "status": "error",
  "errors": ["HF_API_KEY not configured"],
  "ats_result": null,
  "recruiter_result": null,
  ...
}
```

The pipeline never returns a 500 — errors are captured per-agent and surfaced in the response with `status: "error"`.

**Example:**

```bash
curl -X POST http://localhost:8000/api/analysis/full \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "John Doe\nPython, FastAPI, React developer",
    "jd_text": "Senior engineer with Python and FastAPI",
    "parsed_skills": ["Python", "FastAPI", "React"]
  }'
```

---

### POST /api/analysis/stream

Starts a 12-agent LangGraph pipeline in a background thread and immediately returns a `run_id` for status polling. Results accumulate in an in-memory progress store as each agent completes.

**Request Body:**

Same as `POST /api/analysis/full` — uses the `AnalysisRequest` schema.

**Response `200 OK`:**

```json
{
  "run_id": "a1b2c3d4",
  "status": "started"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/analysis/stream \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "John Doe\nPython, FastAPI, React developer",
    "jd_text": "Senior engineer with Python and FastAPI",
    "parsed_skills": ["Python", "FastAPI", "React"]
  }'
```

---

### GET /api/analysis/status/{run_id}

Polls the progress of a streaming analysis run. The `run_id` comes from the `/api/analysis/stream` response.

**Response `200 OK` (in progress):**

```json
{
  "status": "started",
  "current_agent": "ats_agent",
  "current_agent_index": 0,
  "results": {},
  "errors": [],
  "created_at": "2026-06-24T10:30:00",
  "updated_at": "2026-06-24T10:30:05"
}
```

**Response `200 OK` (agent completed — partial result in `results`):**

```json
{
  "status": "started",
  "current_agent": "recruiter_agent",
  "current_agent_index": 1,
  "results": {
    "ats_result": {
      "overall_score": 85,
      "category_label": "Strong",
      "breakdown": { "Keyword Match": 85, "Skill Match": 80 },
      "evidence": ["Matched keyword 'python'", "Missing keyword 'kubernetes'"]
    }
  },
  "errors": [],
  "created_at": "2026-06-24T10:30:00",
  "updated_at": "2026-06-24T10:30:08"
}
```

**Response `200 OK` (complete):**

```json
{
  "status": "completed",
  "current_agent": "selection_agent",
  "current_agent_index": 11,
  "results": {
    "ats_result": { ... },
    "recruiter_result": { ... },
    "hiring_manager_result": { ... },
    "simulator_results": { ... },
    "skill_gap_result": { ... },
    "truthfulness_result": { ... },
    "company_result": { ... },
    "salary_result": { ... },
    "rewrite_result": { ... },
    "interview_result": { ... },
    "famous_questions_result": { ... },
    "selection_probability": { ... }
  },
  "errors": [],
  "created_at": "2026-06-24T10:30:00",
  "updated_at": "2026-06-24T10:35:00"
}
```

**Response `200 OK` (not found / expired):**

```json
{
  "status": "not_found"
}
```

Runs expire after 5 minutes of completion. The frontend displays a "tracking expired" message and prompts re-analysis.

**Example:**

```bash
curl http://localhost:8000/api/analysis/status/a1b2c3d4
```

---

### POST /api/llm/chat

Simple stateless chat with the configured LLM. No RAG context is injected.

**Request Body:**

```json
{
  "messages": [
    {"role": "user", "content": "How can I improve my resume?"}
  ],
  "model": "Qwen3 Instruct",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Schema (`ChatRequest`):**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `messages` | object[] | Yes | — | Array of `{role, content}` messages |
| `model` | string | No | `null` (uses default) | Model name from the registry |
| `temperature` | float | No | `0.7` | Sampling temperature (0.0–1.0) |
| `max_tokens` | integer | No | `2048` | Maximum response tokens |

**Response `200 OK`:**

```json
{
  "content": "Start by quantifying your achievements...",
  "model": "Qwen3 Instruct",
  "model_id": "Qwen/Qwen3-8B-Instruct",
  "usage": {
    "input_tokens": 45,
    "output_tokens": 120,
    "total_tokens": 165,
    "estimated_cost": 0.000028
  }
}
```

**Error Response `500`:**

```json
{
  "detail": "No models available"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What is a good ATS score?"}]
  }'
```

---

### POST /api/llm/rag-chat

Chat endpoint with RAG context injection. The backend retrieves relevant knowledge chunks from ChromaDB, re-ranks them with a cross-encoder, and injects the most relevant context into the system prompt before calling the LLM.

**Request Body:**

```json
{
  "messages": [
    {"role": "user", "content": "What are the key skills for a data scientist?"}
  ],
  "resume_context": "Candidate has experience in Python, SQL, and machine learning...",
  "model": "Qwen3 Instruct",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Schema (`RAGChatRequest`):**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `messages` | object[] | Yes | — | Chat history + latest user query |
| `resume_context` | string | No | `""` | Additional resume context to inject |
| `model` | string | No | `null` | Model name from the registry |
| `temperature` | float | No | `0.7` | Sampling temperature |
| `max_tokens` | integer | No | `2048` | Maximum response tokens |

**Response `200 OK`:**

```json
{
  "content": "Based on the knowledge base, key data scientist skills include...",
  "model": "Qwen3 Instruct",
  "model_id": "Qwen/Qwen3-8B-Instruct",
  "usage": {
    "input_tokens": 312,
    "output_tokens": 180,
    "total_tokens": 492,
    "estimated_cost": 0.000067
  },
  "citations": [
    {
      "content": "Data scientists typically need proficiency in Python...",
      "score": 0.892,
      "source": "knowledge base"
    }
  ]
}
```

The `citations` array contains the top 3 retrieved chunks with relevance scores. Sources come from the 30 seed knowledge documents stored in ChromaDB.

**Example:**

```bash
curl -X POST http://localhost:8000/api/llm/rag-chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "How does ATS scoring work?"}]
  }'
```

---

### GET /api/llm/models

List all available LLM models and the currently active one.

**Response `200 OK`:**

```json
{
  "models": [
    "Qwen3 Instruct",
    "DeepSeek-R1 Distill",
    "Gemma 3",
    "Mistral Small",
    "Llama 3.1 Instruct"
  ],
  "current": "Qwen3 Instruct"
}
```

**Example:**

```bash
curl http://localhost:8000/api/llm/models
```

---

### POST /api/llm/models/switch

Switch the active LLM model.

**Request:**

Query parameter: `model_name` (string, required)

```bash
curl -X POST "http://localhost:8000/api/llm/models/switch?model_name=Llama%203.1%20Instruct"
```

**Response `200 OK`:**

```json
{
  "current_model": "Llama 3.1 Instruct"
}
```

**Error Response `400`:**

```json
{
  "detail": "Unknown model: NonExistentModel"
}
```

---

### POST /api/auth/register

Register a new user account.

**Request Body:**

```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass1!"
}
```

**Response `201 Created`:**

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "role": "user",
  "is_active": true
}
```

**Error `400`:** Weak password, duplicate email, or missing fields.

---

### POST /api/auth/login

Authenticate and receive JWT tokens.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "SecurePass1!"
}
```

**Response `200 OK`:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 1800
}
```

**Error `401`:** Invalid credentials. **Error `423`:** Account locked (15 min).

---

### POST /api/auth/refresh

Obtain a new access token using a refresh token.

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response `200 OK`:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

### GET /api/auth/me

Get the currently authenticated user's profile. Requires `Authorization: Bearer <token>`.

**Response `200 OK`:**

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "role": "user",
  "is_active": true
}
```

---

### POST /api/auth/logout

Invalidate the current session (client-side token discard).

**Response `200 OK`:**

```json
{
  "message": "Logout successful. Discard your tokens."
}
```

---

### GET /api/auth/users *(admin / super_admin)*

List all registered users.

**Response `200 OK`:**

```json
[
  { "id": 1, "email": "admin@test.com", "username": "admin", "role": "super_admin", "is_active": true },
  { "id": 2, "email": "user@example.com", "username": "johndoe", "role": "user", "is_active": true }
]
```

**Error `403`:** Non-admin user.

---

### GET /api/auth/audit-logs *(admin / super_admin)*

Retrieve the most recent 200 audit log entries.

**Response `200 OK`:**

```json
[
  {
    "id": 1,
    "user_email": "admin@test.com",
    "method": "POST",
    "path": "/api/auth/login",
    "status_code": 200,
    "ip_address": "127.0.0.1",
    "duration_ms": 45,
    "created_at": "2026-06-22T10:30:00"
  }
]
```

---

### PATCH /api/auth/users/{user_id}/role *(super_admin)*

Change a user's role.

**Request Body:**

```json
{
  "role": "admin"
}
```

**Response `200 OK`:**

```json
{
  "message": "User user@example.com role updated to admin"
}
```

---

### PATCH /api/auth/users/{user_id}/toggle-active *(super_admin)*

Activate or deactivate a user account.

**Response `200 OK`:**

```json
{
  "message": "User user@example.com active=false"
}
```

---

### GET /api/vault/sessions

List all analysis sessions for the authenticated user.

**Response `200 OK`:**

```json
[
  {
    "session_id": "uuid-string",
    "analysis_date": "2026-06-22T10:30:00",
    "company_name": "TechCorp",
    "job_role": "Senior Engineer",
    "ats_score": 85,
    "recruiter_score": 78,
    "hiring_manager_score": 72
  }
]
```

---

### GET /api/vault/sessions/{session_id}

Get full analysis detail for a session, including all agent results.

**Response `200 OK`:** Full analysis response (same schema as `/api/analysis/full` response) with `session_id`, `analysis_date`, `resume_text`, `jd_text`.

---

### DELETE /api/vault/sessions/{session_id}

Delete a session and its linked resume/JD records.

**Response `200 OK`:**

```json
{
  "message": "Session deleted successfully"
}
```

---

### GET /api/vault/compare

Compare two analysis sessions side-by-side with score deltas, skill/keyword/bullet/project changes, and an improvement summary.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `v1` | int | Yes | First analysis session ID (older version) |
| `v2` | int | Yes | Second analysis session ID (newer version) |

**Response `200 OK`:**

```json
{
  "score_deltas": {
    "ats": 8.0,
    "recruiter": 5.0,
    "hm": 3.0
  },
  "skills": {
    "added": ["Docker", "Kubernetes"],
    "removed": [],
    "common": ["Python", "FastAPI"]
  },
  "keywords": {
    "added": ["docker", "kubernetes"],
    "removed": [],
    "common_count": 42
  },
  "bullet_changes": {
    "improved": 3,
    "added": 2,
    "removed": 1
  },
  "project_changes": {
    "added": ["CI/CD Pipeline"],
    "removed": []
  },
  "improvement_summary": "ATS score improved by 8 points. Added skills: Docker, Kubernetes. Added 2 bullet points.",
  "version_a": { "score": 72, "skills": ["Python", "FastAPI"], "date": "2026-06-22T10:00:00" },
  "version_b": { "score": 80, "skills": ["Python", "FastAPI", "Docker", "Kubernetes"], "date": "2026-06-22T11:00:00" }
}
```

---

### GET /api/vault/versions

List all resume version records across all analyses, ordered by creation date (newest first). Each analysis run auto-creates a version record with all scores.

**Response `200 OK`:**

```json
[
  {
    "id": 1,
    "version_number": 1,
    "resume_id": 1,
    "analysis_result_id": 1,
    "ats_score": 85.0,
    "recruiter_score": 78.0,
    "hiring_manager_score": 82.0,
    "truthfulness_score": 90.0,
    "created_at": "2026-06-22T10:30:00"
  }
]
```

---

### GET /api/vault/versions/{version_id}

Get a single version record by its ID.

**Response `200 OK`:** Same schema as `/api/vault/versions` response for a single item.

**Error `404`:** Version not found.

---

### POST /api/compare/resumes

Compare two resumes line-by-line and by skill set.

**Request Body:**

```json
{
  "resume_a": "Full text of resume A...",
  "resume_b": "Full text of resume B..."
}
```

**Response `200 OK`:**

```json
{
  "total_lines_a": 120,
  "total_lines_b": 135,
  "diff_lines": [
    {"type": "equal", "content": "Python, FastAPI, React"},
    {"type": "added", "content": "Docker, Kubernetes", "line_b": 15},
    {"type": "removed", "content": "jQuery", "line_a": 12}
  ],
  "skills_diff": {
    "added": ["Docker", "Kubernetes"],
    "removed": ["jQuery"],
    "common": ["Python", "FastAPI", "React"]
  }
}
```

---

### POST /api/library/upload

Upload a resume file (encrypted at rest).

**Request:** `multipart/form-data` with fields `file` (PDF/TXT) and `file_type` (resume/jd/both).

**Response `201 Created`:**

```json
{
  "file_id": "uuid",
  "original_filename": "resume.pdf",
  "file_type": "resume",
  "size": 45230,
  "uploaded_at": "2026-06-22T10:30:00"
}
```

**Error `413`:** File exceeds 10 MB limit. **Error `400`:** Invalid file type.

---

### GET /api/library/files

List all uploaded files.

**Response `200 OK`:**

```json
[
  {
    "file_id": "uuid",
    "original_filename": "resume.pdf",
    "file_type": "resume",
    "size": 45230,
    "uploaded_at": "2026-06-22T10:30:00"
  }
]
```

---

### GET /api/library/files/{file_id}

Download a decrypted file.

**Response `200 OK`:** Binary file stream with `Content-Disposition: attachment`.

**Error `404`:** File not found.

---

### DELETE /api/library/files/{file_id}

Delete an uploaded file.

**Response `200 OK`:**

```json
{
  "message": "File deleted successfully"
}
```

Retrieve token usage and cost statistics for the current session.

**Response `200 OK`:**

```json
{
  "current_model": "Qwen3 Instruct",
  "total_input_tokens": 15420,
  "total_output_tokens": 8930,
  "total_tokens": 24350,
  "total_cost": 0.003872,
  "api_calls": 47,
  "failed_calls": 2
}
```

**Example:**

```bash
curl http://localhost:8000/api/llm/stats
```

---

## Error Response Format

All errors follow a consistent structure:

| HTTP Status | Meaning |
|---|---|
| `200` | Success (pipeline errors returned in body) |
| `400` | Bad request — invalid parameters, prompt injection blocked |
| `401` | Unauthorized — missing or invalid JWT token |
| `403` | Forbidden — insufficient role (user vs admin vs super_admin) |
| `404` | Not found — session, file, or user not found |
| `413` | Payload too large — file exceeds 10 MB limit |
| `423` | Locked — account temporarily locked due to failed login attempts |
| `429` | Too many requests — rate limit exceeded (60 req/min) |
| `500` | Server error — models unavailable, API failures |

**Error response example:**

```json
{
  "detail": "No models available"
}
```

---

## Status Codes Summary

| Code | Description |
|---|---|
| `200` | Request successful |
| `400` | Invalid request body, parameters, or prompt injection detected |
| `401` | Missing or invalid authentication token |
| `403` | Insufficient role permissions |
| `404` | Resource not found |
| `413` | Upload file exceeds size limit |
| `423` | Account locked |
| `429` | Rate limit exceeded |
| `500` | Server-side error (missing config, API failure) |
