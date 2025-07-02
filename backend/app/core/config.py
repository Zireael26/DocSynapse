"""
DocSynapse Configuration Management

This module handles all configuration settings for the DocSynapse application,
including environment variables, defaults, and validation.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application Settings
    APP_NAME: str = "DocSynapse"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080"
    ]

    # Crawler Settings
    MAX_CONCURRENT_REQUESTS: int = 5
    REQUEST_DELAY: float = 1.0
    TIMEOUT: int = 30
    MAX_PAGES: int = 1000
    USER_AGENT: str = "DocSynapse/1.0 (+https://github.com/docsynapse/docsynapse)"

    # Playwright Settings
    HEADLESS: bool = True
    BROWSER_TYPE: str = "chromium"  # chromium, firefox, webkit

    # File Settings
    MAX_FILE_SIZE: str = "100MB"
    OUTPUT_DIR: str = "./output"

    # Redis Settings (optional)
    REDIS_URL: Optional[str] = None
    USE_REDIS: bool = False

    # Security Settings
    MAX_CONTENT_LENGTH: int = 100 * 1024 * 1024  # 100MB

    # Language filtering configuration
    LANGUAGE_FILTERS: dict = {
        # Common language path patterns to exclude
        'exclude_patterns': [
            r'/zh/',           # Chinese
            r'/zh-cn/',        # Chinese Simplified
            r'/zh-tw/',        # Chinese Traditional
            r'/zh-hant/',      # Chinese Traditional (FastAPI specific)
            r'/ja/',           # Japanese
            r'/fr/',           # French
            r'/es/',           # Spanish
            r'/de/',           # German
            r'/it/',           # Italian
            r'/pt/',           # Portuguese
            r'/ru/',           # Russian
            r'/ko/',           # Korean
            r'/ar/',           # Arabic
            r'/hi/',           # Hindi
            r'/tr/',           # Turkish
            r'/az/',           # Azerbaijani
            r'/bn/',           # Bengali
            r'/fa/',           # Persian/Farsi
            r'/he/',           # Hebrew
            r'/id/',           # Indonesian
            r'/uk/',           # Ukrainian
            r'/ur/',           # Urdu
            r'/vi/',           # Vietnamese
            r'/yo/',           # Yoruba
            r'/em/',           # Emoji/Special case
            r'/hu/',           # Hungarian
            r'/pl/',           # Polish
            r'/nl/',           # Dutch
            # Add more patterns as needed
        ],

        # Preferred language (usually English)
        'preferred_language': 'en',

        # Domain-specific language patterns
        'domain_patterns': {
            'fastapi.tiangolo.com': [
                r'/zh-hant/',      # FastAPI Chinese Traditional
                r'/ja/',           # FastAPI Japanese
                r'/fr/',           # FastAPI French
                r'/es/',           # FastAPI Spanish
                r'/de/',           # FastAPI German
                r'/pt/',           # FastAPI Portuguese
                r'/ru/',           # FastAPI Russian
                r'/ko/',           # FastAPI Korean
                r'/ar/',           # FastAPI Arabic
                r'/hi/',           # FastAPI Hindi
                r'/tr/',           # FastAPI Turkish
                r'/az/',           # FastAPI Azerbaijani
                r'/bn/',           # FastAPI Bengali
                r'/fa/',           # FastAPI Persian/Farsi
                r'/he/',           # FastAPI Hebrew
                r'/id/',           # FastAPI Indonesian
                r'/uk/',           # FastAPI Ukrainian
                r'/ur/',           # FastAPI Urdu
                r'/vi/',           # FastAPI Vietnamese
                r'/yo/',           # FastAPI Yoruba
                r'/em/',           # FastAPI Emoji/Special
                r'/hu/',           # FastAPI Hungarian
                r'/pl/',           # FastAPI Polish
                r'/nl/',           # FastAPI Dutch
            ]
        }
    }

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("OUTPUT_DIR")
    @classmethod
    def create_output_dir(cls, v):
        """Ensure output directory exists."""
        Path(v).mkdir(exist_ok=True)
        return v

    @field_validator("MAX_FILE_SIZE")
    @classmethod
    def parse_file_size(cls, v):
        """Parse file size string to bytes."""
        if isinstance(v, str):
            v = v.upper()
            if v.endswith("MB"):
                return int(v[:-2]) * 1024 * 1024
            elif v.endswith("GB"):
                return int(v[:-2]) * 1024 * 1024 * 1024
            elif v.endswith("KB"):
                return int(v[:-2]) * 1024
            else:
                return int(v)
        return v

    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
