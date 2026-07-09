from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Float, String, Text, DateTime, JSON, ForeignKey

from database.connection import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True)

    ats_score = Column(Float, nullable=True)
    ats_breakdown = Column(JSON, nullable=True)
    ats_evidence = Column(JSON, nullable=True)

    recruiter_score = Column(Float, nullable=True)
    recruiter_decision = Column(String(20), nullable=True)
    recruiter_confidence = Column(Float, nullable=True)
    recruiter_reasoning = Column(Text, nullable=True)

    hiring_manager_score = Column(Float, nullable=True)
    hiring_manager_decision = Column(String(20), nullable=True)
    hiring_manager_reasoning = Column(Text, nullable=True)

    truthfulness_score = Column(Float, nullable=True)
    truthfulness_details = Column(JSON, nullable=True)

    skill_gap = Column(JSON, nullable=True)
    selection_probability = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, resume_id={self.resume_id}, ats={self.ats_score})>"
