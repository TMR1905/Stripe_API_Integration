from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.models.user import User
from app.core.security import hash_password, verify_password


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, password: str, full_name: Optional[str] = None) -> User:
    if get_user_by_email(db, email):
        raise ValueError("Email already registered")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user


def verify_user_credentials(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user
