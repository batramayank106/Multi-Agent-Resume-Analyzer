from models.company_insight import CompanyInsight
from database.connection import SyncSessionLocal


class CompanyInsightRepository:

    @staticmethod
    def create(company_name: str, **kwargs) -> CompanyInsight:
        with SyncSessionLocal() as session:
            insight = CompanyInsight(company_name=company_name, **kwargs)
            session.add(insight)
            session.commit()
            session.refresh(insight)
            return insight

    @staticmethod
    def get_by_id(insight_id: int) -> CompanyInsight | None:
        with SyncSessionLocal() as session:
            return session.query(CompanyInsight).filter(CompanyInsight.id == insight_id).first()

    @staticmethod
    def get_by_company(company_name: str) -> CompanyInsight | None:
        with SyncSessionLocal() as session:
            return session.query(CompanyInsight).filter(
                CompanyInsight.company_name == company_name
            ).first()

    @staticmethod
    def get_all() -> list[CompanyInsight]:
        with SyncSessionLocal() as session:
            return session.query(CompanyInsight).order_by(
                CompanyInsight.company_name.asc()
            ).all()

    @staticmethod
    def upsert(company_name: str, **kwargs) -> CompanyInsight:
        with SyncSessionLocal() as session:
            insight = session.query(CompanyInsight).filter(
                CompanyInsight.company_name == company_name
            ).first()
            if insight:
                for key, value in kwargs.items():
                    if hasattr(insight, key):
                        setattr(insight, key, value)
            else:
                insight = CompanyInsight(company_name=company_name, **kwargs)
                session.add(insight)
            session.commit()
            session.refresh(insight)
            return insight

    @staticmethod
    def delete(insight_id: int) -> bool:
        with SyncSessionLocal() as session:
            insight = session.query(CompanyInsight).filter(
                CompanyInsight.id == insight_id
            ).first()
            if not insight:
                return False
            session.delete(insight)
            session.commit()
            return True
