import logging

from database.connection import get_sync_session
from models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def log_request(
    user_id: int | None = None,
    user_email: str | None = None,
    method: str = "",
    path: str = "",
    status_code: int = 0,
    ip_address: str | None = None,
    user_agent: str | None = None,
    duration_ms: int | None = None,
):
    try:
        session = get_sync_session()
        try:
            entry = AuditLog(
                user_id=user_id,
                user_email=user_email,
                method=method,
                path=path,
                status_code=status_code,
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms,
            )
            session.add(entry)
            session.commit()
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Audit log failed: {e}")


def get_recent_logs(limit: int = 100) -> list[AuditLog]:
    session = get_sync_session()
    try:
        return (
            session.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()
