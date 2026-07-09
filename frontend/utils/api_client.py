import os
import httpx
from typing import Optional

try:
    import streamlit as st
    BACKEND_URL = os.getenv("BACKEND_URL") or st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")
except Exception:
    BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


def _auth_headers():
    try:
        import streamlit as st
        token = st.session_state.get("access_token")
        if token:
            return {"Authorization": f"Bearer {token}"}
    except Exception:
        pass
    return {}


def health_check() -> bool:
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{BACKEND_URL}/health")
            return r.status_code == 200
    except Exception:
        return False


def run_full_analysis(
    resume_text: str,
    jd_text: Optional[str] = None,
    parsed_skills: Optional[list[str]] = None,
    parsed_experience: Optional[list[dict]] = None,
    parsed_projects: Optional[list[dict]] = None,
    parsed_education: Optional[list[dict]] = None,
    parsed_achievements: Optional[list[str]] = None,
) -> dict:
    payload = {
        "resume_text": resume_text,
        "jd_text": jd_text or "",
        "parsed_skills": parsed_skills or [],
        "parsed_experience": parsed_experience or [],
        "parsed_projects": parsed_projects or [],
        "parsed_education": parsed_education or [],
        "parsed_achievements": parsed_achievements or [],
    }
    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.post(f"{BACKEND_URL}/api/analysis/full", json=payload, headers=_auth_headers())
            r.raise_for_status()
            return r.json()
    except Exception as e:
        return {"status": "error", "errors": [str(e)]}


def start_analysis_stream(
    resume_text: str,
    jd_text: Optional[str] = None,
    parsed_skills: Optional[list[str]] = None,
    parsed_experience: Optional[list[dict]] = None,
    parsed_projects: Optional[list[dict]] = None,
    parsed_education: Optional[list[dict]] = None,
    parsed_achievements: Optional[list[str]] = None,
) -> dict:
    payload = {
        "resume_text": resume_text,
        "jd_text": jd_text or "",
        "parsed_skills": parsed_skills or [],
        "parsed_experience": parsed_experience or [],
        "parsed_projects": parsed_projects or [],
        "parsed_education": parsed_education or [],
        "parsed_achievements": parsed_achievements or [],
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{BACKEND_URL}/api/analysis/stream", json=payload, headers=_auth_headers())
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


def poll_analysis_status(run_id: str) -> dict:
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{BACKEND_URL}/api/analysis/status/{run_id}", headers=_auth_headers())
            r.raise_for_status()
            return r.json()
    except Exception:
        return {"status": "not_found"}


def list_llm_models() -> dict:
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{BACKEND_URL}/api/llm/models")
            return r.json()
    except Exception:
        return {}


def llm_chat(messages: list[dict], temperature: float = 0.7) -> dict:
    payload = {"messages": messages, "temperature": temperature}
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(f"{BACKEND_URL}/api/llm/chat", json=payload, headers=_auth_headers())
            return r.json()
    except Exception as e:
        return {"content": f"Error: {e}"}


def rag_chat(
    messages: list[dict],
    resume_context: str = "",
    temperature: float = 0.7,
) -> dict:
    payload = {
        "messages": messages,
        "resume_context": resume_context,
        "temperature": temperature,
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(f"{BACKEND_URL}/api/llm/rag-chat", json=payload, headers=_auth_headers())
            r.raise_for_status()
            return r.json()
    except Exception as e:
        return {"content": f"Error: {e}", "citations": []}


def get_llm_stats() -> dict:
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{BACKEND_URL}/api/llm/stats")
            return r.json()
    except Exception:
        return {}


# --- Auth ---

def auth_register(email: str, username: str, password: str) -> dict:
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{BACKEND_URL}/api/auth/register", json={
                "email": email, "username": username, "password": password,
            })
            return {"status": r.status_code, "body": r.json() if r.status_code < 500 else {}}
    except Exception as e:
        return {"status": 0, "body": {"detail": str(e)}}


def auth_login(email: str, password: str) -> dict:
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{BACKEND_URL}/api/auth/login", json={
                "email": email, "password": password,
            })
            return {"status": r.status_code, "body": r.json() if r.status_code < 500 else {}}
    except Exception as e:
        return {"status": 0, "body": {"detail": str(e)}}


