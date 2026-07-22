from typing import Optional

from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import User

COOKIE_NAME = "pg_session"


def get_token_from_request(request: Request) -> Optional[str]:
    return request.cookies.get(COOKIE_NAME)


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    token = get_token_from_request(request)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if user and user.is_active:
        return user
    return None


def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required"
        )
    return user
