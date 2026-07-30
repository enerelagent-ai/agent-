import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

DbSession = Annotated[Session, Depends(get_db)]

_security = HTTPBasic(auto_error=False)


def require_admin(credentials: HTTPBasicCredentials | None = Depends(_security)) -> None:
    """Gate a route behind ADMIN_USERNAME/ADMIN_PASSWORD (see Settings).

    Auth is opt-in via those two env vars rather than always-on, so local
    dev stays exactly as frictionless as it was before this existed; a
    deployment (Render) that sets both gets every listings/dashboard route
    protected. Uses compare_digest on both fields -- checking only the
    password would still leak whether the *username* was right via timing,
    so both need the constant-time comparison.
    """
    if settings.admin_username is None or settings.admin_password is None:
        return
    valid = credentials is not None and (
        secrets.compare_digest(credentials.username, settings.admin_username)
        and secrets.compare_digest(credentials.password, settings.admin_password)
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
