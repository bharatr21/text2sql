"""
Unit tests for session service.
"""

import pytest

from text2sql.services.session_service import SessionService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_session(session_service: SessionService, sample_session_id: str):
    """Test creating a new session."""
    result = await session_service.create_session(sample_session_id)
    assert result is True

    # Verify session exists
    exists = await session_service.session_exists(sample_session_id)
    assert exists is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_session_info(session_service: SessionService, sample_session_id: str):
    """Test getting session information."""
    await session_service.create_session(sample_session_id)

    info = await session_service.get_session_info(sample_session_id)
    assert info is not None
    assert info["session_id"] == sample_session_id
    assert "created_at" in info
    assert "last_activity" in info
    assert info["message_count"] == 0
    assert info["is_active"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_message(session_service: SessionService, sample_session_id: str):
    """Test adding messages to a session."""
    # Add human message
    result = await session_service.add_message(
        sample_session_id, "human", "How many employees are there?"
    )
    assert result is True

    # Add AI message
    result = await session_service.add_message(
        sample_session_id, "ai", "SELECT COUNT(*) FROM employees"
    )
    assert result is True

    # Check message count
    count = await session_service.get_message_count(sample_session_id)
    assert count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_history(session_service: SessionService, sample_session_id: str):
    """Test retrieving conversation history."""
    # Add some messages
    await session_service.add_message(sample_session_id, "human", "Question 1")
    await session_service.add_message(sample_session_id, "ai", "Answer 1")
    await session_service.add_message(sample_session_id, "human", "Question 2")

    # Get history
    history = await session_service.get_history(sample_session_id)

    assert len(history) == 3
    assert history[0]["role"] == "human"
    assert history[0]["content"] == "Question 1"
    assert history[1]["role"] == "ai"
    assert history[1]["content"] == "Answer 1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_system_message(session_service: SessionService, sample_session_id: str):
    """Test adding system messages."""
    await session_service.add_message(
        sample_session_id, "system", "You are a helpful SQL assistant."
    )

    history = await session_service.get_history(sample_session_id, include_system=True)
    system_messages = [msg for msg in history if msg["role"] == "system"]

    assert len(system_messages) == 1
    assert system_messages[0]["content"] == "You are a helpful SQL assistant."


@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_summarize(session_service: SessionService, sample_session_id: str):
    """Test conversation summarization trigger."""
    # Initially should not summarize
    should_summarize = await session_service.should_summarize(sample_session_id)
    assert should_summarize is False

    # Add many messages
    for i in range(25):  # More than the default threshold
        await session_service.add_message(sample_session_id, "human", f"Question {i}")

    should_summarize = await session_service.should_summarize(sample_session_id)
    assert should_summarize is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_clear_session(session_service: SessionService, sample_session_id: str):
    """Test clearing session data."""
    # Add some data
    await session_service.add_message(sample_session_id, "human", "Test message")

    # Clear session
    result = await session_service.clear_session(sample_session_id)
    assert result is True

    # Verify session no longer exists
    exists = await session_service.session_exists(sample_session_id)
    assert exists is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_active_sessions(session_service: SessionService):
    """Test listing active sessions."""
    # Create multiple sessions
    session_ids = ["session-1", "session-2", "session-3"]

    for session_id in session_ids:
        await session_service.create_session(session_id)

    # List sessions
    active_sessions = await session_service.list_active_sessions()

    assert len(active_sessions) >= len(session_ids)
    for session_id in session_ids:
        assert session_id in active_sessions


@pytest.mark.unit
@pytest.mark.asyncio
async def test_history_limit(session_service: SessionService, sample_session_id: str):
    """Test history retrieval with limit."""
    # Add many messages
    for i in range(10):
        await session_service.add_message(sample_session_id, "human", f"Question {i}")

    # Get limited history
    history = await session_service.get_history(sample_session_id, limit=5)

    assert len(history) == 5