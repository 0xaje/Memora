"""
Memora Configuration Module.
Loads environment variables and provides validated settings using Pydantic Settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Memora"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
        description="Comma-separated allowed origins for frontend development"
    )

    # Real Sibyl Memory configuration
    SIBYL_DB_PATH: str = Field(
        default=str(Path.home() / ".sibyl-memory" / "memora.db"),
        description="Path to SQLite database used by Sibyl MemoryClient"
    )
    SIBYL_TENANT_ID: str = Field(
        default="00000000-0000-0000-0000-000000000001",
        description="Default tenant UUID for Sibyl"
    )
    SIBYL_TIER: str = Field(
        default="free",
        description="Sibyl tier level ('free' or paid tier)"
    )

    def resolved_db_path(self) -> str:
        """Returns the expanded absolute path for the Sibyl database file."""
        return str(Path(self.SIBYL_DB_PATH).expanduser().resolve())


settings = Settings()
