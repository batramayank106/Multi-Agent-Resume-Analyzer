"""End-to-end test: run all agents with dummy data and verify LLM responses."""

import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from config import settings
from agents.graph import run_analysis
from agents.ats_agent import ATSAgent, ATS_WEIGHTS
import json


SAMPLE_RESUME = """John Doe
Software Engineer

Skills: Python, FastAPI, PostgreSQL, Docker, AWS, Git, TypeScript, GraphQL

Experience:
Senior Software Engineer, Tech Corp (2020-Present)
- Built microservices architecture with FastAPI and PostgreSQL
- Deployed Docker containers on AWS ECS
- Led team of 5 engineers delivering 3 major projects

Projects:
E-commerce Platform - Full-stack application with React and Node.js
CI/CD Pipeline - Automated deployment system using GitHub Actions

Education:
MS Computer Science, University of Technology, 2019

Achievements:
Published 2 research papers in peer-reviewed journals
Led team of 5 engineers"""

SAMPLE_JD = """Software Engineer

Requirements:
- Python, FastAPI, PostgreSQL
- Docker, AWS, Kubernetes
- 3+ years experience
- Strong problem-solving skills
- Machine Learning experience preferred
- TypeScript or GraphQL knowledge"""


def _build_state():
    return {
        "resume_id": None, "jd_id": None,
        "resume_text": SAMPLE_RESUME,
        "jd_text": SAMPLE_JD,
        "parsed_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Git", "TypeScript", "GraphQL"],
        "parsed_experience": [{"company": "Tech Corp", "title": "Senior Software Engineer", "years": "2020-Present"}],
        "parsed_projects": [{"name": "E-commerce Platform"}, {"name": "CI/CD Pipeline"}],
        "parsed_education": [{"degree": "MS Computer Science", "university": "University of Technology"}],
        "parsed_achievements": ["Published 2 research papers", "Led team of 5 engineers"],
        "ats_result": None, "recruiter_result": None, "hiring_manager_result": None,
        "simulator_results": None, "skill_gap_result": None, "truthfulness_result": None,
        "company_result": None, "salary_result": None, "rewrite_result": None,
        "interview_result": None, "famous_questions_result": None,
        "selection_probability": None, "errors": [], "status": "started",
    }


has_llm_key = settings.groq_api_key is not None or settings.hf_api_key is not None


@pytest.mark.skipif(not has_llm_key, reason="No LLM API key configured")
def test_ats_agent_llm():
    """Test ATS agent uses LLM and produces valid scores."""
    agent = ATSAgent()
    result = agent.run(_build_state())
    ats = result["ats_result"]

    assert ats["llm_scored"] is True, "LLM should score when API key is present"
    assert 0 <= ats["overall_score"] <= 100
    assert ats["category_label"] in ["Poor", "Average", "Good", "Strong", "Exceptional"]


@pytest.mark.skipif(not has_llm_key, reason="No LLM API key configured — would hang on network timeouts")
def test_full_pipeline():
    """Test full agent pipeline produces structured results."""
    initial_state = _build_state()
    result = run_analysis(initial_state)

    assert result.get("status") in ["completed", "partial"]
    assert result.get("ats_result") is not None


@pytest.mark.skipif(not has_llm_key, reason="No LLM API key configured")
def test_agent_responses_meaningful():
    """Verify LLM responses contain meaningful analysis (not boilerplate)."""
    agent = ATSAgent()
    result = agent.run(_build_state())
    ats = result["ats_result"]

    evidence_found = any(
        ev.get("deductions") or ev.get("evidence")
        for ev in ats.get("evidence", [])
    )
    assert evidence_found, "LLM should produce evidence-backed analysis"
