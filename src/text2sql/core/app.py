"""
Modern FastAPI application with async support and dependency injection.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..agents.sql_agent import SQLAgent
from ..agents.summarization_agent import SummarizationAgent
from ..core.config import Settings, settings
from ..core.logging import configure_logging, get_logger
from ..models.schemas import (
    ErrorResponse,
    HealthCheck,
    SQLQueryRequest,
    SQLQueryResponse,
)
from ..services import DatabaseService, LLMService, RedisService, SessionService


# Global service instances
database_service: DatabaseService = None
llm_service: LLMService = None
redis_service: RedisService = None
session_service: SessionService = None
summarization_agent: SummarizationAgent = None
sql_agent: SQLAgent = None

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global database_service, llm_service, redis_service, session_service, summarization_agent, sql_agent

    logger.info("Starting Text2SQL application")

    try:
        # Initialize services
        database_service = DatabaseService(settings.database)
        llm_service = LLMService(settings.llm)
        redis_service = RedisService(settings.redis)

        # Initialize summarization agent
        summarization_agent = SummarizationAgent(llm_service)

        # Initialize session service with summarization agent
        session_service = SessionService(
            redis_service,
            settings.app,
            summarization_agent=summarization_agent,
            keep_recent_messages=settings.app.keep_recent_messages
        )

        # Initialize SQL agent
        sql_agent = SQLAgent(
            database=database_service.langchain_db,
            llm_service=llm_service,
            session_service=session_service,
            max_rows=settings.app.max_sql_rows,
        )

        logger.info("All services initialized successfully")
        yield

    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise

    finally:
        logger.info("Shutting down Text2SQL application")

        # Cleanup services
        if database_service:
            await database_service.close()
        if redis_service:
            await redis_service.close()

        logger.info("Application shutdown complete")


def create_app(config: Settings = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    global settings

    if config:
        settings = config

    # Configure logging
    configure_logging(settings.app.log_level, settings.app.debug)

    # Create FastAPI app
    app = FastAPI(
        title=settings.app.title,
        description=settings.app.description,
        version=settings.app.version,
        debug=settings.app.debug,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client=request.client.host if request.client else None,
        )

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
        )

        return response

    # Add exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            error=str(exc),
            method=request.method,
            url=str(request.url),
        )

        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="InternalServerError",
                message="An unexpected error occurred",
                detail=str(exc) if settings.app.debug else None,
            ).model_dump(),
        )

    # Service dependencies
    def get_database_service() -> DatabaseService:
        if database_service is None:
            raise HTTPException(status_code=503, detail="Database service not available")
        return database_service

    def get_llm_service() -> LLMService:
        if llm_service is None:
            raise HTTPException(status_code=503, detail="LLM service not available")
        return llm_service

    def get_redis_service() -> RedisService:
        if redis_service is None:
            raise HTTPException(status_code=503, detail="Redis service not available")
        return redis_service

    def get_session_service() -> SessionService:
        if session_service is None:
            raise HTTPException(status_code=503, detail="Session service not available")
        return session_service

    def get_sql_agent() -> SQLAgent:
        if sql_agent is None:
            raise HTTPException(status_code=503, detail="SQL agent not available")
        return sql_agent

    # Routes
    @app.get("/", response_model=Dict[str, str])
    async def root():
        """Root endpoint with basic information."""
        return {
            "name": settings.app.title,
            "version": settings.app.version,
            "description": settings.app.description,
        }

    @app.get("/health", response_model=HealthCheck)
    async def health_check(
        db: DatabaseService = Depends(get_database_service),
        redis: RedisService = Depends(get_redis_service),
        llm: LLMService = Depends(get_llm_service),
    ):
        """Health check endpoint."""
        services = {}

        # Check database
        try:
            db_healthy = await db.health_check()
            services["database"] = "healthy" if db_healthy else "unhealthy"
        except Exception:
            services["database"] = "unhealthy"

        # Check Redis
        try:
            redis_healthy = await redis.health_check()
            services["redis"] = "healthy" if redis_healthy else "unhealthy"
        except Exception:
            services["redis"] = "unhealthy"

        # Check LLM
        try:
            llm_healthy = await llm.health_check()
            services["llm"] = "healthy" if llm_healthy else "unhealthy"
        except Exception:
            services["llm"] = "unhealthy"

        # Overall status
        all_healthy = all(status == "healthy" for status in services.values())
        status = "healthy" if all_healthy else "degraded"

        return HealthCheck(
            status=status,
            version=settings.app.version,
            services=services,
        )

    @app.post("/query", response_model=SQLQueryResponse)
    async def execute_query(
        request: SQLQueryRequest,
        agent: SQLAgent = Depends(get_sql_agent),
    ):
        """Execute a natural language query and return SQL results."""
        logger.info(
            "Processing query request",
            session_id=request.session_id,
            question=request.question[:100] + "..." if len(request.question) > 100 else request.question,
        )

        try:
            start_time = time.time()

            # Run the SQL agent
            result = await agent.arun(
                question=request.question,
                session_id=request.session_id,
            )

            execution_time = time.time() - start_time

            # Handle errors
            if result.get("error"):
                logger.error(
                    "Query execution failed",
                    session_id=request.session_id,
                    error=result["error"],
                )
                return SQLQueryResponse(
                    session_id=request.session_id,
                    sql_query="",
                    error=result["error"],
                    execution_time=execution_time,
                )

            # Count rows if results are available
            row_count = None
            if isinstance(result.get("query_results"), list):
                row_count = len(result["query_results"])
            elif isinstance(result.get("query_results"), str):
                # Try to extract row count from string result
                try:
                    lines = result["query_results"].strip().split('\n')
                    row_count = len([line for line in lines if line.strip() and not line.startswith('|')])
                except:
                    row_count = None

            logger.info(
                "Query executed successfully",
                session_id=request.session_id,
                execution_time=execution_time,
                row_count=row_count,
            )

            return SQLQueryResponse(
                session_id=request.session_id,
                sql_query=result.get("sql_query", ""),
                query_results=result.get("query_results"),
                execution_time=execution_time,
                row_count=row_count,
                metadata={
                    "agent_execution_time": result.get("execution_time"),
                    "llm_provider": llm_service.settings.provider,
                    "llm_model": llm_service.settings.model,
                },
            )

        except Exception as e:
            logger.error(
                "Unexpected error during query processing",
                session_id=request.session_id,
                error=str(e),
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process query: {str(e)}",
            )

    @app.get("/sessions/{session_id}/info")
    async def get_session_info(
        session_id: str,
        session: SessionService = Depends(get_session_service),
    ):
        """Get information about a session."""
        info = await session.get_session_info(session_id)
        if not info:
            raise HTTPException(status_code=404, detail="Session not found")
        return info

    @app.get("/sessions/{session_id}/history")
    async def get_session_history(
        session_id: str,
        limit: int = 50,
        session: SessionService = Depends(get_session_service),
    ):
        """Get conversation history for a session."""
        history = await session.get_history(session_id, limit=limit)
        return {"session_id": session_id, "history": history}

    @app.delete("/sessions/{session_id}")
    async def delete_session(
        session_id: str,
        session: SessionService = Depends(get_session_service),
    ):
        """Delete a session and all its data."""
        await session.delete_session(session_id)
        return {"message": f"Session {session_id} deleted successfully"}

    @app.get("/sessions")
    async def list_sessions(
        session: SessionService = Depends(get_session_service),
    ):
        """List all active sessions."""
        sessions = await session.list_active_sessions()
        return {"sessions": sessions}

    @app.get("/database/tables")
    async def get_database_tables(
        db: DatabaseService = Depends(get_database_service),
    ):
        """Get list of database tables."""
        tables = await db.get_table_names()
        return {"tables": tables}

    @app.get("/database/schema")
    async def get_database_schema(
        db: DatabaseService = Depends(get_database_service),
    ):
        """Get database schema information."""
        schema = await db.get_table_info()
        return {"schema": schema}

    return app