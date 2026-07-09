from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Float, Text, DateTime, JSON, ForeignKey

from database.connection import Base


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    analysis_result_id = Column(Integer, ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=True, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    content_text = Column(Text, nullable=True)
    content_tex = Column(Text, nullable=True)
    ats_score = Column(Float, nullable=True)
    recruiter_score = Column(Float, nullable=True)
    hiring_manager_score = Column(Float, nullable=True)
    truthfulness_score = Column(Float, nullable=True)
    selection_probability = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<ResumeVersion(id={self.id}, resume_id={self.resume_id}, v{self.version_number})>"
