import json
import logging

from agents.base_agent import BaseAgent
from services.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


class FamousQuestionsAgent(BaseAgent):

    def __init__(self):
        super().__init__("Famous Questions Agent")

    def run(self, state: dict) -> dict:
        self._log_start(resume_id=state.get("resume_id"))

        company_name = state.get("company_result", {}).get("company_name", "Unknown Company")
        jd_text = state.get("jd_text")

        messages = prompt_manager.famous_questions(company_name, jd_text)
        response = self._safe_llm_call(messages, temperature=0.4)

        if response:
            content = response.get("content", "")
            result = self._parse_response(content)
            result["company"] = company_name
            result["llm_scored"] = True
        else:
            result = self._fallback(company_name)

        self._log_end(result)
        return {"famous_questions_result": result}

    def _fallback(self, company_name: str) -> dict:
        return {
            "company": company_name,
            "questions": [],
            "question_count": 0,
            "llm_scored": False,
            "fallback_note": "LLM unavailable — famous question generation requires AI.",
        }

    def _parse_response(self, content: str) -> dict:
        questions = self._extract_json_array(content)
        if questions:
            return {"questions": questions, "question_count": len(questions)}
        return self._fallback("Unknown")


famous_questions_agent = FamousQuestionsAgent()
