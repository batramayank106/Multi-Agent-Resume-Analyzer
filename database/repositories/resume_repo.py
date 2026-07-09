from models.resume import Resume
from database.connection import SyncSessionLocal


class ResumeRepository:

    @staticmethod
    def create(filename: str, original_text: str = None) -> Resume:
        with SyncSessionLocal() as session:
            resume = Resume(filename=filename, original_text=original_text)
            session.add(resume)
            session.commit()
            session.refresh(resume)
            return resume

    @staticmethod
    def get_by_id(resume_id: int) -> Resume | None:
        with SyncSessionLocal() as session:
            return session.query(Resume).filter(Resume.id == resume_id).first()

    @staticmethod
    def get_all() -> list[Resume]:
        with SyncSessionLocal() as session:
            return session.query(Resume).order_by(Resume.created_at.desc()).all()

    @staticmethod
    def update(resume_id: int, **kwargs) -> Resume | None:
        with SyncSessionLocal() as session:
            resume = session.query(Resume).filter(Resume.id == resume_id).first()
            if not resume:
                return None
            for key, value in kwargs.items():
                if hasattr(resume, key):
                    setattr(resume, key, value)
            session.commit()
            session.refresh(resume)
            return resume

    @staticmethod
    def delete(resume_id: int) -> bool:
        with SyncSessionLocal() as session:
            resume = session.query(Resume).filter(Resume.id == resume_id).first()
            if not resume:
                return False
            session.delete(resume)
            session.commit()
            return True
