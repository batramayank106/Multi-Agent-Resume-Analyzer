import json
import logging

from agents.base_agent import BaseAgent
from services.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


class CompanyAgent(BaseAgent):

    def __init__(self):
        super().__init__("Company Research Agent")

    def run(self, state: dict) -> dict:
        self._log_start(resume_id=state.get("resume_id"))

        company_name = self._extract_company(state.get("parsed_experience", []), state.get("jd_text", ""))
        jd_text = state.get("jd_text")

        messages = prompt_manager.company_insight(company_name, jd_text)
        response = self._safe_llm_call(messages, temperature=0.3)

        if response:
            content = response.get("content", "")
            result = self._parse_response(content)
            result["llm_scored"] = True
        else:
            result = self._fallback(company_name)

        result["company_name"] = company_name
        self._log_end(result)
        return {"company_result": result}

    def _fallback(self, company_name: str) -> dict:
        return {
            "company_overview": f"{company_name} — LLM research unavailable.",
            "culture_fit_indicators": [],
            "growth_opportunities": [],
            "red_flags": [],
            "industry_position": "Unknown",
            "overall_suitability": "UNKNOWN",
            "culture_score": 0,
            "review_summary": "",
            "pros": [],
            "cons": [],
            "work_life_balance": "Average",
            "career_growth": "Average",
            "llm_scored": False,
            "fallback_note": f"LLM unavailable for {company_name} research. Set HF_API_KEY in .env for full AI analysis.",
        }

    def _extract_company(self, experience: list[dict], jd_text: str) -> str:
        companies = [e.get("company", "") for e in experience if e.get("company")]
        if companies:
            return companies[0]
        return "Unknown Company"

    def _parse_response(self, content: str) -> dict:
        parsed = self._extract_json(content)
        if parsed:
            return {
                "company_overview": parsed.get("company_overview", ""),
                "culture_fit_indicators": parsed.get("culture_fit_indicators", []),
                "growth_opportunities": parsed.get("growth_opportunities", []),
                "red_flags": parsed.get("red_flags", []),
                "industry_position": parsed.get("industry_position", ""),
                "overall_suitability": parsed.get("overall_suitability", "UNKNOWN"),
                "culture_score": parsed.get("culture_score", 0),
                "review_summary": parsed.get("review_summary", ""),
                "pros": parsed.get("pros", []),
                "cons": parsed.get("cons", []),
                "work_life_balance": parsed.get("work_life_balance", "Average"),
                "career_growth": parsed.get("career_growth", "Average"),
            }
        return self._fallback("Unknown")


company_agent = CompanyAgent()
