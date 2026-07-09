import json
import logging

from agents.base_agent import BaseAgent
from services.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


class SkillGapAgent(BaseAgent):

    def __init__(self):
        super().__init__("Skill Gap Agent")

    def run(self, state: dict) -> dict:
        self._log_start(resume_id=state.get("resume_id"))

        resume_skills = state.get("parsed_skills", [])
        jd_text = state.get("jd_text", "")
        jd_requirements = self._extract_requirements(jd_text)

        messages = prompt_manager.skill_gap(resume_skills, jd_requirements)
        response = self._safe_llm_call(messages, temperature=0.3)

        if response:
            content = response.get("content", "")
            result = self._parse_response(content)
            result["llm_scored"] = True
        else:
            result = self._fallback(resume_skills, jd_requirements)

        self._log_end(result)
        return {"skill_gap_result": result}

    def _fallback(self, resume_skills: list[str], jd_requirements: list[str]) -> dict:
        missing = [r for r in jd_requirements if r.lower() not in [s.lower() for s in resume_skills]]
        return {
            "required_skills": jd_requirements[:10],
            "preferred_skills": [],
            "missing_skills": missing[:10],
            "priority_levels": {},
            "gap_severity": "unknown",
            "suggested_additions": [],
            "llm_scored": False,
            "fallback_note": "LLM unavailable — showing basic skill comparison. Set HF_API_KEY in .env for full AI analysis.",
        }

    def _extract_requirements(self, jd_text: str) -> list[str]:
        if not jd_text:
            return []
        lines = [l.strip() for l in jd_text.split("\n") if l.strip()]
        return lines[:20]

    def _parse_response(self, content: str) -> dict:
        parsed = self._extract_json(content)
        if parsed:
            return {
                "required_skills": parsed.get("required_skills", []),
                "preferred_skills": parsed.get("preferred_skills", []),
                "missing_skills": parsed.get("missing_skills", []),
                "priority_levels": parsed.get("priority_levels", {}),
                "gap_severity": parsed.get("gap_severity", "unknown"),
                "suggested_additions": parsed.get("suggested_additions", []),
            }
        return {"gap_severity": "unknown", "missing_skills": []}


skill_gap_agent = SkillGapAgent()
