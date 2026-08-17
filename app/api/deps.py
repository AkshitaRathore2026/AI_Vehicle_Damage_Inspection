from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_user_by_email

bearer_scheme = HTTPBearer(
    scheme_name="JWT Bearer",
    description="Paste the JWT access token returned by /api/auth/login.",
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "message": "Could not validate credentials.",
            "error": "invalid_token",
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        email = payload.get("sub")
        if not isinstance(email, str):
            raise credentials_exception
    except jwt.InvalidTokenError as exc:
        raise credentials_exception from exc

    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "User account is inactive.",
                "error": "inactive_user",
            },
        )
    return user


def require_roles(*roles: str) -> Callable[[User], User]:
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "You do not have permission to perform this action.",
                    "error": "forbidden_role",
                },
            )
        return current_user

    return role_checker


def get_current_admin(
    current_user: User = Depends(require_roles("admin")),
) -> User:
    return current_user


def get_current_inspector_or_admin(
    current_user: User = Depends(require_roles("admin", "inspector")),
) -> User:
    return current_user
