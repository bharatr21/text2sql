"""
Session management service for conversation history using Redis.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.config import AppSettings
from ..core.logging import LoggerMixin
from ..models.schemas import ChatMessage
from .redis_service import RedisService


class SessionService(LoggerMixin):
    """Session management service."""

    def __init__(self, redis_service: RedisService, app_settings: AppSettings):
        self.redis_service = redis_service
        self.app_settings = app_settings

    def _get_session_key(self, session_id: str) -> str:
        """Get Redis key for session messages."""
        return f"session:{session_id}:messages"

    def _get_session_info_key(self, session_id: str) -> str:
        """Get Redis key for session info."""
        return f"session:{session_id}:info"

    def _get_system_key(self, session_id: str) -> str:
        """Get Redis key for system messages."""
        return f"session:{session_id}:system"

    async def create_session(self, session_id: str) -> bool:
        """Create a new session."""
        self.logger.info("Creating new session", session_id=session_id)

        session_info = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "message_count": 0,
            "is_active": True,
        }

        info_key = self._get_session_info_key(session_id)
        await self.redis_service.set(info_key, session_info, ex=self.app_settings.session_ttl)

        return True

    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        info_key = self._get_session_info_key(session_id)
        return await self.redis_service.get(info_key)

    async def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        info_key = self._get_session_info_key(session_id)
        return await self.redis_service.exists(info_key)

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a message to the session history."""
        self.logger.debug("Adding message to session", session_id=session_id, role=role)

        # Ensure session exists
        if not await self.session_exists(session_id):
            await self.create_session(session_id)

        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )

        # Special handling for system messages
        if role == "system":
            system_key = self._get_system_key(session_id)
            await self.redis_service.sadd(system_key, message.model_dump())
            await self.redis_service.expire(system_key, self.app_settings.session_ttl)
        else:
            # Add to conversation history
            session_key = self._get_session_key(session_id)
            await self.redis_service.rpush(session_key, message.model_dump())
            await self.redis_service.expire(session_key, self.app_settings.session_ttl)

        # Update session info
        await self._update_session_activity(session_id)

        return True

    async def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        include_system: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        self.logger.debug("Getting session history", session_id=session_id, limit=limit)

        messages = []

        # Get system messages if requested
        if include_system:
            system_key = self._get_system_key(session_id)
            system_messages = await self.redis_service.smembers(system_key)
            messages.extend(system_messages)

        # Get conversation messages
        session_key = self._get_session_key(session_id)
        conversation_messages = await self.redis_service.lrange(
            session_key, 0, limit - 1 if limit else -1
        )
        messages.extend(conversation_messages)

        # Sort by timestamp (system messages first, then by chronological order)
        messages.sort(key=lambda x: (x.get("role") != "system", x.get("timestamp", "")))

        return messages

    async def get_message_count(self, session_id: str) -> int:
        """Get the number of messages in a session."""
        session_key = self._get_session_key(session_id)
        return await self.redis_service.llen(session_key)

    async def should_summarize(self, session_id: str) -> bool:
        """Check if conversation should be summarized."""
        count = await self.get_message_count(session_id)
        return count >= self.app_settings.max_history_messages

    async def summarize_and_trim(
        self,
        session_id: str,
        summary: str,
        keep_recent: int = 5,
    ) -> bool:
        """Summarize conversation and trim old messages."""
        self.logger.info("Summarizing conversation", session_id=session_id)

        # Add summary as system message
        await self.add_message(session_id, "system", f"Previous conversation summary: {summary}")

        # Keep only recent messages
        session_key = self._get_session_key(session_id)
        await self.redis_service.ltrim(session_key, -keep_recent, -1)

        return True

    async def clear_session(self, session_id: str) -> bool:
        """Clear all session data."""
        self.logger.info("Clearing session", session_id=session_id)

        session_key = self._get_session_key(session_id)
        info_key = self._get_session_info_key(session_id)
        system_key = self._get_system_key(session_id)

        await self.redis_service.delete(session_key, info_key, system_key)

        return True

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session completely."""
        return await self.clear_session(session_id)

    async def list_active_sessions(self) -> List[str]:
        """List all active session IDs."""
        pattern = "session:*:info"
        keys = await self.redis_service.keys(pattern)

        active_sessions = []
        for key in keys:
            session_info = await self.redis_service.get(key)
            if session_info and session_info.get("is_active", False):
                active_sessions.append(session_info["session_id"])

        return active_sessions

    async def _update_session_activity(self, session_id: str) -> None:
        """Update session last activity timestamp."""
        info_key = self._get_session_info_key(session_id)
        session_info = await self.redis_service.get(info_key, {})

        session_info["last_activity"] = datetime.utcnow().isoformat()
        session_info["message_count"] = session_info.get("message_count", 0) + 1

        await self.redis_service.set(info_key, session_info, ex=self.app_settings.session_ttl)

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (for maintenance)."""
        self.logger.info("Cleaning up expired sessions")

        pattern = "session:*:info"
        keys = await self.redis_service.keys(pattern)

        expired_count = 0
        for key in keys:
            if not await self.redis_service.exists(key):
                # Session already expired, clean up related keys
                session_id = key.split(":")[1]
                await self.clear_session(session_id)
                expired_count += 1

        self.logger.info("Cleaned up expired sessions", count=expired_count)
        return expired_count