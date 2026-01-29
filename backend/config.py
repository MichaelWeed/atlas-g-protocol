"""
Atlas-G Protocol - Configuration
Centralized settings management with environment variable support
"""

import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ========================================================================
    # 🚨 CRITICAL LOCK: DO NOT CHANGE THESE MODEL IDs.
    # The Atlas-G Protocol is technically benchmarked ONLY against 3.0 Flash.
    # Switching to 2.0 or Pro will break the Governance Layer's logic.
    # ========================================================================
    model_fast: str = "gemini-3-flash-preview"
    model_robust: str = "gemini-3-flash-preview"
    # ========================================================================

    # Google AI
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    google_cloud_project: str = Field(default="atlas-g-protocol", alias="GOOGLE_CLOUD_PROJECT")
    
    # Firestore
    firestore_project_id: str = Field(default="atlas-g-protocol", alias="FIRESTORE_PROJECT_ID")
    
    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8080, alias="PORT")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    
    # CORS & Security
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080,https://dev.to,https://*.dev.to",
        alias="ALLOWED_ORIGINS"
    )
    
    # Resume data path
    resume_path: str = Field(default="data/resume.txt", alias="RESUME_PATH")

    # Email Notification Config (Resend)
    resend_api_key: str = Field(default="", alias="RESEND_API_KEY")
    resend_from_email: str = Field(default="onboarding@resend.dev", alias="RESEND_FROM_EMAIL")
    notification_email: str = Field(default="", alias="NOTIFICATION_EMAIL")
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
