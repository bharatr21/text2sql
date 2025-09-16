"""
Modern database service using SQLAlchemy 2.0 and async patterns.
"""

from typing import Any, Dict, List, Optional

from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ..core.config import DatabaseSettings
from ..core.logging import LoggerMixin


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class DatabaseService(LoggerMixin):
    """Modern database service with async support."""

    def __init__(self, settings: DatabaseSettings):
        self.settings = settings
        self._engine = None
        self._async_engine = None
        self._async_session_maker = None
        self._langchain_db = None

    @property
    def engine(self):
        """Get or create the synchronous engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.settings.url,
                pool_size=self.settings.pool_size,
                max_overflow=self.settings.max_overflow,
                pool_timeout=self.settings.pool_timeout,
                pool_recycle=self.settings.pool_recycle,
                echo=self.settings.echo,
            )
        return self._engine

    @property
    def async_engine(self):
        """Get or create the async engine."""
        if self._async_engine is None:
            # Convert sync URL to async URL if needed
            async_url = self.settings.url
            if async_url.startswith("sqlite://"):
                async_url = async_url.replace("sqlite://", "sqlite+aiosqlite://")
            elif async_url.startswith("mysql+mysqlconnector://"):
                async_url = async_url.replace("mysql+mysqlconnector://", "mysql+aiomysql://")
            elif async_url.startswith("postgresql://"):
                async_url = async_url.replace("postgresql://", "postgresql+asyncpg://")

            # SQLite-specific configuration
            if "sqlite" in async_url:
                self._async_engine = create_async_engine(
                    async_url,
                    echo=self.settings.echo,
                    # SQLite doesn't use connection pooling in the same way
                    connect_args={"check_same_thread": False}
                )
            else:
                self._async_engine = create_async_engine(
                    async_url,
                    pool_size=self.settings.pool_size,
                    max_overflow=self.settings.max_overflow,
                    pool_timeout=self.settings.pool_timeout,
                    pool_recycle=self.settings.pool_recycle,
                    echo=self.settings.echo,
                )
        return self._async_engine

    @property
    def async_session_maker(self):
        """Get or create the async session maker."""
        if self._async_session_maker is None:
            self._async_session_maker = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._async_session_maker

    @property
    def langchain_db(self) -> SQLDatabase:
        """Get the LangChain SQLDatabase instance."""
        if self._langchain_db is None:
            self._langchain_db = SQLDatabase.from_uri(self.settings.url)
        return self._langchain_db

    async def get_async_session(self) -> AsyncSession:
        """Get an async database session."""
        return self.async_session_maker()

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        fetch_results: bool = True,
    ) -> Optional[List[Dict[str, Any]]]:
        """Execute a SQL query asynchronously."""
        self.logger.info("Executing query", query=query[:100] + "..." if len(query) > 100 else query)

        try:
            async with self.get_async_session() as session:
                result = await session.execute(text(query), parameters or {})

                if fetch_results:
                    rows = result.fetchall()
                    if rows:
                        # Convert to list of dictionaries
                        columns = result.keys()
                        return [dict(zip(columns, row)) for row in rows]
                    return []

                await session.commit()
                return None

        except Exception as e:
            self.logger.error("Query execution failed", error=str(e), query=query)
            raise

    async def get_table_info(self) -> str:
        """Get database table information."""
        try:
            return self.langchain_db.get_table_info()
        except Exception as e:
            self.logger.error("Failed to get table info", error=str(e))
            raise

    async def get_table_names(self) -> List[str]:
        """Get list of table names."""
        try:
            return self.langchain_db.get_usable_table_names()
        except Exception as e:
            self.logger.error("Failed to get table names", error=str(e))
            raise

    async def close(self) -> None:
        """Close database connections."""
        self.logger.info("Closing database connections")

        if self._async_engine:
            await self._async_engine.dispose()

        if self._engine:
            self._engine.dispose()

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.get_async_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            self.logger.error("Database health check failed", error=str(e))
            return False