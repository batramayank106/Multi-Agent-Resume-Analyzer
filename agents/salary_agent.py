import json
import logging

from agents.base_agent import BaseAgent
from services.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


class SalaryAgent(BaseAgent):

    def __init__(self):
        super().__init__("Salary Estimation Agent")

    def run(self, state: dict) -> dict:
        self._log_start(resume_id=state.get("resume_id"))

        company_name = state.get("company_result", {}).get("company_name", "Unknown Company")
        jd_text = state.get("jd_text")
        parsed_skills = state.get("parsed_skills", [])

        messages = prompt_manager.salary_estimate(company_name, jd_text, parsed_skills)
        response = self._safe_llm_call(messages, temperature=0.3)

        if response:
            content = response.get("content", "")
            result = self._parse_response(content)
            result["llm_scored"] = True
        else:
            result = self._fallback(company_name)

        self._log_end(result)
        return {"salary_result": result}

    def _fallback(self, company_name: str) -> dict:
        return {
            "salary_range": "N/A",
            "currency": "INR",
            "confidence": "Low",
            "factors": ["LLM unavailable for salary estimation"],
            "source": "LLM Knowledge",
            "llm_scored": False,
            "fallback_note": f"LLM unavailable for salary estimation. Set HF_API_KEY in .env.",
        }

    def _parse_response(self, content: str) -> dict:
        parsed = self._extract_json(content)
        if parsed:
            return {
                "salary_range": parsed.get("salary_range", "N/A"),
                "currency": parsed.get("currency", "INR"),
                "confidence": parsed.get("confidence", "Low"),
                "factors": parsed.get("factors", []),
                "source": parsed.get("source", "LLM Knowledge"),
            }
        return self._fallback("Unknown")


salary_agent = SalaryAgent()
