import logging

from agents.base_agent import BaseAgent
from services.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


class HiringManagerAgent(BaseAgent):

    def __init__(self):
        super().__init__("Hiring Manager Agent")

    def run(self, state: dict) -> dict:
        self._log_start(resume_id=state.get("resume_id"))

        resume_text = state.get("resume_text", "")
        jd_text = state.get("jd_text")

        messages = prompt_manager.hiring_manager_review(resume_text, jd_text)
        response = self._safe_llm_call(messages, temperature=0.3)

        if response:
            content = response.get("content", "")
            result = self._parse_response(content)
            result["llm_scored"] = True
        else:
            result = self._fallback()

        self._log_end(result)
        return {"hiring_manager_result": result}

    def _fallback(self) -> dict:
        return {
            "hiring_manager_score": 50,
            "decision": "UNKNOWN",
            "reasoning": "LLM scoring unavailable. Set HF_API_KEY in .env for AI-powered hiring manager review.",
            "llm_scored": False,
            "fallback_note": "Showing neutral score — set HF_API_KEY for full AI analysis.",
            "dimension_scores": {},
        }

    def _parse_response(self, content: str) -> dict:
        parsed = self._extract_json(content)
        if parsed:
            return {
                "hiring_manager_score": parsed.get("hiring_manager_score", 50),
                "decision": parsed.get("decision", "REJECT"),
                "reasoning": parsed.get("reasoning", ""),
                "dimension_scores": parsed.get("dimension_scores", {}),
            }
        return self._fallback()


hiring_manager_agent = HiringManagerAgent()
