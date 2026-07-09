import time
import logging

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

_requests: dict[str, list[float]] = {}
MAX_REQUESTS = 60
SUPER_ADMIN_MAX_REQUESTS = 120
WINDOW_SECONDS = 60


def check_rate_limit(client_key: str, is_super_admin: bool = False) -> None:
    now = time.time()
    window_start = now - WINDOW_SECONDS
    limit = SUPER_ADMIN_MAX_REQUESTS if is_super_admin else MAX_REQUESTS

    if client_key not in _requests:
        _requests[client_key] = []

    _requests[client_key] = [t for t in _requests[client_key] if t > window_start]

    if len(_requests[client_key]) >= limit:
        logger.warning(f"Rate limit exceeded for {client_key}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {limit} requests per {WINDOW_SECONDS}s.",
        )

    _requests[client_key].append(now)
