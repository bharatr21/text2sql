# Text2SQL

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2+-purple.svg)](https://langchain.com/)
[![uv](https://img.shields.io/badge/uv-managed-orange.svg)](https://github.com/astral-sh/uv)

A modern, production-ready Text-to-SQL system built with **LangChain**, **LangGraph**, and **FastAPI**. Convert natural language questions into SQL queries and execute them against your database with conversational context and session management.

## ✨ Features

- 🤖 **LangGraph-powered SQL Agent** - Intelligent workflow for reliable SQL generation
- 🚀 **Async-First Architecture** - Built for performance with async/await throughout
- 🗃️ **SQLite Integration** - Lightweight, fast database operations with aiosqlite
- 💬 **Conversational Interface** - Maintains context across questions with Redis sessions
- 🔌 **Multi-LLM Support** - Works with OpenAI, Anthropic, and Together AI
- 🛡️ **Type Safety** - Full type hints and Pydantic validation
- 📊 **Health Monitoring** - Built-in health checks and structured logging
- 🧪 **Comprehensive Testing** - Unit and integration tests with pytest
- 📚 **REST API** - Complete FastAPI application with automatic docs

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Redis server (optional, for session management)

### Installation

```bash
# Clone the repository
git clone https://github.com/bharatr21/text2sql.git
cd text2sql

# Install dependencies with uv
uv sync

# Activate the virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
```bash
# Database
DB_URL=sqlite:///data/sample.db

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
OPENAI_API_KEY=your-api-key-here

# Optional: Redis for sessions
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Create Sample Database

```bash
# Create a sample SQLite database with demo data
uv run text2sql create-db --db-path data/sample.db
```

### Start the Server

```bash
# Development mode with auto-reload
uv run text2sql serve --reload

# Production mode
uv run text2sql serve --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## 💻 Usage

### CLI Interface

```bash
# Send a query via CLI
uv run text2sql query --question "How many employees are in Engineering?"

# Check system health
uv run text2sql health

# List active sessions
uv run text2sql sessions

# Get session details
uv run text2sql sessions --session-id your-session-id
```

### API Examples

#### Query with curl
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me all employees with salary greater than 100000",
    "session_id": "user-123",
    "message_type": "human"
  }'
```

#### Query with Python
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/query",
        json={
            "question": "What is the average salary by department?",
            "session_id": "user-123",
            "message_type": "human"
        }
    )
    print(response.json())
```

### Sample Questions

Try these questions with the sample database:

- "How many employees are there?"
- "What is the average salary by department?"
- "Show me all projects that are in progress"
- "Who are the employees in Engineering?"
- "What is the total budget for all departments?"
- "Which projects have a budget over 500000?"

## 🏗️ Architecture

### Project Structure
```
src/text2sql/
├── core/           # App configuration, logging, FastAPI setup
├── agents/         # LangGraph SQL agent
├── services/       # Database, LLM, Redis, Session services
├── models/         # Pydantic schemas
├── utils/          # Database utilities and helpers
└── cli.py          # Command-line interface

tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── conftest.py     # Test configuration
```

### Key Components

- **SQLAgent**: LangGraph state machine for SQL generation workflow
- **DatabaseService**: Async SQLAlchemy 2.0 database operations
- **LLMService**: Multi-provider LLM interface (OpenAI, Anthropic, Together)
- **SessionService**: Redis-based conversation management
- **FastAPI App**: Modern async REST API with dependency injection

## 🧪 Testing

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

## 🔧 Development

### Code Quality

```bash
# Linting
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/

# Type checking
uv run mypy src/

# Format code
uv run ruff format src/ tests/
```

### Adding New LLM Providers

1. Install the provider's LangChain integration
2. Add provider configuration to `LLMSettings`
3. Implement provider initialization in `LLMService._create_*_llm()`
4. Update tests and documentation

### Database Support

While optimized for SQLite, the system can work with other databases:

1. Install appropriate async driver (e.g., `asyncpg` for PostgreSQL)
2. Update `DB_URL` in configuration
3. Modify `DatabaseService.async_engine` for database-specific settings

## 📚 API Documentation

Once the server is running, visit:

- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### Main Endpoints

- `POST /query` - Execute natural language query
- `GET /health` - System health check
- `GET /sessions` - List active sessions
- `GET /sessions/{id}/history` - Get conversation history
- `GET /database/tables` - List database tables
- `GET /database/schema` - Get database schema

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`uv run pytest`)
5. Run code quality checks (`uv run ruff check src/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) for the excellent LLM framework
- [LangGraph](https://github.com/langchain-ai/langgraph) for agent workflow orchestration
- [FastAPI](https://fastapi.tiangolo.com/) for the modern web framework
- [uv](https://github.com/astral-sh/uv) for fast Python package management

## 📧 Contact

**Bharat Raghunathan** - bharatraghunthan9767@gmail.com

Project Link: [https://github.com/bharatr21/text2sql](https://github.com/bharatr21/text2sql)
