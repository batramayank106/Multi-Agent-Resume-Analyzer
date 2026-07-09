import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from services.audit_service import log_request
from services.rate_limit import check_rate_limit

logger = logging.getLogger(__name__)

# Paths to skip audit logging (health checks, static)
_SKIP_PATHS = {"/health", "/favicon.ico", "/docs", "/openapi.json", "/redoc"}
# Paths to skip rate limiting
_RATE_LIMIT_SKIP = {"/health"}


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Detect super admin for relaxed rate limit
        is_super_admin = False
        try:
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                from jose import jwt
                from config import settings
                payload = jwt.decode(auth[7:], settings.jwt_secret, algorithms=[settings.jwt_algorithm])
                if payload.get("role") == "super_admin":
                    is_super_admin = True
        except Exception:
            pass

        # Rate limiting
        if path not in _RATE_LIMIT_SKIP:
            try:
                check_rate_limit(client_ip, is_super_admin=is_super_admin)
            except Exception:
                if path not in _SKIP_PATHS:
                    log_request(method=request.method, path=path, status_code=429, ip_address=client_ip)
                return Response(status_code=429, content='{"detail":"Rate limit exceeded"}', media_type="application/json")

        start = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            if path not in _SKIP_PATHS:
                log_request(method=request.method, path=path, status_code=500, ip_address=client_ip, duration_ms=duration)
            raise

        duration = int((time.time() - start) * 1000)

        if path not in _SKIP_PATHS and path.startswith("/api/"):
            user_id = None
            user_email = None
            try:
                auth = request.headers.get("authorization", "")
                if auth.startswith("Bearer "):
                    from jose import jwt
                    from config import settings
                    payload = jwt.decode(auth[7:], settings.jwt_secret, algorithms=[settings.jwt_algorithm])
                    user_email = payload.get("sub")
                    user_id = payload.get("user_id")
            except Exception:
                pass

            log_request(
                user_id=user_id,
                user_email=user_email,
                method=request.method,
                path=path,
                status_code=response.status_code,
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent", "")[:500],
                duration_ms=duration,
            )

        return response
