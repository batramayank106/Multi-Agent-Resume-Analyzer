from models.resume_version import ResumeVersion
from database.connection import SyncSessionLocal
from models.analysis_result import AnalysisResult


class VersionRepository:

    @staticmethod
    def create(resume_id: int, version_number: int = 1, content_text: str = None) -> ResumeVersion:
        with SyncSessionLocal() as session:
            version = ResumeVersion(
                resume_id=resume_id, version_number=version_number, content_text=content_text
            )
            session.add(version)
            session.commit()
            session.refresh(version)
            return version

    @staticmethod
    def create_from_analysis(
        resume_id: int,
        analysis_result_id: int,
        content_text: str = None,
        ats_score: float = None,
        recruiter_score: float = None,
        hiring_manager_score: float = None,
        truthfulness_score: float = None,
        selection_probability: dict = None,
    ) -> ResumeVersion:
        with SyncSessionLocal() as session:
            latest = session.query(ResumeVersion).filter(
                ResumeVersion.resume_id == resume_id
            ).order_by(ResumeVersion.version_number.desc()).first()
            version_number = (latest.version_number + 1) if latest else 1

            version = ResumeVersion(
                resume_id=resume_id,
                analysis_result_id=analysis_result_id,
                version_number=version_number,
                content_text=content_text,
                ats_score=ats_score,
                recruiter_score=recruiter_score,
                hiring_manager_score=hiring_manager_score,
                truthfulness_score=truthfulness_score,
                selection_probability=selection_probability,
            )
            session.add(version)
            session.commit()
            session.refresh(version)
            return version

    @staticmethod
    def get_by_id(version_id: int) -> ResumeVersion | None:
        with SyncSessionLocal() as session:
            return session.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()

    @staticmethod
    def get_by_resume(resume_id: int) -> list[ResumeVersion]:
        with SyncSessionLocal() as session:
            return session.query(ResumeVersion).filter(
                ResumeVersion.resume_id == resume_id
            ).order_by(ResumeVersion.version_number.desc()).all()

    @staticmethod
    def get_by_analysis(analysis_result_id: int) -> ResumeVersion | None:
        with SyncSessionLocal() as session:
            return session.query(ResumeVersion).filter(
                ResumeVersion.analysis_result_id == analysis_result_id
            ).first()

    @staticmethod
    def list_all() -> list[ResumeVersion]:
        with SyncSessionLocal() as session:
            return session.query(ResumeVersion).order_by(ResumeVersion.created_at.desc()).all()

    @staticmethod
    def get_latest(resume_id: int) -> ResumeVersion | None:
        with SyncSessionLocal() as session:
            return session.query(ResumeVersion).filter(
                ResumeVersion.resume_id == resume_id
            ).order_by(ResumeVersion.version_number.desc()).first()

    @staticmethod
    def update(version_id: int, **kwargs) -> ResumeVersion | None:
        with SyncSessionLocal() as session:
            version = session.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()
            if not version:
                return None
            for key, value in kwargs.items():
                if hasattr(version, key):
                    setattr(version, key, value)
            session.commit()
            session.refresh(version)
            return version
