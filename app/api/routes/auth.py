from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, MessageResponse, RegisterRequest, UserResponse
from app.services.auth_service import authenticate_user, build_auth_token, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    user = register_user(db, payload)
    return {
        "success": True,
        "message": "User registered successfully.",
        "data": build_auth_token(user),
    }


@router.post("/login", response_model=AuthResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    user = authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Invalid email or password.",
                "error": "invalid_credentials",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "User account is inactive.",
                "error": "inactive_user",
            },
        )

    return {
        "success": True,
        "message": "Login successful.",
        "data": build_auth_token(user),
    }


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> dict[str, object]:
    return {
        "success": True,
        "message": "Current user retrieved successfully.",
        "data": current_user,
    }


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)) -> dict[str, object]:
    return {
        "success": True,
        "message": "Logout successful. Discard the access token on the client.",
        "data": {"email": current_user.email},
    }
