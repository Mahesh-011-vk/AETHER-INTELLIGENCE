import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General Environment
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")

    # LLM Providers (Priority: 1. Gemini -> 2. Groq -> 3. DeepSeek)
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GROQ_API_KEY: Optional[str] = Field(default=None)
    DEEPSEEK_API_KEY: Optional[str] = Field(default=None)

    # GitHub API
    GITHUB_TOKEN: Optional[str] = Field(default=None)

    # Google Sheets API
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(default=None)
    GOOGLE_SPREADSHEET_ID: Optional[str] = Field(default=None)

    # Storage
    DATABASE_URL: str = Field(default=f"sqlite:///{BASE_DIR / 'data' / 'ai_pipeline.db'}")
    DATA_RAW_DIR: Path = Field(default=BASE_DIR / "data" / "raw")
    DATA_PROCESSED_DIR: Path = Field(default=BASE_DIR / "data" / "processed")

    # Concurrency & Resilience
    MAX_CONCURRENT_REQUESTS: int = Field(default=10)
    REQUEST_TIMEOUT_SECONDS: int = Field(default=30)
    MAX_RETRIES: int = Field(default=3)
    BACKOFF_FACTOR: float = Field(default=1.5)

    # Quality & Freshness Windows
    ROLLING_WINDOW_HOURS: int = Field(default=24)
    RAPIDFUZZ_SIMILARITY_THRESHOLD: float = Field(default=85.0)

    @classmethod
    def mask_secret(cls, secret: Optional[str]) -> str:
        if not secret:
            return "[NOT SET]"
        if len(secret) <= 8:
            return "***"
        return f"{secret[:4]}...{secret[-4:]}"

settings = Settings()

