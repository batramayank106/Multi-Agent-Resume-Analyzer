import logging
import math
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from database.connection import get_sync_session
from models.analysis_result import AnalysisResult
from models.resume import Resume
from models.job_description import JobDescription
from models.resume_version import ResumeVersion
from services.version_diff_service import compare_versions
from services.auth_service import get_current_user
from models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vault", tags=["vault"])


class VaultSessionSummary(BaseModel):
    id: int
    ats_score: Optional[float] = None
    recruiter_score: Optional[float] = None
    hm_score: Optional[float] = None
    ats_breakdown: Optional[dict] = None
    created_at: str


class VaultSessionDetail(BaseModel):
    id: int
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None
    ats_result: Optional[dict] = None
    recruiter_result: Optional[dict] = None
    hiring_manager_result: Optional[dict] = None
    simulator_results: Optional[dict] = None
    skill_gap_result: Optional[dict] = None
    truthfulness_result: Optional[dict] = None
    company_result: Optional[dict] = None
    rewrite_result: Optional[dict] = None
    interview_result: Optional[dict] = None
    selection_probability: Optional[dict] = None
    created_at: str


class VersionSummary(BaseModel):
    id: int
    version_number: int
    resume_id: int
    analysis_result_id: Optional[int] = None
    ats_score: Optional[float] = None
    recruiter_score: Optional[float] = None
    hiring_manager_score: Optional[float] = None
    truthfulness_score: Optional[float] = None
    created_at: str


@router.get("/versions")
def list_versions(current_user: User = Depends(get_current_user)):
    session = get_sync_session()
    try:
        rows = session.query(ResumeVersion).order_by(ResumeVersion.created_at.desc()).all()
        return [VersionSummary(
            id=v.id,
            version_number=v.version_number,
            resume_id=v.resume_id,
            analysis_result_id=v.analysis_result_id,
            ats_score=v.ats_score,
            recruiter_score=v.recruiter_score,
            hiring_manager_score=v.hiring_manager_score,
            truthfulness_score=v.truthfulness_score,
            created_at=v.created_at.isoformat() if v.created_at else "",
        ) for v in rows]
    finally:
        session.close()


@router.get("/versions/{version_id}")
def get_version(version_id: int, current_user: User = Depends(get_current_user)):
    session = get_sync_session()
    try:
        v = session.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()
        if not v:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
        return VersionSummary(
            id=v.id,
            version_number=v.version_number,
            resume_id=v.resume_id,
            analysis_result_id=v.analysis_result_id,
            ats_score=v.ats_score,
            recruiter_score=v.recruiter_score,
            hiring_manager_score=v.hiring_manager_score,
            truthfulness_score=v.truthfulness_score,
            created_at=v.created_at.isoformat() if v.created_at else "",
        )
    finally:
        session.close()


@router.get("/sessions")
def list_sessions(current_user: User = Depends(get_current_user)):
    session = get_sync_session()
    try:
        rows = (
            session.query(AnalysisResult)
            .order_by(AnalysisResult.created_at.desc())
            .all()
        )
        def _safe(v):
            if v is None:
                return None
            if isinstance(v, float) and math.isnan(v):
                return None
            return v

        result = []
        for r in rows:
            ats_breakdown = r.ats_breakdown or {}
            ats_score = _safe(r.ats_score)
            if ats_score is None:
                ats_score = _safe(ats_breakdown.get("overall_score")) or _safe(ats_breakdown.get("ats_score"))
            result.append(VaultSessionSummary(
                id=r.id,
                ats_score=ats_score,
                recruiter_score=_safe(r.recruiter_score),
                hm_score=_safe(r.hiring_manager_score),
                ats_breakdown=ats_breakdown,
                created_at=r.created_at.isoformat() if r.created_at else "",
            ))
        return result
    finally:
        session.close()


@router.get("/sessions/{session_id}", response_model=VaultSessionDetail)
def get_session(session_id: int, current_user: User = Depends(get_current_user)):
    session = get_sync_session()
    try:
        ar = session.query(AnalysisResult).filter(AnalysisResult.id == session_id).first()
        if not ar:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        resume_text = None
        jd_text = None
        if ar.resume_id:
            resume = session.query(Resume).filter(Resume.id == ar.resume_id).first()
            if resume:
                resume_text = resume.original_text
        if ar.job_description_id:
            jd = session.query(JobDescription).filter(JobDescription.id == ar.job_description_id).first()
            if jd:
                jd_text = jd.description_text

        def build_agent_result(score, decision=None, reasoning=None, confidence=None, extra=None):
            d = {}
            if score is not None:
                d["score"] = score
            if decision:
                d["decision"] = decision
            if reasoning:
                d["reasoning"] = reasoning
            if confidence is not None:
                d["confidence"] = confidence
            if extra:
                d.update(extra)
            return d if d else None

        ats = {}
        if ar.ats_score is not None or ar.ats_breakdown:
            ats["ats_score"] = ar.ats_score
            if ar.ats_breakdown:
                ats["breakdown"] = ar.ats_breakdown
            if ar.ats_evidence:
                ats["evidence"] = ar.ats_evidence

        return VaultSessionDetail(
            id=ar.id,
            resume_text=resume_text,
            jd_text=jd_text,
            ats_result=ats or None,
            recruiter_result=build_agent_result(ar.recruiter_score, ar.recruiter_decision, ar.recruiter_reasoning, ar.recruiter_confidence),
            hiring_manager_result=build_agent_result(ar.hiring_manager_score, ar.hiring_manager_decision, ar.hiring_manager_reasoning),
            simulator_results=ar.skill_gap,
            skill_gap_result=ar.skill_gap,
            truthfulness_result=build_agent_result(ar.truthfulness_score, extra={"details": ar.truthfulness_details} if ar.truthfulness_details else None),
            selection_probability=ar.selection_probability,
            created_at=ar.created_at.isoformat() if ar.created_at else "",
        )
    finally:
        session.close()


class CompareVersionsRequest(BaseModel):
    v1: int
    v2: int


@router.get("/compare")
def compare_versions_endpoint(v1: int, v2: int, current_user: User = Depends(get_current_user)):
    session = get_sync_session()
    try:
        ar1 = session.query(AnalysisResult).filter(AnalysisResult.id == v1).first()
        ar2 = session.query(AnalysisResult).filter(AnalysisResult.id == v2).first()

        if not ar1 or not ar2:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both sessions not found")

        resume1 = session.query(Resume).filter(Resume.id == ar1.resume_id).first() if ar1.resume_id else None
        resume2 = session.query(Resume).filter(Resume.id == ar2.resume_id).first() if ar2.resume_id else None

        result = compare_versions(ar1, ar2, resume1, resume2)
        return result
    finally:
        session.close()


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, current_user: User = Depends(get_current_user)):
    session = get_sync_session()
    try:
        ar = session.query(AnalysisResult).filter(AnalysisResult.id == session_id).first()
        if not ar:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        session.delete(ar)
        session.commit()
        logger.info(f"Deleted analysis session {session_id}")
    finally:
        session.close()
