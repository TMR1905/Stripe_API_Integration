from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Application Settings
    APP_NAME: str = "FastAPI SaaS Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database Configuration
    DATABASE_URL: str
    DB_ECHO: bool = False
    
    # Security & Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Stripe Configuration
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    
    # CORS Settings
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    ALLOWED_METHODS: str = "GET,POST,PUT,DELETE,PATCH"
    ALLOWED_HEADERS: str = "*"
    
    # Email Settings (Optional)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    
    # Redis (Optional)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def allowed_methods_list(self) -> List[str]:
        """Convert comma-separated methods to list"""
        return [method.strip() for method in self.ALLOWED_METHODS.split(",")]
    
    @property
    def allowed_headers_list(self) -> List[str]:
        """Convert comma-separated headers to list"""
        if self.ALLOWED_HEADERS == "*":
            return ["*"]
        return [header.strip() for header in self.ALLOWED_HEADERS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Create and cache settings instance
    """
    return Settings()


# Create a global settings instance
settings = get_settings()