from pydantic import BaseModel
from typing import Optional, Any


class AnalysisRequest(BaseModel):
    resume_text: str
    jd_text: Optional[str] = None
    parsed_skills: list[str] = []
    parsed_experience: list[dict] = []
    parsed_projects: list[dict] = []
    parsed_education: list[dict] = []
    parsed_achievements: list[str] = []


class AnalysisResponse(BaseModel):
    id: Optional[int] = None
    status: str
    ats_result: Optional[dict] = None
    recruiter_result: Optional[dict] = None
    hiring_manager_result: Optional[dict] = None
    simulator_results: Optional[dict] = None
    skill_gap_result: Optional[dict] = None
    truthfulness_result: Optional[dict] = None
    company_result: Optional[dict] = None
    salary_result: Optional[dict] = None
    rewrite_result: Optional[dict] = None
    interview_result: Optional[dict] = None
    famous_questions_result: Optional[dict] = None
    selection_probability: Optional[dict] = None
    errors: list[str] = []


class AnalysisStatusResponse(BaseModel):
    status: str
    current_agent: Optional[str] = None
    current_agent_index: int = -1
    results: dict[str, Any] = {}
    errors: list[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
