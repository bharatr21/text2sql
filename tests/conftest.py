"""
Pytest configuration and fixtures for Text2SQL tests.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from text2sql.core.app import create_app
from text2sql.core.config import Settings, DatabaseSettings, RedisSettings, LLMSettings, AppSettings
from text2sql.services import DatabaseService, RedisService, LLMService, SessionService
from text2sql.utils.db_utils import create_sample_database


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_db_url(temp_db_path: str) -> str:
    """Create a sample database and return its URL."""
    return create_sample_database(temp_db_path)


@pytest.fixture
def test_settings(sample_db_url: str) -> Settings:
    """Create test settings with temporary database."""
    return Settings(
        app=AppSettings(
            debug=True,
            log_level="DEBUG",
        ),
        database=DatabaseSettings(
            url=sample_db_url,
            echo=True,
            pool_size=1,
            max_overflow=0,
        ),
        redis=RedisSettings(
            host="localhost",
            port=6379,
            db=15,  # Use a different DB for tests
        ),
        llm=LLMSettings(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="test-key",  # Mock key for tests
        ),
    )


@pytest_asyncio.fixture
async def database_service(test_settings: Settings) -> AsyncGenerator[DatabaseService, None]:
    """Create a database service for testing."""
    service = DatabaseService(test_settings.database)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def redis_service(test_settings: Settings) -> AsyncGenerator[RedisService, None]:
    """Create a Redis service for testing."""
    service = RedisService(test_settings.redis)

    # Clear test database
    await service.flushdb()

    yield service

    # Cleanup
    await service.flushdb()
    await service.close()


@pytest.fixture
def llm_service(test_settings: Settings) -> LLMService:
    """Create a mock LLM service for testing."""

    class MockLLMService(LLMService):
        def __init__(self, settings):
            self.settings = settings

        async def ainvoke(self, messages, **kwargs):
            # Mock response for testing
            class MockResponse:
                content = "SELECT COUNT(*) FROM employees WHERE gender = 'Male'"
            return MockResponse()

        async def health_check(self):
            return True

    return MockLLMService(test_settings.llm)


@pytest_asyncio.fixture
async def session_service(redis_service: RedisService, test_settings: Settings) -> SessionService:
    """Create a session service for testing."""
    return SessionService(redis_service, test_settings.app)


@pytest.fixture
def test_app(test_settings: Settings) -> TestClient:
    """Create a test FastAPI application."""
    app = create_app(test_settings)
    return TestClient(app)


@pytest.fixture
def sample_questions():
    """Sample questions for testing."""
    return [
        "How many employees are there?",
        "What is the average salary by department?",
        "Who are the employees in Engineering?",
        "Show me all projects that are in progress",
        "What is the total budget for all departments?",
    ]


@pytest.fixture
def sample_session_id():
    """Sample session ID for testing."""
    return "test-session-123"


# Markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow