import json
import logging

from agents.base_agent import BaseAgent
from services.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


class RecruiterAgent(BaseAgent):

    def __init__(self):
        super().__init__("Recruiter Agent")

    def run(self, state: dict) -> dict:
        self._log_start(resume_id=state.get("resume_id"))

        resume_text = state.get("resume_text", "")
        jd_text = state.get("jd_text")

        messages = prompt_manager.recruiter_review(resume_text, jd_text)
        response = self._safe_llm_call(messages, temperature=0.3)

        if response:
            content = response.get("content", "")
            result = self._parse_response(content)
            result["llm_scored"] = True
        else:
            result = self._fallback()

        self._log_end(result)
        return {"recruiter_result": result}

    def _fallback(self) -> dict:
        return {
            "recruiter_score": 50,
            "decision": "UNKNOWN",
            "confidence": 0,
            "reasoning": "LLM scoring unavailable. Set HF_API_KEY in .env for AI-powered recruiter review.",
            "llm_scored": False,
            "fallback_note": "Showing neutral score — set HF_API_KEY for full AI analysis.",
            "dimension_scores": {},
        }

    def _parse_response(self, content: str) -> dict:
        parsed = self._extract_json(content)
        if parsed:
            return {
                "recruiter_score": parsed.get("recruiter_score", 50),
                "decision": parsed.get("decision", "REJECT"),
                "confidence": int(parsed.get("confidence", 50)),
                "reasoning": parsed.get("reasoning", ""),
                "dimension_scores": parsed.get("dimension_scores", {}),
            }
        return self._fallback()


recruiter_agent = RecruiterAgent()