def auth_refresh(refresh_token: str) -> dict:
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{BACKEND_URL}/api/auth/refresh", json={"refresh_token": refresh_token})
            return {"status": r.status_code, "body": r.json() if r.status_code < 500 else {}}
    except Exception as e:
        return {"status": 0, "body": {"detail": str(e)}}


def auth_me(access_token: str) -> dict:
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{BACKEND_URL}/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
            return {"status": r.status_code, "body": r.json() if r.status_code < 500 else {}}
    except Exception as e:
        return {"status": 0, "body": {"detail": str(e)}}


def auth_list_users(access_token: str) -> dict:
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{BACKEND_URL}/api/auth/users", headers={"Authorization": f"Bearer {access_token}"})
            return {"status": r.status_code, "body": r.json() if r.status_code < 500 else {}}
    except Exception as e:
        return {"status": 0, "body": {"detail": str(e)}}


DEMO_RESUME = """Rahul Sharma
Senior Full-Stack Engineer

Skills: Python, FastAPI, React, TypeScript, PostgreSQL, Docker, AWS, Kubernetes, Redis, GraphQL

Experience:
Senior Software Engineer, TechCorp (2021-Present)
- Architected microservices platform handling 10M+ daily requests using FastAPI and PostgreSQL
- Reduced deployment time by 60% with Docker-based CI/CD pipeline on AWS ECS
- Led migration from monolith to microservices, serving 200k+ users

Full-Stack Developer, StartupHub (2019-2021)
- Built real-time dashboard with React, TypeScript, and WebSocket connections
- Implemented GraphQL API layer reducing frontend data fetching by 40%
- Managed PostgreSQL database with 50+ tables and complex query optimization

Projects:
Cloud-Native E-Commerce Platform — FastAPI, React, PostgreSQL, Docker, AWS
Real-Time Analytics Dashboard — TypeScript, GraphQL, Redis, WebSockets
CI/CD Pipeline Automation — GitHub Actions, Docker, Terraform

Education:
MS Computer Science, IIT Delhi (2017-2019)
BTech Information Technology, NIT Trichy (2013-2017)

Achievements:
Published 3 papers on distributed systems
Won hackathon for AI-powered resume analyzer
Led engineering team of 8 developers"""

DEMO_JD = """Senior Full-Stack Engineer

About the Role:
We're looking for an experienced Full-Stack Engineer to join our platform team. You'll architect and build scalable web services, collaborate with product and design teams, and mentor junior engineers.

Requirements:
- Python, FastAPI, or Node.js backend experience
- React or TypeScript frontend experience
- PostgreSQL or similar relational databases
- Docker and container orchestration (Kubernetes preferred)
- Cloud platforms (AWS/GCP/Azure)
- Experience with microservices architecture
- CI/CD pipelines and DevOps practices
- 5+ years of professional software engineering experience

Nice to Have:
- GraphQL API design
- Redis or similar caching systems
- Machine learning pipeline experience
- Open source contributions

What We Offer:
- Competitive salary and equity
- Remote-first culture
- Learning budget for conferences and courses
- Health insurance and wellness benefits"""

DEMO_SAMPLE_DATA = {
    "resume_text": DEMO_RESUME,
    "jd_text": DEMO_JD,
    "parsed_skills": ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker", "AWS", "Kubernetes", "Redis", "GraphQL"],
    "parsed_experience": [
        {"company": "TechCorp", "title": "Senior Software Engineer", "years": "2021-Present"},
        {"company": "StartupHub", "title": "Full-Stack Developer", "years": "2019-2021"},
    ],
    "parsed_projects": [
        {"name": "Cloud-Native E-Commerce Platform"},
        {"name": "Real-Time Analytics Dashboard"},
        {"name": "CI/CD Pipeline Automation"},
    ],
    "parsed_education": [
        {"degree": "MS Computer Science", "university": "IIT Delhi", "year": "2019"},
        {"degree": "BTech Information Technology", "university": "NIT Trichy", "year": "2017"},
    ],
    "parsed_achievements": ["Published 3 papers on distributed systems", "Won hackathon for AI-powered resume analyzer", "Led engineering team of 8 developers"],
}
