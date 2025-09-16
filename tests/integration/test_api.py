"""
Integration tests for the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_root_endpoint(test_app: TestClient):
    """Test the root endpoint."""
    response = test_app.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "description" in data


@pytest.mark.integration
def test_health_endpoint(test_app: TestClient):
    """Test the health check endpoint."""
    response = test_app.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "services" in data
    assert "timestamp" in data


@pytest.mark.integration
def test_database_tables_endpoint(test_app: TestClient):
    """Test the database tables endpoint."""
    response = test_app.get("/database/tables")

    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert isinstance(data["tables"], list)
    assert "employees" in data["tables"]


@pytest.mark.integration
def test_database_schema_endpoint(test_app: TestClient):
    """Test the database schema endpoint."""
    response = test_app.get("/database/schema")

    assert response.status_code == 200
    data = response.json()
    assert "schema" in data
    assert isinstance(data["schema"], str)
    assert "employees" in data["schema"]


@pytest.mark.integration
def test_query_endpoint(test_app: TestClient, sample_session_id: str):
    """Test the main query endpoint."""
    response = test_app.post(
        "/query",
        json={
            "question": "How many employees are there?",
            "session_id": sample_session_id,
            "message_type": "human",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "sql_query" in data
    assert "query_results" in data
    assert data["session_id"] == sample_session_id


@pytest.mark.integration
def test_query_endpoint_validation(test_app: TestClient):
    """Test query endpoint validation."""
    # Missing question
    response = test_app.post(
        "/query",
        json={
            "session_id": "test-session",
            "message_type": "human",
        },
    )
    assert response.status_code == 422

    # Empty question
    response = test_app.post(
        "/query",
        json={
            "question": "",
            "session_id": "test-session",
            "message_type": "human",
        },
    )
    assert response.status_code == 422

    # Missing session_id
    response = test_app.post(
        "/query",
        json={
            "question": "Test question",
            "message_type": "human",
        },
    )
    assert response.status_code == 422


@pytest.mark.integration
def test_session_info_endpoint(test_app: TestClient, sample_session_id: str):
    """Test session info endpoint."""
    # First, create a session by making a query
    test_app.post(
        "/query",
        json={
            "question": "Test question",
            "session_id": sample_session_id,
            "message_type": "human",
        },
    )

    # Then get session info
    response = test_app.get(f"/sessions/{sample_session_id}/info")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == sample_session_id
    assert "created_at" in data
    assert "message_count" in data


@pytest.mark.integration
def test_session_history_endpoint(test_app: TestClient, sample_session_id: str):
    """Test session history endpoint."""
    # Create some conversation history
    test_app.post(
        "/query",
        json={
            "question": "First question",
            "session_id": sample_session_id,
            "message_type": "human",
        },
    )

    test_app.post(
        "/query",
        json={
            "question": "Second question",
            "session_id": sample_session_id,
            "message_type": "human",
        },
    )

    # Get history
    response = test_app.get(f"/sessions/{sample_session_id}/history")

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "history" in data
    assert data["session_id"] == sample_session_id
    assert len(data["history"]) >= 2


@pytest.mark.integration
def test_list_sessions_endpoint(test_app: TestClient):
    """Test list sessions endpoint."""
    # Create a few sessions
    session_ids = ["session-1", "session-2", "session-3"]

    for session_id in session_ids:
        test_app.post(
            "/query",
            json={
                "question": "Test question",
                "session_id": session_id,
                "message_type": "human",
            },
        )

    # List sessions
    response = test_app.get("/sessions")

    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)

    # Check that our sessions are in the list
    returned_sessions = data["sessions"]
    for session_id in session_ids:
        assert session_id in returned_sessions


@pytest.mark.integration
def test_delete_session_endpoint(test_app: TestClient, sample_session_id: str):
    """Test delete session endpoint."""
    # Create a session
    test_app.post(
        "/query",
        json={
            "question": "Test question",
            "session_id": sample_session_id,
            "message_type": "human",
        },
    )

    # Delete the session
    response = test_app.delete(f"/sessions/{sample_session_id}")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data

    # Verify session is deleted (should return 404)
    response = test_app.get(f"/sessions/{sample_session_id}/info")
    assert response.status_code == 404


@pytest.mark.integration
def test_error_handling(test_app: TestClient):
    """Test API error handling."""
    # Test non-existent session
    response = test_app.get("/sessions/non-existent-session/info")
    assert response.status_code == 404

    # Test invalid endpoints
    response = test_app.get("/non-existent-endpoint")
    assert response.status_code == 404