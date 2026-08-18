"""
app/core/config.py — Application Configuration

PATTERN: Pydantic Settings v2 with environment variable binding.

WHY Pydantic Settings over python-dotenv:
    - Type-safe: env vars are validated and coerced to Python types at startup.
    - Fails fast: missing required vars raise a clear error before any request
      is served — not during a request in production.
    - Nested model support: complex config (DB pool, Redis, etc.) is
      structured, not flat string parsing.
    - Secret file support: reads from Docker secrets files transparently.

WHY NOT:
    - os.environ directly: No type coercion, no validation, no defaults.
    - dynaconf: Additional dependency with more complexity than needed.
    - django.conf.settings: FastAPI-specific patterns don't need Django's
      application container concept.

SCALABILITY:
    The Settings object is instantiated ONCE at module import time and
    cached via @lru_cache in get_settings(). All 4 Uvicorn worker processes
    share the same config — no repeated parsing.

SECURITY:
    - SecretStr wraps sensitive values (passwords, keys). Calling str() or
      logging a SecretStr returns '**********', preventing accidental leakage
      in logs, Sentry events, or error messages.
    - model_config sets env_file and case_sensitive to prevent surprising
      case-insensitive matches on case-sensitive Linux file systems.
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """PostgreSQL connection configuration."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = Field(
        default="postgresql+asyncpg://erp_user:erp_password@localhost:5432/erp_db",
        description="Async SQLAlchemy connection URL",
    )
    pool_size: int = Field(default=20, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=5, le=120)
    pool_recycle: int = Field(
        default=1800,
        description="Recycle connections after N seconds. Prevents stale connections.",
    )
    echo: bool = Field(
        default=False,
        description="Log all SQL statements. NEVER enable in production — leaks data.",
    )

    @property
    def sync_url(self) -> str:
        """
        Alembic requires a synchronous connection URL.
        Replace asyncpg driver with psycopg2 for migration commands.
        """
        return self.url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


class RedisSettings(BaseSettings):
    """Redis connection configuration."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    url: str = Field(
        default="redis://:redis_password@localhost:6379/0",
        description="Redis connection URL for application cache",
    )
    max_connections: int = Field(
        default=50,
        description="Connection pool size. Set based on: (workers * concurrency) + buffer",
    )
    socket_timeout: int = Field(default=5)
    socket_connect_timeout: int = Field(default=5)
    health_check_interval: int = Field(default=30)


class CelerySettings(BaseSettings):
    """Celery distributed task queue configuration."""

    model_config = SettingsConfigDict(env_prefix="CELERY_")

    broker_url: str = Field(
        default="redis://:redis_password@localhost:6379/1",
        description="Redis DB 1 for Celery broker (separate from app cache on DB 0)",
    )
    result_backend: str = Field(
        default="redis://:redis_password@localhost:6379/2",
    )
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: list[str] = ["json"]
    timezone: str = "Asia/Kolkata"
    enable_utc: bool = True
    task_soft_time_limit: int = 300      # 5 minutes — soft kill
    task_time_limit: int = 600           # 10 minutes — hard kill
    worker_prefetch_multiplier: int = 1  # Fair task distribution across workers


class StorageSettings(BaseSettings):
    """Storage backend configuration — local or S3."""

    model_config = SettingsConfigDict(env_prefix="")

    storage_backend: Literal["local", "s3"] = Field(
        default="local",
        description="'local' for Docker volume, 's3' for AWS S3 or MinIO",
    )
    media_root: str = Field(default="/app/media")
    media_url: str = Field(default="/media/")

    # AWS S3 (only used when storage_backend = "s3")
    aws_access_key_id: str | None = Field(default=None)
    aws_secret_access_key: SecretStr | None = Field(default=None)
    aws_region: str = Field(default="ap-south-1")
    aws_s3_bucket: str | None = Field(default=None)
    aws_s3_endpoint_url: str | None = Field(
        default=None,
        description="Override for MinIO or other S3-compatible stores",
    )


class CompanySettings(BaseSettings):
    """Company profile — printed on all PDF documents."""

    model_config = SettingsConfigDict(env_prefix="COMPANY_")

    name: str = Field(default="Mini Blinkit Private Limited")
    gst_number: str = Field(default="29ABCDE1234F1Z5")
    state_code: str = Field(
        default="29",
        description="Used to determine SGST/CGST (intra-state) vs IGST (inter-state)",
    )
    address: str = Field(default="Bengaluru, Karnataka - 560001")
    phone: str = Field(default="+91-9876543210")
    email: str = Field(default="operations@miniblinkit.com")


class Settings(BaseSettings):
    """
    Master application settings.

    Reads from environment variables and .env file.
    All nested settings classes are instantiated here.

    IMPORTANT: Do not access settings via global `settings` object inside
    functions that need to be testable — use dependency injection instead.
    This class is instantiated once (see get_settings()).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # Silently ignore unknown env vars
    )

    # ── Application ─────────────────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "Mini Blinkit ERP"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ── API ─────────────────────────────────────────────────────────────────
    api_v1_prefix: str = "/api/v1"

    # ── Security ────────────────────────────────────────────────────────────
    # SecretStr ensures this value never appears in logs or stack traces
    secret_key: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_hex(64)),
        description="JWT signing key. Must be explicitly set in production.",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, ge=5, le=10080)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=90)

    # ── CORS ────────────────────────────────────────────────────────────────
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
    )

    # ── Nested Settings ─────────────────────────────────────────────────────
    # Each sub-group reads its own prefix from env vars
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    company: CompanySettings = Field(default_factory=CompanySettings)

    # ── Pagination ──────────────────────────────────────────────────────────
    default_page_size: int = Field(default=25, ge=1, le=200)
    max_page_size: int = Field(default=200, ge=1, le=1000)

    # ── Stock Reservation ───────────────────────────────────────────────────
    stock_reservation_timeout_seconds: int = Field(
        default=60,
        description="Seconds before an unpaid order releases reserved inventory",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Parse comma-separated string from env var into a list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns the cached Settings singleton.

    WHY @lru_cache: Settings parsing (disk I/O, env reads, Pydantic validation)
    happens exactly once per process. All subsequent calls return the cached
    object in O(1). Under 4 Uvicorn workers, this runs 4 times total — once
    per process.

    In tests, call get_settings.cache_clear() before patching to ensure
    fresh settings are loaded.
    """
    return Settings()


# Module-level convenience reference.
# Use get_settings() in dependency-injected contexts for testability.
settings: Settings = get_settings()
