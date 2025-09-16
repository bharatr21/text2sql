# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modern Text-to-SQL system built with the latest LangChain, LangGraph, and async Python patterns. The system uses **SQLite** for lightweight, fast database operations and is designed for production use with comprehensive testing, monitoring, and configuration management.

## Core Architecture

The system follows a clean, layered architecture with full async support:

### Application Structure (`src/text2sql/`)
- **`core/`** - Application configuration, logging, and FastAPI app factory
- **`agents/`** - LangGraph-based SQL agent for conversational query processing
- **`services/`** - Business logic layer (Database, LLM, Redis, Session services)
- **`models/`** - Pydantic schemas for API requests/responses
- **`utils/`** - Utility functions for database setup and management

### Key Components
- **SQLAgent** (`agents/sql_agent.py`) - LangGraph state machine for SQL generation workflow
- **DatabaseService** (`services/database_service.py`) - Async SQLAlchemy 2.0 database operations
- **LLMService** (`services/llm_service.py`) - Multi-provider LLM interface (OpenAI, Anthropic, Together)
- **SessionService** (`services/session_service.py`) - Redis-based conversation management
- **FastAPI App** (`core/app.py`) - Modern async REST API with dependency injection

### Technology Stack
- **LangGraph** - Agent workflow orchestration
- **LangChain** - LLM integrations and SQL tools
- **FastAPI** - Async web framework
- **SQLAlchemy 2.0** - Modern async ORM
- **SQLite + aiosqlite** - Lightweight async database
- **Redis + aioredis** - Session storage and caching
- **Pydantic v2** - Data validation and settings management
- **Structlog** - Structured logging
- **uv** - Modern Python package management

## Development Commands

### Environment Setup
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Activate the environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

### Database Setup
```bash
# Create sample SQLite database
uv run text2sql create-db --db-path data/sample.db

# Or create in custom location
uv run text2sql create-db --db-path /path/to/your/database.db --force
```

### Configuration
Create a `.env` file in the project root:
```bash
# Database
DB_URL=sqlite:///data/sample.db

# Redis (optional, defaults to localhost)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
OPENAI_API_KEY=your-api-key-here

# App Settings
APP_DEBUG=false
APP_LOG_LEVEL=INFO
```

### Running the Application
```bash
# Start the development server
uv run text2sql serve --host 127.0.0.1 --port 8000 --reload

# Production mode
uv run text2sql serve --host 0.0.0.0 --port 8000 --workers 4
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/text2sql --cov-report=html

# Run only unit tests
uv run pytest tests/unit/ -m unit

# Run only integration tests
uv run pytest tests/integration/ -m integration
```

### CLI Usage
```bash
# Send a query via CLI
uv run text2sql query --question "How many employees are in Engineering?"

# Check API health
uv run text2sql health

# List active sessions
uv run text2sql sessions

# Get session info
uv run text2sql sessions --session-id your-session-id
```

### Code Quality
```bash
# Run linting
uv run ruff check src/ tests/

# Auto-fix linting issues
uv run ruff check --fix src/ tests/

# Type checking
uv run mypy src/

# Format code
uv run ruff format src/ tests/
```

## API Endpoints

### Core Endpoints
- **POST `/query`** - Natural language to SQL conversion and execution
- **GET `/health`** - System health check with service status
- **GET `/`** - API information

### Session Management
- **GET `/sessions`** - List active sessions
- **GET `/sessions/{session_id}/info`** - Get session information
- **GET `/sessions/{session_id}/history`** - Get conversation history
- **DELETE `/sessions/{session_id}`** - Delete session

### Database Inspection
- **GET `/database/tables`** - List database tables
- **GET `/database/schema`** - Get database schema information

### Example API Usage
```bash
# Query with curl
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many employees are in each department?",
    "session_id": "user-123",
    "message_type": "human"
  }'

# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/query" -Method Post -ContentType "application/json" -Body '{"question": "Show me all projects with budget over 500000", "session_id": "user-456", "message_type": "human"}'
```

## Configuration Management

The system uses **Pydantic Settings** for configuration with environment variable support:

### Settings Structure
- **AppSettings** - Application-level configuration
- **DatabaseSettings** - SQLite database configuration
- **RedisSettings** - Redis connection settings
- **LLMSettings** - LLM provider configuration

### Configuration Sources (in order of precedence)
1. Environment variables (e.g., `DB_URL`, `LLM_PROVIDER`)
2. `.env` file in project root
3. Default values in settings classes

### Sensitive Information
- Store API keys in environment variables or `sensitive/` directory
- Never commit API keys to version control
- Use different configurations for development/testing/production

## Important Implementation Details

- **Async Throughout** - Full async/await pattern for optimal performance
- **Type Safety** - Complete type hints and Pydantic validation
- **Error Handling** - Comprehensive error handling with structured logging
- **Session Management** - Redis-based conversation history with automatic cleanup
- **LangGraph Workflow** - State machine approach for reliable SQL generation
- **SQLite Optimization** - Configured for fast, lightweight operations
- **Health Monitoring** - Built-in health checks for all services
- **Production Ready** - Proper logging, monitoring, and configuration management

## Dependencies

Modern Python packages managed by **uv**:
- **Core**: `fastapi`, `uvicorn`, `pydantic>=2.0`, `sqlalchemy>=2.0`
- **LangChain**: `langchain>=0.2`, `langgraph>=0.1`, `langchain-openai`, `langchain-anthropic`
- **Database**: `aiosqlite`, `alembic`
- **Caching**: `redis[hiredis]`, `aioredis`
- **Utilities**: `structlog`, `click`, `httpx`, `python-dotenv`
- **Development**: `pytest`, `pytest-asyncio`, `ruff`, `mypy`