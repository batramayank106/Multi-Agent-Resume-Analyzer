from models.analysis_result import AnalysisResult
from database.connection import SyncSessionLocal


class AnalysisRepository:

    @staticmethod
    def create(resume_id: int, job_description_id: int = None) -> AnalysisResult:
        with SyncSessionLocal() as session:
            result = AnalysisResult(resume_id=resume_id, job_description_id=job_description_id)
            session.add(result)
            session.commit()
            session.refresh(result)
            return result

    @staticmethod
    def get_by_id(result_id: int) -> AnalysisResult | None:
        with SyncSessionLocal() as session:
            return session.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()

    @staticmethod
    def get_by_resume(resume_id: int) -> list[AnalysisResult]:
        with SyncSessionLocal() as session:
            return session.query(AnalysisResult).filter(
                AnalysisResult.resume_id == resume_id
            ).order_by(AnalysisResult.created_at.desc()).all()

    @staticmethod
    def get_all() -> list[AnalysisResult]:
        with SyncSessionLocal() as session:
            return session.query(AnalysisResult).order_by(AnalysisResult.created_at.desc()).all()

    @staticmethod
    def update(result_id: int, **kwargs) -> AnalysisResult | None:
        with SyncSessionLocal() as session:
            result = session.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
            if not result:
                return None
            for key, value in kwargs.items():
                if hasattr(result, key):
                    setattr(result, key, value)
            session.commit()
            session.refresh(result)
            return result

    @staticmethod
    def delete(result_id: int) -> bool:
        with SyncSessionLocal() as session:
            result = session.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
            if not result:
                return False
            session.delete(result)
            session.commit()
            return True
