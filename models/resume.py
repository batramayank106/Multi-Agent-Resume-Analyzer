from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from database.connection import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    original_text = Column(Text, nullable=True)
    parsed_skills = Column(JSON, nullable=True, default=list)
    parsed_experience = Column(JSON, nullable=True, default=list)
    parsed_projects = Column(JSON, nullable=True, default=list)
    parsed_education = Column(JSON, nullable=True, default=list)
    parsed_achievements = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<Resume(id={self.id}, filename='{self.filename}')>"
