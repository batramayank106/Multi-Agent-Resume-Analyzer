import uuid
import threading
import time
from datetime import datetime, timedelta

_store = {}
_lock = threading.Lock()
_STALE_TTL_SECONDS = 300  # 5 minutes — clean up completed/errored runs


def _cleanup_old():
    now = datetime.now()
    stale_ids = []
    for rid, entry in list(_store.items()):
        if entry["status"] in ("completed", "error"):
            updated = datetime.fromisoformat(entry["updated_at"])
            if now - updated > timedelta(seconds=_STALE_TTL_SECONDS):
                stale_ids.append(rid)
    for rid in stale_ids:
        del _store[rid]
    return len(stale_ids)

AGENT_NAMES = [
    "ats_agent", "recruiter_agent", "hiring_manager_agent",
    "simulator_agent", "skill_gap_agent", "truthfulness_agent",
    "company_agent", "salary_agent", "rewrite_agent",
    "interview_agent", "famous_questions_agent", "selection_agent",
]

AGENT_DISPLAY_NAMES = {
    "ats_agent": "ATS",
    "recruiter_agent": "Recruiter",
    "hiring_manager_agent": "HM",
    "simulator_agent": "Simulator",
    "skill_gap_agent": "Skill Gap",
    "truthfulness_agent": "Truth",
    "company_agent": "Company",
    "salary_agent": "Salary",
    "rewrite_agent": "Rewrite",
    "interview_agent": "Interview",
    "famous_questions_agent": "Famous Qs",
    "selection_agent": "Selection",
}


RESULT_KEY_MAP = {
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


def create_run() -> str:
    run_id = str(uuid.uuid4())[:8]
    with _lock:
        _cleanup_old()
        _store[run_id] = {
            "status": "started",
            "current_agent": None,
            "current_agent_index": -1,
            "results": {},
            "errors": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
    return run_id


def update_progress(run_id: str, agent_key: str, result: dict = None):
    with _lock:
        _cleanup_old()
        if run_id not in _store:
            return
        entry = _store[run_id]
        if result is not None:
            result_key = RESULT_KEY_MAP.get(agent_key, agent_key)
            entry["results"][result_key] = result
        if agent_key in AGENT_NAMES:
            entry["current_agent"] = agent_key
            entry["current_agent_index"] = AGENT_NAMES.index(agent_key)
        if agent_key == "selection_agent" and result is not None:
            entry["status"] = "completed"
        entry["updated_at"] = datetime.now().isoformat()


def set_error(run_id: str, error: str):
    with _lock:
        if run_id in _store:
            _store[run_id]["errors"].append(error)
            _store[run_id]["status"] = "error"
            _store[run_id]["updated_at"] = datetime.now().isoformat()


def set_complete(run_id: str):
    with _lock:
        if run_id in _store:
            _store[run_id]["status"] = "completed"
            _store[run_id]["updated_at"] = datetime.now().isoformat()


def get_status(run_id: str) -> dict:
    with _lock:
        entry = _store.get(run_id)
        if not entry:
            return {"status": "not_found"}
        now = datetime.now()
        updated = datetime.fromisoformat(entry["updated_at"])
        if entry["status"] in ("completed", "error") and now - updated > timedelta(seconds=_STALE_TTL_SECONDS):
            del _store[run_id]
            return {"status": "not_found"}
        return dict(entry)


def cleanup_stale() -> int:
    with _lock:
        return _cleanup_old()
