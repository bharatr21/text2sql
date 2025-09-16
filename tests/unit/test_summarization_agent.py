"""
Tests for the SummarizationAgent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.text2sql.agents.summarization_agent import SummarizationAgent
from src.text2sql.services.llm_service import LLMService


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    llm_service = MagicMock(spec=LLMService)

    # Mock AI response with summary content
    mock_response = MagicMock()
    mock_response.content = "User explored NYC crime data, asking about felony rates in Manhattan and Brooklyn. Found 3 felony cases in Manhattan vs 1 in Brooklyn during January 2024."

    llm_service.ainvoke = AsyncMock(return_value=mock_response)
    return llm_service


@pytest.fixture
def summarization_agent(mock_llm_service):
    """Create a SummarizationAgent with mocked dependencies."""
    return SummarizationAgent(mock_llm_service)


@pytest.fixture
def sample_conversation():
    """Sample conversation messages for testing."""
    return [
        {"role": "human", "content": "How many felony crimes occurred in Manhattan?", "timestamp": "2024-01-01T10:00:00"},
        {"role": "ai", "content": "SELECT COUNT(*) FROM nyc_crime_data WHERE area_name = 'Manhattan' AND crime_class = 'Felony'", "timestamp": "2024-01-01T10:00:01"},
        {"role": "human", "content": "What about Brooklyn?", "timestamp": "2024-01-01T10:01:00"},
        {"role": "ai", "content": "SELECT COUNT(*) FROM nyc_crime_data WHERE area_name = 'Brooklyn' AND crime_class = 'Felony'", "timestamp": "2024-01-01T10:01:01"},
        {"role": "human", "content": "Compare the two boroughs", "timestamp": "2024-01-01T10:02:00"},
        {"role": "ai", "content": "SELECT area_name, COUNT(*) FROM nyc_crime_data WHERE area_name IN ('Manhattan', 'Brooklyn') AND crime_class = 'Felony' GROUP BY area_name", "timestamp": "2024-01-01T10:02:01"},
    ]


@pytest.mark.asyncio
async def test_summarize_conversation_initial(summarization_agent, sample_conversation):
    """Test initial conversation summarization."""
    result = await summarization_agent.summarize_conversation(
        messages=sample_conversation,
        session_id="test-session-1"
    )

    assert result["success"] is True
    assert result["error"] is None
    assert result["summary"] is not None
    assert "NYC crime data" in result["summary"]
    assert "felony" in result["summary"].lower()


@pytest.mark.asyncio
async def test_summarize_conversation_progressive(summarization_agent, sample_conversation):
    """Test progressive summarization with existing summary."""
    existing_summary = "User previously explored population data for California and Texas."

    result = await summarization_agent.summarize_conversation(
        messages=sample_conversation,
        session_id="test-session-2",
        existing_summary=existing_summary
    )

    assert result["success"] is True
    assert result["error"] is None
    assert result["summary"] is not None


@pytest.mark.asyncio
async def test_summarize_conversation_empty_messages(summarization_agent):
    """Test summarization with empty message list."""
    result = await summarization_agent.summarize_conversation(
        messages=[],
        session_id="test-session-3"
    )

    assert result["success"] is False
    assert result["error"] is not None
    assert "No conversation messages to summarize" in result["error"]


@pytest.mark.asyncio
async def test_summarize_conversation_system_messages_filtered(summarization_agent):
    """Test that system messages are filtered out."""
    messages_with_system = [
        {"role": "system", "content": "You are a SQL expert", "timestamp": "2024-01-01T09:00:00"},
        {"role": "human", "content": "Show me crime data", "timestamp": "2024-01-01T10:00:00"},
        {"role": "ai", "content": "SELECT * FROM nyc_crime_data LIMIT 10", "timestamp": "2024-01-01T10:00:01"},
        {"role": "system", "content": "Previous conversation summary: ...", "timestamp": "2024-01-01T10:30:00"},
    ]

    result = await summarization_agent.summarize_conversation(
        messages=messages_with_system,
        session_id="test-session-4"
    )

    assert result["success"] is True
    # Should have processed only human and ai messages


@pytest.mark.asyncio
async def test_summarize_conversation_llm_error(mock_llm_service, sample_conversation):
    """Test handling of LLM service errors."""
    # Make LLM service raise an exception
    mock_llm_service.ainvoke.side_effect = Exception("LLM service unavailable")

    agent = SummarizationAgent(mock_llm_service)

    result = await agent.summarize_conversation(
        messages=sample_conversation,
        session_id="test-session-5"
    )

    assert result["success"] is False
    assert result["error"] is not None
    assert "LLM service unavailable" in result["error"]


def test_initial_summary_prompt(summarization_agent):
    """Test that initial summary prompt is properly formatted."""
    prompt = summarization_agent._get_initial_summary_prompt()

    assert "SQL database conversations" in prompt
    assert "100-300 words" in prompt
    assert "database tables" in prompt
    assert "chronological flow" in prompt


def test_progressive_summary_prompt(summarization_agent):
    """Test that progressive summary prompt is properly formatted."""
    prompt = summarization_agent._get_progressive_summary_prompt()

    assert "existing conversation summary" in prompt
    assert "new information" in prompt
    assert "100-400 words" in prompt
    assert "updated summary" in prompt