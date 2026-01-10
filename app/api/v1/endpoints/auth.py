from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, Token, RefreshTokenRequest
from app.schemas.user import User as UserSchema
from app.services.auth_service import register_user, login_user, refresh_tokens
from app.core.security import decode_token
from app.services.user_service import get_user_by_id
from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        _, token = register_user(db, payload)
        return token
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        _, token = login_user(db, payload.email, payload.password)
        return token
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    decoded = decode_token(payload.refresh_token)
    if not decoded or decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    sub = decoded.get("sub")
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return refresh_tokens(user)


@router.get("/me", response_model=UserSchema)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile information.

    Requires valid access token in Authorization header.
    """
    return current_user
