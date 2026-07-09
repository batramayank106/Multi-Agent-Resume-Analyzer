import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_sync_session
from models.user import User
from models.audit_log import AuditLog
from services.auth_service import (
    hash_password, verify_password, validate_password,
    create_access_token, create_refresh_token, decode_token,
    get_current_user, handle_login_lockout, require_role,
)
from services.audit_service import get_recent_logs

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    password_error = validate_password(body.password)
    if password_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=password_error)
    session = get_sync_session()
    try:
        if session.query(User).filter(User.email == body.email).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        if session.query(User).filter(User.username == body.username).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
        user = User(
            email=body.email,
            username=body.username,
            hashed_password=hash_password(body.password),
            role="user",
        )
        session.add(user)
        session.commit()
        logger.info(f"User registered: {body.email}")
        return {"message": "User registered successfully", "email": body.email}
    finally:
        session.close()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    session = get_sync_session()
    try:
        user = session.query(User).filter(User.email == body.email).first()
        if not user or not verify_password(body.password, user.hashed_password):
            if user:
                handle_login_lockout(user, session, failed=True)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        if user.is_locked and user.locked_until:
            now = datetime.now(timezone.utc)
            if now < user.locked_until:
                raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account locked. Try again later.")
            user.is_locked = False
            user.failed_attempts = 0
            user.locked_until = None
        handle_login_lockout(user, session, failed=False)
        access_token = create_access_token({"sub": user.email, "role": user.role})
        refresh_token = create_refresh_token({"sub": user.email, "role": user.role})
        logger.info(f"User logged in: {body.email}")
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    finally:
        session.close()


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: dict):
    refresh_token_str = body.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token required")
    payload = decode_token(refresh_token_str)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    email = payload.get("sub")
    session = get_sync_session()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")
        access_token = create_access_token({"sub": user.email, "role": user.role})
        new_refresh = create_refresh_token({"sub": user.email, "role": user.role})
        return TokenResponse(access_token=access_token, refresh_token=new_refresh)
    finally:
        session.close()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
    )


@router.get("/users")
def list_users(current_user: User = Depends(get_current_user)):
    if current_user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    session = get_sync_session()
    try:
        users = session.query(User).all()
        return [
            UserResponse(id=u.id, email=u.email, username=u.username, role=u.role, is_active=u.is_active)
            for u in users
        ]
    finally:
        session.close()


@router.post("/logout")
def logout():
    return {"message": "Logout successful. Discard your tokens."}


class AuditLogResponse(BaseModel):
    id: int
    user_email: str | None = None
    method: str
    path: str
    status_code: int
    ip_address: str | None = None
    duration_ms: int | None = None
    created_at: str


@router.get("/audit-logs")
def list_audit_logs(current_user: User = Depends(get_current_user)):
    if current_user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    logs = get_recent_logs(limit=200)
    return [
        AuditLogResponse(
            id=log.id,
            user_email=log.user_email,
            method=log.method,
            path=log.path,
            status_code=log.status_code,
            ip_address=log.ip_address,
            duration_ms=log.duration_ms,
            created_at=log.created_at.isoformat() if log.created_at else "",
        )
        for log in logs
    ]


@router.patch("/users/{user_id}/role")
def update_user_role(user_id: int, body: dict, current_user: User = Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin only")
    new_role = body.get("role")
    if new_role not in ("user", "admin", "super_admin"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    session = get_sync_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.role = new_role
        session.commit()
        return {"message": f"User {user.email} role updated to {new_role}"}
    finally:
        session.close()


@router.patch("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: int, current_user: User = Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin only")
    session = get_sync_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.is_active = not user.is_active
        session.commit()
        return {"message": f"User {user.email} active={user.is_active}"}
    finally:
        session.close()
