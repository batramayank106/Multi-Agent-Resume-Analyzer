import logging
import re
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config import settings
from database.connection import get_sync_session
from models.user import User

logger = logging.getLogger(__name__)
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def validate_password(password: str) -> str | None:
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return "Password must contain at least one digit"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-]", password):
        return "Password must contain at least one special character"
    return None


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(security_optional)):
    if credentials is None:
        return None
    try:
        return get_current_user(credentials=credentials)
    except HTTPException:
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token required")
    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    session = get_sync_session()
    try:
        user = session.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")
        if user.is_locked:
            now = datetime.now(timezone.utc)
            if user.locked_until and now < user.locked_until:
                raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account locked due to too many failed attempts")
            user.is_locked = False
            user.failed_attempts = 0
            user.locked_until = None
            session.commit()
        return user
    finally:
        session.close()


def require_role(*roles: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user") or next(
                (v for v in kwargs.values() if isinstance(v, User)), None
            )
            if user and user.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires one of roles: {', '.join(roles)}",
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def handle_login_lockout(user: User, session: Session, failed: bool):
    if not failed:
        user.failed_attempts = 0
        user.is_locked = False
        user.locked_until = None
        session.commit()
        return

    user.failed_attempts = (user.failed_attempts or 0) + 1
    if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
        user.is_locked = True
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
        logger.warning(f"User {user.email} locked out until {user.locked_until}")
    session.commit()


def create_super_admin():
    if not settings.super_admin_email or not settings.super_admin_password:
        logger.info("SUPER_ADMIN_EMAIL or SUPER_ADMIN_PASSWORD not set, skipping super admin creation")
        return
    session = get_sync_session()
    try:
        existing = session.query(User).filter(
            (User.email == settings.super_admin_email) | (User.username == "superadmin")
        ).first()
        if existing:
            if existing.email == settings.super_admin_email and existing.username == "superadmin":
                logger.info(f"Super admin {settings.super_admin_email} already exists")
                return
            logger.info(f"Updating stale super admin entry to {settings.super_admin_email}")
            existing.email = settings.super_admin_email
            existing.username = "superadmin"
            existing.hashed_password = hash_password(settings.super_admin_password)
            existing.role = "super_admin"
            existing.is_active = True
            session.commit()
            logger.info(f"Super admin {settings.super_admin_email} updated")
            return
        user = User(
            email=settings.super_admin_email,
            username="superadmin",
            hashed_password=hash_password(settings.super_admin_password),
            role="super_admin",
            is_active=True,
        )
        session.add(user)
        session.commit()
        logger.info(f"Super admin {settings.super_admin_email} created")
    finally:
        session.close()
