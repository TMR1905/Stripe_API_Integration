from sqlalchemy.orm import Session
from typing import Tuple

from app.schemas.auth import Token
from app.schemas.user import UserCreate, User
from app.services.user_service import create_user, verify_user_credentials
from app.core.security import create_access_token, create_refresh_token


def register_user(db: Session, payload: UserCreate) -> Tuple[User, Token]:
    """
    Register a new user and return tokens
    """
    user = create_user(db, email=payload.email, password=payload.password, full_name=payload.full_name)
    claims = {"sub": str(user.id), "email": user.email}
    access = create_access_token(claims)
    refresh = create_refresh_token(claims)
    return user, Token(access_token=access, refresh_token=refresh)


def login_user(db: Session, email: str, password: str) -> Tuple[User, Token]:
    """
    Verify credentials and return tokens
    """
    user = verify_user_credentials(db, email, password)
    if not user:
        raise ValueError("Invalid credentials")
    claims = {"sub": str(user.id), "email": user.email}
    access = create_access_token(claims)
    refresh = create_refresh_token(claims)
    return user, Token(access_token=access, refresh_token=refresh)


def refresh_tokens(user: User) -> Token:
    """
    Issue new access/refresh tokens for a user
    """
    claims = {"sub": str(user.id), "email": user.email}
    access = create_access_token(claims)
    refresh = create_refresh_token(claims)
    return Token(access_token=access, refresh_token=refresh)
