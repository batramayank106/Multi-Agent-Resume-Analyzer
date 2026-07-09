from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from database.connection import Base


class CompanyInsight(Base):
    __tablename__ = "company_insights"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_name = Column(String(255), nullable=False, unique=True, index=True)
    hiring_patterns = Column(JSON, nullable=True, default=dict)
    technologies = Column(JSON, nullable=True, default=list)
    trends = Column(JSON, nullable=True, default=list)
    desired_skills = Column(JSON, nullable=True, default=list)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<CompanyInsight(id={self.id}, company='{self.company_name}')>"
