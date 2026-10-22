"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """HeatSense typed environment configuration."""

    model_config = SettingsConfigDict(
        env_prefix="HEATSENSE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="development", description="Runtime environment")
    version: str = Field(default="0.1.0", description="API version")
    api_prefix: str = Field(default="/api/v1", description="API route prefix")

    host: str = Field(default="127.0.0.1", description="Server bind host")
    port: int = Field(default=8000, description="Server bind port")
    log_level: str = Field(default="INFO", description="Log level")
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins",
    )

    data_dir: Path = Field(default=Path("data"), description="Path to datasets directory")
    artifacts_dir: Path = Field(
        default=Path("artifacts"), description="Path to model artifacts directory"
    )

    model_version: str = Field(default="v1", description="Active ML model version")
    supported_regions: List[str] = Field(
        default=["IN"], description="List of supported country/region codes"
    )

    # API boundaries and safety limits
    max_search_limit: int = Field(default=50, description="Max results for location search")
    max_history_days: int = Field(default=365, description="Max historical query span in days")
    max_grid_area_deg2: float = Field(
        default=25.0, description="Max bounding box area in square degrees for grid queries"
    )
    cache_ttl_seconds: int = Field(default=300, description="In-memory cache TTL in seconds")


settings = Settings()
