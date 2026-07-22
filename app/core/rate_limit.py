from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

from app.core.security import decode_access_token
from app.services.auth import COOKIE_NAME


def rate_limit_key(request: Request) -> str:
    """Key by authenticated user id when available, otherwise by IP."""
    token = request.cookies.get(COOKIE_NAME)
    if token:
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            return f"user:{payload['sub']}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=rate_limit_key)
