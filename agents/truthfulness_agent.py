import json
import logging

from agents.base_agent import BaseAgent
from services.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


class TruthfulnessAgent(BaseAgent):

    def __init__(self):
        super().__init__("Truthfulness Agent")

    def run(self, state: dict) -> dict:
        self._log_start(resume_id=state.get("resume_id"))

        resume_text = state.get("resume_text", "")

        messages = prompt_manager.truthfulness_check(resume_text)
        response = self._safe_llm_call(messages, temperature=0.2)

        if response:
            content = response.get("content", "")
            result = self._parse_response(content)
            result["llm_scored"] = True
        else:
            result = self._fallback()

        self._log_end(result)
        return {"truthfulness_result": result}

    def _fallback(self) -> dict:
        return {
            "truthfulness_score": 50,
            "flagged_items": [],
            "llm_scored": False,
            "fallback_note": "LLM unavailable — no truthfulness check performed. Set HF_API_KEY in .env for full AI analysis.",
        }

    def _parse_response(self, content: str) -> dict:
        parsed = self._extract_json(content)
        if parsed:
            return {
                "truthfulness_score": parsed.get("truthfulness_score", 50),
                "flagged_items": parsed.get("flagged_items", []),
            }
        return self._fallback()


truthfulness_agent = TruthfulnessAgent()
