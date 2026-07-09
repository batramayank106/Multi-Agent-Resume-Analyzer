import json
import logging

from agents.base_agent import BaseAgent
from services.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


class InterviewAgent(BaseAgent):

    def __init__(self):
        super().__init__("Interview Prep Agent")

    def run(self, state: dict) -> dict:
        self._log_start(resume_id=state.get("resume_id"))

        resume_text = state.get("resume_text", "")
        jd_text = state.get("jd_text")

        messages = prompt_manager.interview_questions(resume_text, jd_text)
        response = self._safe_llm_call(messages, temperature=0.4)

        if response:
            content = response.get("content", "")
            result = self._parse_response(content)
            result["llm_scored"] = True
        else:
            result = self._fallback()

        self._log_end(result)
        return {"interview_result": result}

    def _fallback(self) -> dict:
        return {
            "questions": [],
            "question_count": 0,
            "llm_scored": False,
            "fallback_note": "LLM unavailable — question generation requires AI. Set HF_API_KEY in .env for full AI analysis.",
        }

    def _parse_response(self, content: str) -> dict:
        questions = self._extract_json_array(content)
        if questions:
            return {"questions": questions, "question_count": len(questions)}
        return self._fallback()


interview_agent = InterviewAgent()
