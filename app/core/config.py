"""Application configuration loaded from environment variables."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings sourced from environment variables."""

    DATABASE_URL: str = Field(..., alias="DATABASE_URL")
    ENV: str = "dev"

    SMTP_HOST: Optional[str] = Field(default=None, alias="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, alias="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: Optional[str] = Field(default=None, alias="SMTP_FROM_EMAIL")
    SMTP_USE_TLS: bool = Field(default=True, alias="SMTP_USE_TLS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
