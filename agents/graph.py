import logging
import sys
from pathlib import Path
from typing import TypedDict, Optional, Any

from langgraph.graph import StateGraph, END

_root = str(Path(__file__).parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from agents.ats_agent import ats_agent
from agents.recruiter_agent import recruiter_agent
from agents.hiring_manager_agent import hiring_manager_agent
from agents.simulator_agent import simulator_agent
from agents.skill_gap_agent import skill_gap_agent
from agents.truthfulness_agent import truthfulness_agent
from agents.company_agent import company_agent
from agents.salary_agent import salary_agent
from agents.rewrite_agent import rewrite_agent
from agents.interview_agent import interview_agent
from agents.famous_questions_agent import famous_questions_agent
from agents.selection_agent import selection_agent
from services.progress_store import update_progress

logger = logging.getLogger(__name__)


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


NODE_NAMES = [
    "ats_agent", "recruiter_agent", "hiring_manager_agent",
    "simulator_agent", "skill_gap_agent", "truthfulness_agent",
    "company_agent", "salary_agent", "rewrite_agent",
    "interview_agent", "famous_questions_agent", "selection_agent",
]

NODE_RESULT_KEYS = {
    "ats_agent": "ats_result",
    "recruiter_agent": "recruiter_result",
    "hiring_manager_agent": "hiring_manager_result",
    "simulator_agent": "simulator_results",
    "skill_gap_agent": "skill_gap_result",
    "truthfulness_agent": "truthfulness_result",
    "company_agent": "company_result",
    "salary_agent": "salary_result",
    "rewrite_agent": "rewrite_result",
    "interview_agent": "interview_result",
    "famous_questions_agent": "famous_questions_result",
    "selection_agent": "selection_probability",
}


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
    wrapper.__name__ = f"{node_name}_node"
    return wrapper


ats_agent_node = _track("ats_agent", lambda s: ats_agent.run(s))
recruiter_agent_node = _track("recruiter_agent", lambda s: recruiter_agent.run(s))
hiring_manager_agent_node = _track("hiring_manager_agent", lambda s: hiring_manager_agent.run(s))
simulator_agent_node = _track("simulator_agent", lambda s: simulator_agent.run(s))
skill_gap_agent_node = _track("skill_gap_agent", lambda s: skill_gap_agent.run(s))
truthfulness_agent_node = _track("truthfulness_agent", lambda s: truthfulness_agent.run(s))
company_agent_node = _track("company_agent", lambda s: company_agent.run(s))
salary_agent_node = _track("salary_agent", lambda s: salary_agent.run(s))
rewrite_agent_node = _track("rewrite_agent", lambda s: rewrite_agent.run(s))
interview_agent_node = _track("interview_agent", lambda s: interview_agent.run(s))
famous_questions_agent_node = _track("famous_questions_agent", lambda s: famous_questions_agent.run(s))
selection_agent_node = _track("selection_agent", lambda s: selection_agent.run(s))


def create_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("ats_agent", ats_agent_node)
    workflow.add_node("recruiter_agent", recruiter_agent_node)
    workflow.add_node("hiring_manager_agent", hiring_manager_agent_node)
    workflow.add_node("simulator_agent", simulator_agent_node)
    workflow.add_node("skill_gap_agent", skill_gap_agent_node)
    workflow.add_node("truthfulness_agent", truthfulness_agent_node)
    workflow.add_node("company_agent", company_agent_node)
    workflow.add_node("salary_agent", salary_agent_node)
    workflow.add_node("rewrite_agent", rewrite_agent_node)
    workflow.add_node("interview_agent", interview_agent_node)
    workflow.add_node("famous_questions_agent", famous_questions_agent_node)
    workflow.add_node("selection_agent", selection_agent_node)

    workflow.set_entry_point("ats_agent")

    workflow.add_conditional_edges(
        "ats_agent",
        lambda state: "continue" if not state.get("ats_result", {}).get("error") else "end",
        {
            "continue": "recruiter_agent",
            "end": END,
        },
    )
    workflow.add_conditional_edges(
        "recruiter_agent",
        lambda state: "continue" if not state.get("recruiter_result", {}).get("error") else "end",
        {
            "continue": "hiring_manager_agent",
            "end": END,
        },
    )
    workflow.add_edge("hiring_manager_agent", "simulator_agent")
    workflow.add_edge("simulator_agent", "skill_gap_agent")
    workflow.add_edge("skill_gap_agent", "truthfulness_agent")
    workflow.add_edge("truthfulness_agent", "company_agent")
    workflow.add_edge("company_agent", "salary_agent")
    workflow.add_edge("salary_agent", "rewrite_agent")
    workflow.add_edge("rewrite_agent", "interview_agent")
    workflow.add_edge("interview_agent", "famous_questions_agent")
    workflow.add_edge("famous_questions_agent", "selection_agent")
    workflow.add_edge("selection_agent", END)

    return workflow


def run_analysis(state: AgentState) -> AgentState:
    graph = create_graph()
    compiled = graph.compile()
    result = compiled.invoke(state)
    result["status"] = "completed" if not result.get("errors") else "partial"
    return result


def run_analysis_with_progress(state: AgentState, run_id: str) -> AgentState:
    state["run_id"] = run_id
    graph = create_graph()
    compiled = graph.compile()
    result = compiled.invoke(state)
    result["status"] = "completed" if not result.get("errors") else "partial"
    from services.progress_store import set_complete, set_error
    if result.get("errors"):
        for err in result["errors"]:
            set_error(run_id, err)
    else:
        set_complete(run_id)
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_state: AgentState = {
        "resume_id": 1,
        "jd_id": 1,
        "resume_text": "John Doe\nSoftware Engineer with Python, FastAPI, React, PostgreSQL, Docker, AWS, TypeScript, GraphQL",
        "jd_text": "Looking for a Senior Software Engineer with Python, FastAPI, TypeScript, PostgreSQL, Docker, AWS experience",
        "parsed_skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker", "AWS", "TypeScript", "GraphQL"],
        "parsed_experience": [{"title": "Senior Engineer", "company": "TechCorp", "bullets": ["Built microservices"]}],
        "parsed_projects": [{"name": "E-Commerce Platform", "description": "Full stack app"}],
        "parsed_education": [{"degree": "B.S. CS", "institution": "University"}],
        "parsed_achievements": ["Published 2 blog posts"],
        "ats_result": None,
        "recruiter_result": None,
        "hiring_manager_result": None,
        "simulator_results": None,
        "skill_gap_result": None,
        "truthfulness_result": None,
        "company_result": None,
        "salary_result": None,
        "rewrite_result": None,
        "interview_result": None,
        "famous_questions_result": None,
        "selection_probability": None,
        "errors": [],
        "status": "started",
    }

    result = run_analysis(test_state)
    ats = result.get("ats_result", {})
    print(f"ATS Score: {ats.get('overall_score')}")
    print(f"Category: {ats.get('category_label')}")

    rec = result.get("recruiter_result", {})
    print(f"\nRecruiter Score: {rec.get('recruiter_score')}")
    print(f"Decision: {rec.get('decision')}")

    hm = result.get("hiring_manager_result", {})
    print(f"\nHM Score: {hm.get('hiring_manager_score')}")
    print(f"Decision: {hm.get('decision')}")

    sim = result.get("simulator_results", {})
    print(f"\nSimulator Overall: {sim.get('overall_decision')} (confidence: {sim.get('overall_confidence')})")
    for persona, pr in sim.get("persona_results", {}).items():
        print(f"  {persona}: {pr.get('decision')} ({pr.get('confidence')})")

    sg = result.get("skill_gap_result", {})
    print(f"\nSkill Gap Severity: {sg.get('gap_severity')}")
    print(f"Missing Skills: {sg.get('missing_skills')}")

    tr = result.get("truthfulness_result", {})
    print(f"\nTruthfulness Score: {tr.get('truthfulness_score')}")
    print(f"Flagged Items: {tr.get('flagged_items')}")

    cr = result.get("company_result", {})
    print(f"\nCompany: {cr.get('company_name')}")
    print(f"Suitability: {cr.get('overall_suitability')}")

    rw = result.get("rewrite_result", {})
    print(f"\nRewrite: {len(rw.get('rewritten_resume', ''))} chars generated")

    iv = result.get("interview_result", {})
    print(f"Interview Questions: {iv.get('question_count')}")

    sp = result.get("selection_probability", {})
    print(f"Selection Probability: {sp.get('overall_probability')}%")

    print("\nGraph test passed!")
