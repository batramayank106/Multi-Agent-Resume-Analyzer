import json
import logging

from agents.base_agent import BaseAgent
from services.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


class SelectionAgent(BaseAgent):

    def __init__(self):
        super().__init__("Selection Probability Agent")

    def run(self, state: dict) -> dict:
        self._log_start(resume_id=state.get("resume_id"))

        ats = state.get("ats_result", {})
        recruiter = state.get("recruiter_result", {})
        hm = state.get("hiring_manager_result", {})
        sg = state.get("skill_gap_result", {})
        tr = state.get("truthfulness_result", {})

        ats_score = ats.get("overall_score", 0)
        recruiter_score = recruiter.get("recruiter_score", 50)
        hm_score = hm.get("hiring_manager_score", 50)
        skill_gap_severity = sg.get("gap_severity", "unknown")
        truthfulness_score = tr.get("truthfulness_score", 50)

        messages = prompt_manager.selection_probability(
            ats_score, recruiter_score, hm_score, skill_gap_severity, truthfulness_score,
        )
        response = self._safe_llm_call(messages, temperature=0.3)

        if response:
            content = response.get("content", "")
            result = self._parse_response(content)
            result["llm_scored"] = True
        else:
            result = self._fallback(ats_score, recruiter_score, hm_score)

        self._log_end(result)
        return {"selection_probability": result}

    def _fallback(self, ats_score: float, recruiter_score: float, hm_score: float) -> dict:
        avg = round((ats_score + recruiter_score + hm_score) / 3)
        return {
            "overall_probability": avg,
            "stage_probabilities": {
                "ATS Pass": f"{ats_score}%",
                "Recruiter Shortlist": f"{recruiter_score}%",
                "Technical Interview": f"{hm_score}%",
                "Onsite": f"{round(avg * 0.8)}%",
                "Offer": f"{round(avg * 0.6)}%",
            },
            "key_factors": [],
            "recommendations": ["Set HF_API_KEY in .env for AI-powered selection analysis."],
            "llm_scored": False,
            "fallback_note": "LLM unavailable — showing score-based estimate. Set HF_API_KEY for full AI analysis.",
        }

    def _parse_response(self, content: str) -> dict:
        parsed = self._extract_json(content)
        if parsed:
            return {
                "overall_probability": parsed.get("overall_probability", 50),
                "stage_probabilities": parsed.get("stage_probabilities", {}),
                "key_factors": parsed.get("key_factors", []),
                "recommendations": parsed.get("recommendations", []),
            }
        return {"overall_probability": 50, "stage_probabilities": {}, "key_factors": [], "recommendations": []}


selection_agent = SelectionAgent()
