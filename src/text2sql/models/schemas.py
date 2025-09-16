"""
Pydantic models for API request/response schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str = Field(..., description="Message role (human, ai, system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SQLQueryRequest(BaseModel):
    """SQL query request model."""

    question: str = Field(..., description="Natural language question")
    session_id: str = Field(..., description="Session identifier")
    message_type: str = Field("human", description="Message type")
    max_rows: Optional[int] = Field(None, description="Maximum rows to return")
    timeout: Optional[float] = Field(None, description="Query timeout in seconds")

    @validator("question")
    def validate_question(cls, v):
        """Validate question is not empty."""
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()

    @validator("session_id")
    def validate_session_id(cls, v):
        """Validate session ID."""
        if not v or not v.strip():
            raise ValueError("Session ID cannot be empty")
        return v.strip()


class SQLQueryResponse(BaseModel):
    """SQL query response model."""

    session_id: str = Field(..., description="Session identifier")
    sql_query: str = Field(..., description="Generated SQL query")
    query_results: Optional[Union[List[Dict[str, Any]], str]] = Field(
        None, description="Query execution results"
    )
    error: Optional[str] = Field(None, description="Error message if any")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    row_count: Optional[int] = Field(None, description="Number of rows returned")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SessionInfo(BaseModel):
    """Session information model."""

    session_id: str = Field(..., description="Session identifier")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    message_count: int = Field(0, description="Number of messages in session")
    is_active: bool = Field(True, description="Whether session is active")


class HealthCheck(BaseModel):
    """Health check response model."""

    status: str = Field("ok", description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="Application version")
    services: Dict[str, str] = Field(
        default_factory=dict, description="Service status details"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request identifier")