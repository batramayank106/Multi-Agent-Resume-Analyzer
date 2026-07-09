import logging
import threading

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_sync_session
from models.resume import Resume
from models.job_description import JobDescription
from models.analysis_result import AnalysisResult
from models.resume_version import ResumeVersion
from schemas.analysis import AnalysisRequest, AnalysisResponse, AnalysisStatusResponse
from agents.graph import run_analysis, run_analysis_with_progress
from services.auth_service import get_optional_user
from services.progress_store import create_run, get_status
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def _build_state(request: AnalysisRequest) -> dict:
    return {
        "resume_id": None,
        "jd_id": None,
        "resume_text": request.resume_text,
        "jd_text": request.jd_text,
        "parsed_skills": request.parsed_skills,
        "parsed_experience": request.parsed_experience,
        "parsed_projects": request.parsed_projects,
        "parsed_education": request.parsed_education,
        "parsed_achievements": request.parsed_achievements,
        "ats_result": None,
        "recruiter_result": None,
        "hiring_manager_result": None,
        "simulator_results": None,
        "skill_gap_result": None,
        "truthfulness_result": None,
        "company_result": None,
        "salary_result": None,
        "rewrite_result": None,
        "interview_result": None,
        "famous_questions_result": None,
        "selection_probability": None,
        "errors": [],
        "status": "started",
    }


def _save_analysis_to_db(request: AnalysisRequest, result: dict) -> int:
    ats = result.get("ats_result") or {}
    recruiter = result.get("recruiter_result") or {}
    hm = result.get("hiring_manager_result") or {}
    truth = result.get("truthfulness_result") or {}

    session = get_sync_session()
    try:
        resume = Resume(
            filename="vault_resume.txt",
            original_text=request.resume_text,
            parsed_skills=request.parsed_skills,
            parsed_experience=request.parsed_experience,
            parsed_projects=request.parsed_projects,
            parsed_education=request.parsed_education,
            parsed_achievements=request.parsed_achievements,
        )
        session.add(resume)
        session.flush()

        jd_id = None
        if request.jd_text:
            jd = JobDescription(
                title="Vault Job Description",
                description_text=request.jd_text,
            )
            session.add(jd)
            session.flush()
            jd_id = jd.id

        analysis = AnalysisResult(
            resume_id=resume.id,
            job_description_id=jd_id,
            ats_score=ats.get("overall_score") or ats.get("ats_score"),
            ats_breakdown=ats.get("breakdown"),
            ats_evidence=ats.get("evidence"),
            recruiter_score=recruiter.get("recruiter_score"),
            recruiter_decision=recruiter.get("decision"),
            recruiter_confidence=recruiter.get("confidence"),
            recruiter_reasoning=recruiter.get("reasoning"),
            hiring_manager_score=hm.get("hiring_manager_score"),
            hiring_manager_decision=hm.get("decision"),
            hiring_manager_reasoning=hm.get("reasoning"),
            truthfulness_score=truth.get("truthfulness_score"),
            truthfulness_details=truth.get("details") or truth.get("flagged_items"),
            skill_gap=result.get("skill_gap_result"),
            selection_probability=result.get("selection_probability"),
        )
        session.add(analysis)
        session.commit()
        analysis_id = analysis.id

        existing_versions = session.query(ResumeVersion).filter(
            ResumeVersion.resume_id == resume.id
        ).count()
        version = ResumeVersion(
            resume_id=resume.id,
            analysis_result_id=analysis_id,
            version_number=existing_versions + 1,
            content_text=request.resume_text,
            ats_score=ats.get("overall_score") or ats.get("ats_score"),
            recruiter_score=recruiter.get("recruiter_score"),
            hiring_manager_score=hm.get("hiring_manager_score"),
            truthfulness_score=truth.get("truthfulness_score"),
            selection_probability=result.get("selection_probability"),
        )
        session.add(version)
        session.commit()

        return analysis_id
    finally:
        session.close()


@router.post("/full", response_model=AnalysisResponse)
async def full_analysis(request: AnalysisRequest, current_user: User | None = Depends(get_optional_user)):
    state = _build_state(request)

    try:
        result = run_analysis(state)
        analysis_id = _save_analysis_to_db(request, result)

        return AnalysisResponse(
            id=analysis_id,
            status=result.get("status", "completed"),
            ats_result=result.get("ats_result"),
            recruiter_result=result.get("recruiter_result"),
            hiring_manager_result=result.get("hiring_manager_result"),
            simulator_results=result.get("simulator_results"),
            skill_gap_result=result.get("skill_gap_result"),
            truthfulness_result=result.get("truthfulness_result"),
            company_result=result.get("company_result"),
            salary_result=result.get("salary_result"),
            rewrite_result=result.get("rewrite_result"),
            interview_result=result.get("interview_result"),
            famous_questions_result=result.get("famous_questions_result"),
            selection_probability=result.get("selection_probability"),
            errors=result.get("errors", []),
        )
    except Exception as e:
        logger.error(f"Full analysis failed: {e}")
        return AnalysisResponse(
            status="error",
            errors=[str(e)],
        )


@router.post("/stream")
async def stream_analysis(request: AnalysisRequest, current_user: User | None = Depends(get_optional_user)):
    run_id = create_run()
    state = _build_state(request)

    def _run():
        try:
            result = run_analysis_with_progress(state, run_id)
            try:
                _save_analysis_to_db(request, result)
                logger.info("Stream analysis saved to DB")
            except Exception as save_err:
                logger.error(f"Failed to save stream analysis to DB: {save_err}")
        except Exception as e:
            logger.error(f"Stream analysis failed: {e}")
            from services.progress_store import set_error
            set_error(run_id, str(e))

    threading.Thread(target=_run, daemon=True).start()

    return {"run_id": run_id, "status": "started"}


@router.get("/status/{run_id}", response_model=AnalysisStatusResponse)
async def analysis_status(run_id: str):
    status = get_status(run_id)
    return AnalysisStatusResponse(**status)
