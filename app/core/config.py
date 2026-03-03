import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "PurpleForge"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/purpleforge")
    
    # Celery & Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Stratus Wrapper
    # For local dev, might just be the command name
    STRATUS_BINARY_PATH: str = "stratus" 

    class Config:
        env_file = ".env"

settings = Settings()
