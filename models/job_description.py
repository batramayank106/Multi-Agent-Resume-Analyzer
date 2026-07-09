from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from database.connection import Base


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    description_text = Column(Text, nullable=False)
    parsed_requirements = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<JobDescription(id={self.id}, title='{self.title}')>"
