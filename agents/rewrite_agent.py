import logging

from agents.base_agent import BaseAgent
from services.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


class RewriteAgent(BaseAgent):

    def __init__(self):
        super().__init__("Resume Rewrite Agent")

    def run(self, state: dict) -> dict:
        self._log_start(resume_id=state.get("resume_id"))

        resume_text = state.get("resume_text", "")
        suggestions = self._build_suggestions(state)

        messages = prompt_manager.resume_rewrite(resume_text, suggestions)
        response = self._safe_llm_call(messages, temperature=0.4)

        if response:
            content = response.get("content", "")
            result = {
                "original_resume": resume_text[:200],
                "suggestions_summary": suggestions[:500],
                "rewritten_resume": content,
                "llm_scored": True,
            }
        else:
            result = self._fallback(resume_text, suggestions)

        self._log_end(result)
        return {"rewrite_result": result}

    def _fallback(self, resume_text: str, suggestions: str) -> dict:
        return {
            "original_resume": resume_text[:200],
            "suggestions_summary": suggestions[:500],
            "rewritten_resume": "",
            "llm_scored": False,
            "fallback_note": "LLM unavailable — resume rewrite requires AI. Set HF_API_KEY in .env for full AI analysis.",
        }

    def _build_suggestions(self, state: dict) -> str:
        parts = []
        ats = state.get("ats_result", {})
        recruiter = state.get("recruiter_result", {})

        missing_kw = ats.get("missing_keywords", [])
        if missing_kw:
            parts.append(f"Add missing keywords: {', '.join(missing_kw)}")

        if recruiter.get("reasoning"):
            parts.append(f"Recruiter feedback: {recruiter['reasoning']}")

        return "\n".join(parts) if parts else "General improvement suggestions."


rewrite_agent = RewriteAgent()
