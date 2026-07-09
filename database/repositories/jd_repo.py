from models.job_description import JobDescription
from database.connection import SyncSessionLocal


class JobDescriptionRepository:

    @staticmethod
    def create(title: str = None, company: str = None, description_text: str = "") -> JobDescription:
        with SyncSessionLocal() as session:
            jd = JobDescription(title=title, company=company, description_text=description_text)
            session.add(jd)
            session.commit()
            session.refresh(jd)
            return jd

    @staticmethod
    def get_by_id(jd_id: int) -> JobDescription | None:
        with SyncSessionLocal() as session:
            return session.query(JobDescription).filter(JobDescription.id == jd_id).first()

    @staticmethod
    def get_all() -> list[JobDescription]:
        with SyncSessionLocal() as session:
            return session.query(JobDescription).order_by(JobDescription.created_at.desc()).all()

    @staticmethod
    def delete(jd_id: int) -> bool:
        with SyncSessionLocal() as session:
            jd = session.query(JobDescription).filter(JobDescription.id == jd_id).first()
            if not jd:
                return False
            session.delete(jd)
            session.commit()
            return True
