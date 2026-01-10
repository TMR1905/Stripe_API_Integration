"""
User Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user (registration)"""
    password: str
    
    # Password validation
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "password": "strongPassword123!"
            }
        }
    )


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class User(UserBase):
    """Schema for user response (what API returns)"""
    id: int
    is_active: bool
    is_superuser: bool
    stripe_customer_id: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)  # Allows conversion from SQLAlchemy model


class UserInDB(User):
    """Schema for user in database (includes hashed password)"""
    hashed_password: str
