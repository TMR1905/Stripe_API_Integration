"""
Authentication Pydantic schemas for login, register, tokens
"""
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "yourPassword123!"
            }
        }
    )


class RegisterRequest(BaseModel):
    """Schema for registration request"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newuser@example.com",
                "password": "strongPassword123!",
                "full_name": "Jane Doe"
            }
        }
    )


class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )


class TokenData(BaseModel):
    """Schema for decoded token data"""
    email: Optional[str] = None
    user_id: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str
