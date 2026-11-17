import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    
    PROJECT_NAME: str = "Cloud-Based Product Delivery & Real-Time Tracking System"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "cloud-computing-tracking-secret-key-2026-supersecure")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    
    # Database URL: defaults to SQLite for immediate local testing; switch to PostgreSQL/RDS via environment variable
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tracking.db")
    
    # Default Admin Credentials for bootstrapping
    DEFAULT_ADMIN_USERNAME: str = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@2026")

settings = Settings()
