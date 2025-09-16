"""
Unit tests for configuration management.
"""

import os
import tempfile
from pathlib import Path

import pytest

from text2sql.core.config import Settings, DatabaseSettings, LLMSettings


@pytest.mark.unit
def test_database_settings_defaults():
    """Test database settings with defaults."""
    settings = DatabaseSettings(url="sqlite:///test.db")

    assert settings.url == "sqlite:///test.db"
    assert settings.pool_size == 5
    assert settings.max_overflow == 10
    assert settings.echo is False


@pytest.mark.unit
def test_database_settings_from_env(monkeypatch):
    """Test database settings from environment variables."""
    monkeypatch.setenv("DB_URL", "sqlite:///env_test.db")
    monkeypatch.setenv("DB_POOL_SIZE", "20")
    monkeypatch.setenv("DB_ECHO", "true")

    settings = DatabaseSettings()

    assert settings.url == "sqlite:///env_test.db"
    assert settings.pool_size == 20
    assert settings.echo is True


@pytest.mark.unit
def test_llm_settings_api_key_from_env(monkeypatch):
    """Test LLM settings API key from environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-from-env")

    settings = LLMSettings(provider="openai")

    assert settings.api_key == "test-key-from-env"


@pytest.mark.unit
def test_llm_settings_api_key_from_file():
    """Test LLM settings API key from file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sensitive directory and file
        sensitive_dir = Path(temp_dir) / "sensitive"
        sensitive_dir.mkdir()

        key_file = sensitive_dir / "openai.txt"
        key_file.write_text("test-key-from-file")

        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            settings = LLMSettings(provider="openai")
            assert settings.api_key == "test-key-from-file"
        finally:
            os.chdir(original_cwd)


@pytest.mark.unit
def test_settings_integration():
    """Test complete settings integration."""
    settings = Settings(
        database=DatabaseSettings(url="sqlite:///test.db"),
        llm=LLMSettings(provider="openai", api_key="test-key"),
    )

    assert settings.database.url == "sqlite:///test.db"
    assert settings.llm.provider == "openai"
    assert settings.llm.api_key == "test-key"
    assert settings.app.title == "Text2SQL API"