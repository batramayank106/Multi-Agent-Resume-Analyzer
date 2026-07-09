"""Tests for salary_agent, famous_questions_agent, and graph wiring."""

import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from config import settings
from agents.graph import create_graph, AgentState
from agents.salary_agent import salary_agent
from agents.famous_questions_agent import famous_questions_agent


has_llm_key = settings.groq_api_key is not None or settings.hf_api_key is not None
llm_skip = pytest.mark.skipif(not has_llm_key, reason="No LLM API key configured")


BASE_STATE = {
    "resume_id": None, "jd_id": None,
    "resume_text": "Test resume",
    "jd_text": "Senior engineer at Google",
    "parsed_skills": ["Python", "FastAPI"],
    "parsed_experience": [], "parsed_projects": [], "parsed_education": [], "parsed_achievements": [],
    "ats_result": None, "recruiter_result": None, "hiring_manager_result": None,
    "simulator_results": None, "skill_gap_result": None, "truthfulness_result": None,
    "company_result": {"company_name": "Google"},
    "salary_result": None, "rewrite_result": None, "interview_result": None,
    "famous_questions_result": None, "selection_probability": None,
    "errors": [], "status": "started",
}


@llm_skip
def test_salary_agent_returns_structure():
    result = salary_agent.run(BASE_STATE)
    sr = result["salary_result"]
    assert "salary_range" in sr
    assert "factors" in sr
    assert "confidence" in sr
    assert "currency" in sr
    assert "llm_scored" in sr


@llm_skip
def test_famous_questions_agent_returns_structure():
    result = famous_questions_agent.run(BASE_STATE)
    fqr = result["famous_questions_result"]
    assert "questions" in fqr
    assert "question_count" in fqr
    assert "company" in fqr
    assert "llm_scored" in fqr


def test_graph_has_all_agents():
    g = create_graph()
    c = g.compile()
    nodes = list(c.get_graph().nodes.keys())
    agent_nodes = [n for n in nodes if n not in ("__start__", "__end__")]
    assert "salary_agent" in agent_nodes
    assert "famous_questions_agent" in agent_nodes
    assert len(agent_nodes) == 12


def test_agent_state_has_new_fields():
    state: AgentState = {
        "resume_id": None, "jd_id": None,
        "resume_text": "", "jd_text": None,
        "parsed_skills": [], "parsed_experience": [], "parsed_projects": [],
        "parsed_education": [], "parsed_achievements": [],
        "ats_result": None, "recruiter_result": None, "hiring_manager_result": None,
        "simulator_results": None, "skill_gap_result": None, "truthfulness_result": None,
        "company_result": None,
        "salary_result": None,
        "rewrite_result": None, "interview_result": None,
        "famous_questions_result": None,
        "selection_probability": None,
        "errors": [], "status": "started",
    }
    assert "salary_result" in state
    assert "famous_questions_result" in state
