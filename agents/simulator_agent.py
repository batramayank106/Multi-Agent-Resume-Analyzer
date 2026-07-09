import json
import logging

from agents.base_agent import BaseAgent
from services.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)

PERSONAS = ["ATS", "HR", "Engineering Manager"]


class SimulatorAgent(BaseAgent):

    def __init__(self):
        super().__init__("Recruiter Simulator")

    def run(self, state: dict) -> dict:
        self._log_start(resume_id=state.get("resume_id"))

        resume_text = state.get("resume_text", "")
        results = {}
        any_llm = False

        for persona in PERSONAS:
            messages = prompt_manager.recruiter_simulator(resume_text, persona)
            response = self._safe_llm_call(messages, temperature=0.3)
            if response:
                content = response.get("content", "")
                parsed = self._parse_response(content)
                parsed["llm_scored"] = True
                any_llm = True
            else:
                parsed = self._fallback(persona)
            results[persona] = parsed

        aggregated = self._aggregate(results)
        aggregated["llm_scored"] = any_llm
        if not any_llm:
            aggregated["fallback_note"] = "LLM scoring unavailable. Set HF_API_KEY in .env for AI-powered simulation."

        self._log_end(aggregated)
        return {"simulator_results": aggregated}

    def _fallback(self, persona: str) -> dict:
        return {
            "decision": "UNKNOWN",
            "confidence": 0,
            "suggestions": "",
            "explanation": f"LLM unavailable for {persona} persona. Set HF_API_KEY in .env.",
            "llm_scored": False,
        }

    def _parse_response(self, content: str) -> dict:
        parsed = self._extract_json(content)
        if parsed:
            return {
                "decision": parsed.get("decision", "REJECT"),
                "confidence": int(parsed.get("confidence", 50)),
                "suggestions": parsed.get("suggestions", ""),
                "explanation": parsed.get("explanation", ""),
            }
        return {"decision": "REJECT", "confidence": 50, "suggestions": "", "explanation": content[:500]}

    def _aggregate(self, results: dict) -> dict:
        decisions = [r["decision"] for r in results.values()]
        confidences = [r["confidence"] for r in results.values()]
        passes = sum(1 for d in decisions if d == "PASS")

        overall_score = round(sum(confidences) / len(confidences)) if confidences else 50

        if passes >= 2:
            overall_decision = "PASS"
        elif passes == 1:
            overall_decision = "CONDITIONAL"
        else:
            overall_decision = "REJECT"

        return {
            "overall_decision": overall_decision,
            "overall_confidence": overall_score,
            "persona_results": results,
            "summary": f"{passes}/{len(PERSONAS)} personas would pass this resume",
        }


simulator_agent = SimulatorAgent()
