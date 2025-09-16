"""
Configuration management using Pydantic Settings.
"""

import os
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(5, description="Connection pool size")
    max_overflow: int = Field(10, description="Maximum overflow connections")
    pool_timeout: int = Field(30, description="Pool timeout in seconds")
    pool_recycle: int = Field(3600, description="Pool recycle time in seconds")
    echo: bool = Field(False, description="Enable SQL echo for debugging")

    class Config:
        env_prefix = "DB_"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    host: str = Field("localhost", description="Redis host")
    port: int = Field(6379, description="Redis port")
    password: Optional[str] = Field(None, description="Redis password")
    db: int = Field(0, description="Redis database number")
    decode_responses: bool = Field(True, description="Decode responses")
    socket_connect_timeout: float = Field(5.0, description="Socket connect timeout")
    socket_timeout: float = Field(5.0, description="Socket timeout")
    retry_on_timeout: bool = Field(True, description="Retry on timeout")
    max_connections: int = Field(20, description="Maximum connections in pool")

    class Config:
        env_prefix = "REDIS_"


class LLMSettings(BaseSettings):
    """LLM configuration settings."""

    provider: Literal["openai", "anthropic", "together"] = Field(
        "openai", description="LLM provider"
    )
    model: str = Field("gpt-4", description="Model name")
    temperature: float = Field(0.0, description="Temperature for generation")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens")
    timeout: float = Field(60.0, description="Request timeout")
    max_retries: int = Field(3, description="Maximum retries")
    api_key: Optional[str] = Field(None, description="API key")

    class Config:
        env_prefix = "LLM_"

    @validator("api_key", pre=True, always=True)
    def get_api_key(cls, v, values):
        """Get API key from environment or file."""
        if v is not None:
            return v

        provider = values.get("provider", "openai")

        # Try environment variable first
        env_key = f"{provider.upper()}_API_KEY"
        if env_key in os.environ:
            return os.environ[env_key]

        # Try sensitive file
        sensitive_dir = Path("sensitive")
        if sensitive_dir.exists():
            key_file = sensitive_dir / f"{provider}.txt"
            if key_file.exists():
                return key_file.read_text().strip()

        return None


class AppSettings(BaseSettings):
    """Application configuration settings."""

    title: str = Field("Text2SQL API", description="Application title")
    description: str = Field(
        "Modern Text-to-SQL system using LangChain and LangGraph",
        description="Application description"
    )
    version: str = Field("0.1.0", description="Application version")
    debug: bool = Field(False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        "INFO", description="Log level"
    )

    # Session management
    session_ttl: int = Field(86400, description="Session TTL in seconds (24 hours)")
    max_history_messages: int = Field(20, description="Maximum messages before summarization")

    # SQL generation
    max_sql_rows: int = Field(100, description="Maximum rows to return from SQL queries")
    sql_timeout: float = Field(30.0, description="SQL query timeout")

    # API settings
    host: str = Field("127.0.0.1", description="API host")
    port: int = Field(8000, description="API port")
    reload: bool = Field(False, description="Auto-reload on code changes")

    class Config:
        env_prefix = "APP_"


class Settings(BaseSettings):
    """Main application settings."""

    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()