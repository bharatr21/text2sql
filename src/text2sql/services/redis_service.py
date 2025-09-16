"""
Modern Redis service with async support and connection pooling.
"""

import json
from typing import Any, Dict, List, Optional, Union

import aioredis
import redis

from ..core.config import RedisSettings
from ..core.logging import LoggerMixin


class RedisService(LoggerMixin):
    """Modern Redis service with async support."""

    def __init__(self, settings: RedisSettings):
        self.settings = settings
        self._sync_client: Optional[redis.Redis] = None
        self._async_client: Optional[aioredis.Redis] = None

    @property
    def sync_client(self) -> redis.Redis:
        """Get or create synchronous Redis client."""
        if self._sync_client is None:
            self._sync_client = redis.Redis(
                host=self.settings.host,
                port=self.settings.port,
                password=self.settings.password,
                db=self.settings.db,
                decode_responses=self.settings.decode_responses,
                socket_connect_timeout=self.settings.socket_connect_timeout,
                socket_timeout=self.settings.socket_timeout,
                retry_on_timeout=self.settings.retry_on_timeout,
                max_connections=self.settings.max_connections,
            )
        return self._sync_client

    @property
    async def async_client(self) -> aioredis.Redis:
        """Get or create asynchronous Redis client."""
        if self._async_client is None:
            self._async_client = aioredis.from_url(
                f"redis://{self.settings.host}:{self.settings.port}/{self.settings.db}",
                password=self.settings.password,
                decode_responses=self.settings.decode_responses,
                socket_connect_timeout=self.settings.socket_connect_timeout,
                socket_timeout=self.settings.socket_timeout,
                retry_on_timeout=self.settings.retry_on_timeout,
                max_connections=self.settings.max_connections,
            )
        return self._async_client

    # Async operations
    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set a key-value pair asynchronously."""
        client = await self.async_client

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        return await client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key asynchronously."""
        client = await self.async_client
        value = await client.get(key)

        if value is None:
            return default

        try:
            # Try to parse as JSON
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Return as string if not JSON
            return value

    async def delete(self, *keys: str) -> int:
        """Delete keys asynchronously."""
        client = await self.async_client
        return await client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check if key exists asynchronously."""
        client = await self.async_client
        return bool(await client.exists(key))

    async def expire(self, key: str, time: int) -> bool:
        """Set key expiration asynchronously."""
        client = await self.async_client
        return await client.expire(key, time)

    async def ttl(self, key: str) -> int:
        """Get time to live for key asynchronously."""
        client = await self.async_client
        return await client.ttl(key)

    # List operations
    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to the left of a list asynchronously."""
        client = await self.async_client
        serialized_values = []
        for value in values:
            if isinstance(value, (dict, list)):
                serialized_values.append(json.dumps(value))
            else:
                serialized_values.append(str(value))
        return await client.lpush(key, *serialized_values)

    async def rpush(self, key: str, *values: Any) -> int:
        """Push values to the right of a list asynchronously."""
        client = await self.async_client
        serialized_values = []
        for value in values:
            if isinstance(value, (dict, list)):
                serialized_values.append(json.dumps(value))
            else:
                serialized_values.append(str(value))
        return await client.rpush(key, *serialized_values)

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get a range of elements from a list asynchronously."""
        client = await self.async_client
        values = await client.lrange(key, start, end)

        result = []
        for value in values:
            try:
                result.append(json.loads(value))
            except (json.JSONDecodeError, TypeError):
                result.append(value)
        return result

    async def llen(self, key: str) -> int:
        """Get the length of a list asynchronously."""
        client = await self.async_client
        return await client.llen(key)

    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim a list to a specified range asynchronously."""
        client = await self.async_client
        return await client.ltrim(key, start, end)

    # Set operations
    async def sadd(self, key: str, *values: Any) -> int:
        """Add values to a set asynchronously."""
        client = await self.async_client
        serialized_values = []
        for value in values:
            if isinstance(value, (dict, list)):
                serialized_values.append(json.dumps(value))
            else:
                serialized_values.append(str(value))
        return await client.sadd(key, *serialized_values)

    async def smembers(self, key: str) -> List[Any]:
        """Get all members of a set asynchronously."""
        client = await self.async_client
        values = await client.smembers(key)

        result = []
        for value in values:
            try:
                result.append(json.loads(value))
            except (json.JSONDecodeError, TypeError):
                result.append(value)
        return result

    async def sismember(self, key: str, value: Any) -> bool:
        """Check if value is a member of a set asynchronously."""
        client = await self.async_client
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await client.sismember(key, value)

    # Hash operations
    async def hset(self, key: str, mapping: Dict[str, Any]) -> int:
        """Set hash fields asynchronously."""
        client = await self.async_client
        serialized_mapping = {}
        for field, value in mapping.items():
            if isinstance(value, (dict, list)):
                serialized_mapping[field] = json.dumps(value)
            else:
                serialized_mapping[field] = str(value)
        return await client.hset(key, mapping=serialized_mapping)

    async def hget(self, key: str, field: str) -> Any:
        """Get a hash field value asynchronously."""
        client = await self.async_client
        value = await client.hget(key, field)

        if value is None:
            return None

        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields and values asynchronously."""
        client = await self.async_client
        hash_data = await client.hgetall(key)

        result = {}
        for field, value in hash_data.items():
            try:
                result[field] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                result[field] = value
        return result

    async def hdel(self, key: str, *fields: str) -> int:
        """Delete hash fields asynchronously."""
        client = await self.async_client
        return await client.hdel(key, *fields)

    # Utility methods
    async def ping(self) -> bool:
        """Ping Redis server asynchronously."""
        try:
            client = await self.async_client
            return await client.ping()
        except Exception as e:
            self.logger.error("Redis ping failed", error=str(e))
            return False

    async def flushdb(self) -> bool:
        """Flush current database asynchronously."""
        client = await self.async_client
        return await client.flushdb()

    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern asynchronously."""
        client = await self.async_client
        return await client.keys(pattern)

    async def close(self) -> None:
        """Close Redis connections."""
        self.logger.info("Closing Redis connections")

        if self._async_client:
            await self._async_client.close()

        if self._sync_client:
            self._sync_client.close()

    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        return await self.ping()