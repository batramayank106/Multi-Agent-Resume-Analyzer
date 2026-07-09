import json
import logging
import re
from typing import Optional

from agents.base_agent import BaseAgent
from services.prompt_manager import prompt_manager
from services.llm_manager import llm_manager
from config import settings

logger = logging.getLogger(__name__)

ATS_WEIGHTS = {
    "keyword_match": 30,
    "skill_match": 20,
    "experience_match": 15,
    "project_match": 15,
    "achievements": 10,
    "education": 5,
    "formatting": 5,
}

SCORE_CATEGORIES = [
    (0, 40, "Poor"),
    (40, 60, "Average"),
    (60, 75, "Good"),
    (75, 90, "Strong"),
    (90, 100, "Exceptional"),
]


class ATSAgent(BaseAgent):

    def __init__(self):
        super().__init__("ATS Agent")

    def _get_category_label(self, score: int) -> str:
        for low, high, label in SCORE_CATEGORIES:
            if low <= score < high:
                return label
        return "Exceptional" if score == 100 else "Poor"

    def _call_llm(self, resume_text: str, jd_text: Optional[str]) -> Optional[dict]:
        messages = prompt_manager.ats_analysis(resume_text, jd_text)
        result = self._safe_llm_call(messages, temperature=0.3)

        if not result:
            return None

        content = result.get("content", "")
        parsed = self._extract_json(content)
        if parsed and "overall_score" in parsed:
            return parsed

        if parsed:
            for score_key in ("overall_score", "overall score", "score", "ats_score"):
                if score_key in parsed:
                    parsed["overall_score"] = parsed[score_key]
                    return parsed

        logger.warning("ATS LLM response missing expected keys, falling back")
        return None

    # Fallback — rule-based scoring used when LLM is unavailable
    def _fallback_keyword_score(self, resume_text: str, jd_text: Optional[str]) -> dict:
        if not jd_text:
            return {"score": 50, "matched": [], "missing": [], "evidence": ["No job description provided for comparison"]}

        resume_lower = resume_text.lower()
        jd_lower = jd_text.lower()

        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
                       "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
                       "been", "being", "have", "has", "had", "do", "does", "did", "will",
                       "would", "could", "should", "may", "might", "shall", "can", "need",
                       "must", "this", "that", "these", "those", "it", "its", "you", "your",
                       "we", "our", "they", "their", "he", "she", "his", "her", "not", "no",
                       "nor", "all", "each", "every", "both", "few", "more", "most", "other",
                       "some", "such", "only", "own", "same", "so", "than", "too", "very",
                       "just", "about", "above", "after", "again", "all", "also", "any",
                       "because", "before", "between", "during", "etc", "including", "within",
                       "without", "per", "under", "over", "into", "through", "while", "where",
                       "which", "who", "whom", "what", "when", "why", "how"}

        jd_words = re.findall(r'[a-zA-Z][a-zA-Z0-9#+\-.]+', jd_lower)
        word_freq = {}
        for w in jd_words:
            if w not in stop_words and len(w) > 2:
                word_freq[w] = word_freq.get(w, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: -x[1])
        keywords = {w for w, freq in sorted_words[:30] if freq >= 2}

        matched = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', resume_lower)]
        missing = [kw for kw in keywords if not re.search(r'\b' + re.escape(kw) + r'\b', resume_lower)]

        score = 50 if len(keywords) == 0 else round((len(matched) / len(keywords)) * 100)

        evidence = []
        for kw in matched:
            evidence.append(f"Found keyword '{kw}' in both resume and JD")
        for kw in missing:
            evidence.append(f"Missing keyword '{kw}' — found in JD but not in resume")

        return {"score": score, "matched": matched, "missing": missing, "evidence": evidence}

    def _fallback_skill_score(self, parsed_skills: list[str], jd_text: Optional[str]) -> dict:
        if not parsed_skills:
            return {"score": 30, "evidence": ["No skills section found in resume"]}
        if not jd_text:
            return {"score": 70, "evidence": ["Skills present but no JD to compare against"]}

        jd_lower = jd_text.lower()
        matched_skills = [s for s in parsed_skills if s.lower() in jd_lower]
        score = 0 if len(parsed_skills) == 0 else round((len(matched_skills) / len(parsed_skills)) * 100)
        return {"score": score, "matched_skills": matched_skills, "evidence": [f"Matched {len(matched_skills)}/{len(parsed_skills)} skills with job description"]}

    def _fallback_experience_score(self, parsed_experience: list[dict]) -> dict:
        if not parsed_experience:
            return {"score": 20, "evidence": ["No experience section found"]}
        years = len(parsed_experience)
        score = 90 if years >= 3 else (70 if years >= 2 else (50 if years >= 1 else 30))
        return {"score": score, "years_entries": years, "evidence": [f"{years} experience entries found"]}

    def _fallback_project_score(self, parsed_projects: list[dict]) -> dict:
        if not parsed_projects:
            return {"score": 20, "evidence": ["No projects section found"]}
        count = len(parsed_projects)
        score = 90 if count >= 3 else (70 if count >= 2 else (50 if count >= 1 else 20))
        return {"score": score, "project_count": count, "evidence": [f"{count} projects listed"]}

    def _fallback_achievements_score(self, parsed_achievements: list[str]) -> dict:
        if not parsed_achievements:
            return {"score": 20, "evidence": ["No achievements section found"]}
        count = len(parsed_achievements)
        score = 90 if count >= 3 else (70 if count >= 2 else (50 if count >= 1 else 20))
        return {"score": score, "achievement_count": count, "evidence": [f"{count} achievements listed"]}

    def _fallback_education_score(self, parsed_education: list[dict]) -> dict:
        if not parsed_education:
            return {"score": 30, "evidence": ["No education section found"]}
        return {"score": 80, "degrees": len(parsed_education), "evidence": [f"{len(parsed_education)} degrees listed"]}

    def _fallback_formatting_score(self, resume_text: str) -> dict:
        issues = []
        sections = ["experience", "education", "skills", "projects"]
        missing_sections = [s for s in sections if s not in resume_text.lower()]
        if missing_sections:
            issues.append(f"Missing sections: {', '.join(missing_sections)}")
        for line in resume_text.split("\n"):
            if len(line) > 200:
                issues.append("Very long line detected (poor formatting)")
                break
        deduction = len(issues) * 15
        score = max(0, 100 - deduction)
        return {"score": score, "issues": issues, "evidence": issues or ["Formatting looks clean"]}

    def _fallback_run(self, state: dict) -> dict:
        resume_text = state.get("resume_text", "")
        jd_text = state.get("jd_text")
        parsed_skills = state.get("parsed_skills", [])
        parsed_experience = state.get("parsed_experience", [])
        parsed_projects = state.get("parsed_projects", [])
        parsed_achievements = state.get("parsed_achievements", [])
        parsed_education = state.get("parsed_education", [])

        keyword = self._fallback_keyword_score(resume_text, jd_text)
        skill = self._fallback_skill_score(parsed_skills, jd_text)
        experience = self._fallback_experience_score(parsed_experience)
        project = self._fallback_project_score(parsed_projects)
        achievements = self._fallback_achievements_score(parsed_achievements)
        education = self._fallback_education_score(parsed_education)
        formatting = self._fallback_formatting_score(resume_text)

        overall = round(
            keyword["score"] * ATS_WEIGHTS["keyword_match"] / 100
            + skill["score"] * ATS_WEIGHTS["skill_match"] / 100
            + experience["score"] * ATS_WEIGHTS["experience_match"] / 100
            + project["score"] * ATS_WEIGHTS["project_match"] / 100
            + achievements["score"] * ATS_WEIGHTS["achievements"] / 100
            + education["score"] * ATS_WEIGHTS["education"] / 100
            + formatting["score"] * ATS_WEIGHTS["formatting"] / 100
        )

        breakdown = {}
        for key, cat in [("keyword_match", keyword), ("skill_match", skill),
                          ("experience_match", experience), ("project_match", project),
                          ("achievements", achievements), ("education", education),
                          ("formatting", formatting)]:
            breakdown[key] = {
                "score": cat["score"],
                "weight": ATS_WEIGHTS[key],
                "contribution": round(cat["score"] * ATS_WEIGHTS[key] / 100),
            }

        evidence = []
        for key, cat in [("keyword_match", keyword), ("skill_match", skill),
                          ("experience_match", experience), ("project_match", project),
                          ("achievements", achievements), ("education", education),
                          ("formatting", formatting)]:
            evidence.append({"category": key, "deductions": cat.get("evidence", [])})

        return {
            "overall_score": overall,
            "category_label": self._get_category_label(overall),
            "breakdown": breakdown,
            "evidence": evidence,
            "missing_keywords": keyword.get("missing", []),
            "matched_keywords": keyword.get("matched", []),
            "llm_scored": False,
            "fallback_note": "LLM scoring unavailable — showing rule-based estimate. Set HF_API_KEY in .env for AI-powered analysis.",
        }

    def run(self, state: dict) -> dict:
        self._log_start(resume_id=state.get("resume_id"))

        resume_text = state.get("resume_text", "")
        jd_text = state.get("jd_text")

        llm_output = self._call_llm(resume_text, jd_text)

        if llm_output:
            cat_scores_raw = llm_output.get("category_scores", {})
            KEY_MAP = {
                "Keyword Match": "keyword_match", "keyword_match": "keyword_match",
                "Skill Match": "skill_match", "skill_match": "skill_match",
                "Experience Match": "experience_match", "experience_match": "experience_match",
                "Project Match": "project_match", "project_match": "project_match",
                "Achievements": "achievements", "achievements": "achievements",
                "Education": "education", "education": "education",
                "Formatting": "formatting", "formatting": "formatting",
            }
            cat_scores = {}
            for raw_key, val in cat_scores_raw.items():
                normalized = KEY_MAP.get(raw_key)
                if normalized:
                    cat_scores[normalized] = max(0, min(100, int(val)))
            for key in ATS_WEIGHTS:
                if key not in cat_scores:
                    cat_scores[key] = 0

            overall = max(0, min(100, int(llm_output.get("overall_score", 0))))

            breakdown = {}
            for key, weight in ATS_WEIGHTS.items():
                score = cat_scores.get(key, 0)
                breakdown[key] = {"score": score, "weight": weight, "contribution": round(score * weight / 100)}

            evidence = []
            for ev in llm_output.get("evidence", []):
                evidence.append({"category": ev.get("category", ""), "deductions": ev.get("deductions", [])})

            result = {
                "overall_score": overall,
                "category_label": self._get_category_label(overall),
                "breakdown": breakdown,
                "evidence": evidence,
                "missing_keywords": llm_output.get("missing_keywords", []),
                "matched_keywords": llm_output.get("matched_keywords", []),
                "llm_scored": True,
            }
        else:
            result = self._fallback_run(state)
            logger.warning(f"Fallback used: {result.get('fallback_note', '')}")

        self._log_end(result)
        return {"ats_result": result}


ats_agent = ATSAgent()
