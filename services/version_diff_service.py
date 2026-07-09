import difflib
import re
from typing import Optional

from models.analysis_result import AnalysisResult
from models.resume import Resume


def _extract_keywords(text: str) -> set[str]:
    words = re.findall(r"[A-Za-z][A-Za-z+#.-]+", text or "")
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "shall", "can", "need",
        "this", "that", "these", "those", "it", "its", "you", "your", "his",
        "her", "their", "our", "we", "they", "he", "she", "not", "no", "nor",
        "about", "into", "over", "after", "before", "between", "under",
        "above", "below", "up", "down", "out", "off", "just", "also", "very",
        "too", "more", "most", "some", "any", "each", "every", "all", "both",
        "few", "several", "than", "then", "else", "other", "such", "only",
        "own", "same", "so", "than", "too", "very", "just", "because", "but",
        "and", "resume", "experience", "skills", "education", "projects",
        "achievements", "summary", "work", "history", "professional",
    }
    return {w.lower() for w in words if w.lower() not in stopwords and len(w) > 1}


def _extract_bullets(text: str) -> list[str]:
    lines = text.splitlines() if text else []
    bullets = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("-") or stripped.startswith("•") or stripped.startswith("*"):
            bullets.append(stripped.lstrip("-•* ").strip())
        elif re.match(r"^\d+[.)]", stripped):
            bullets.append(re.sub(r"^\d+[.)]\s*", "", stripped).strip())
    return bullets


def compare_versions(
    analysis_a: AnalysisResult,
    analysis_b: AnalysisResult,
    resume_a: Optional[Resume] = None,
    resume_b: Optional[Resume] = None,
) -> dict:
    text_a = resume_a.original_text if resume_a else ""
    text_b = resume_b.original_text if resume_b else ""

    keywords_a = _extract_keywords(text_a)
    keywords_b = _extract_keywords(text_b)

    skills_a = set((resume_a.parsed_skills or []) if resume_a else [])
    skills_b = set((resume_b.parsed_skills or []) if resume_b else [])

    bullets_a = set(_extract_bullets(text_a))
    bullets_b = set(_extract_bullets(text_b))

    proj_a = set()
    proj_b = set()
    if resume_a and resume_a.parsed_projects:
        for p in resume_a.parsed_projects:
            if isinstance(p, dict):
                proj_a.add(p.get("name", ""))
            elif isinstance(p, str):
                proj_a.add(p)
    if resume_b and resume_b.parsed_projects:
        for p in resume_b.parsed_projects:
            if isinstance(p, dict):
                proj_b.add(p.get("name", ""))
            elif isinstance(p, str):
                proj_b.add(p)

    score_deltas = {
        "ats": round((analysis_b.ats_score or 0) - (analysis_a.ats_score or 0), 1),
        "recruiter": round((analysis_b.recruiter_score or 0) - (analysis_a.recruiter_score or 0), 1),
        "hm": round((analysis_b.hiring_manager_score or 0) - (analysis_a.hiring_manager_score or 0), 1),
    }

    common_skills = skills_a & skills_b
    added_skills = skills_b - skills_a
    removed_skills = skills_a - skills_b

    common_keywords = keywords_a & keywords_b
    added_keywords = keywords_b - keywords_a
    removed_keywords = keywords_a - keywords_b

    improved_bullets = bullets_a & bullets_b
    added_bullets = bullets_b - bullets_a
    removed_bullets = bullets_a - bullets_b

    added_projects = proj_b - proj_a
    removed_projects = proj_a - proj_b

    summary_parts = []
    if score_deltas["ats"] > 0:
        summary_parts.append(f"ATS score improved by {score_deltas['ats']} points")
    elif score_deltas["ats"] < 0:
        summary_parts.append(f"ATS score decreased by {abs(score_deltas['ats'])} points")
    else:
        summary_parts.append("ATS score remained unchanged")

    if added_skills:
        s = ", ".join(sorted(added_skills)[:5])
        summary_parts.append(f"added skills: {s}")
    if removed_skills:
        s = ", ".join(sorted(removed_skills)[:5])
        summary_parts.append(f"removed skills: {s}")
    if added_bullets:
        summary_parts.append(f"added {len(added_bullets)} bullet points")
    if removed_bullets:
        summary_parts.append(f"removed {len(removed_bullets)} bullet points")
    if added_projects:
        s = ", ".join(sorted(added_projects)[:3])
        summary_parts.append(f"added projects: {s}")

    if not summary_parts:
        summary_parts.append("No significant changes detected between versions")

    return {
        "score_deltas": score_deltas,
        "skills": {
            "added": sorted(added_skills),
            "removed": sorted(removed_skills),
            "common": sorted(common_skills),
        },
        "keywords": {
            "added": sorted(added_keywords)[:20],
            "removed": sorted(removed_keywords)[:20],
            "common_count": len(common_keywords),
        },
        "bullet_changes": {
            "improved": len(improved_bullets),
            "added": len(added_bullets),
            "removed": len(removed_bullets),
        },
        "project_changes": {
            "added": sorted(added_projects),
            "removed": sorted(removed_projects),
        },
        "improvement_summary": ". ".join(part.capitalize() for part in summary_parts) + ".",
        "version_a": {
            "score": analysis_a.ats_score,
            "skills": sorted(skills_a),
            "date": analysis_a.created_at.isoformat() if analysis_a.created_at else "",
        },
        "version_b": {
            "score": analysis_b.ats_score,
            "skills": sorted(skills_b),
            "date": analysis_b.created_at.isoformat() if analysis_b.created_at else "",
        },
    }
