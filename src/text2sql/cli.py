"""
Command line interface for the Text2SQL application.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
import uvicorn

from .core.app import create_app
from .core.config import Settings, settings
from .core.logging import configure_logging, get_logger
from .utils.db_utils import create_sample_database, get_sample_questions


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--log-level", default="INFO", help="Set log level")
@click.pass_context
def main(ctx, debug: bool, log_level: str):
    """Text2SQL - Modern Text-to-SQL system using LangChain and LangGraph."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["log_level"] = log_level

    # Configure logging
    configure_logging(log_level, debug)


@main.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
@click.option("--workers", default=1, type=int, help="Number of worker processes")
@click.option("--config", type=click.Path(exists=True), help="Configuration file path")
@click.pass_context
def serve(ctx, host: str, port: int, reload: bool, workers: int, config: Optional[str]):
    """Start the Text2SQL API server."""
    logger = get_logger(__name__)

    # Load configuration
    if config:
        # TODO: Load configuration from file
        logger.info("Loading configuration from file", config_file=config)

    # Update settings
    settings.app.host = host
    settings.app.port = port
    settings.app.reload = reload
    settings.app.debug = ctx.obj["debug"]

    logger.info(
        "Starting Text2SQL server",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        debug=ctx.obj["debug"],
    )

    # Create and run the app
    app = create_app(settings)

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
        log_level=ctx.obj["log_level"].lower(),
    )


@main.command()
@click.option("--db-path", default="data/sample.db", help="Database file path")
@click.option("--force", is_flag=True, help="Overwrite existing database")
def create_db(db_path: str, force: bool):
    """Create a sample SQLite database with demo data."""
    logger = get_logger(__name__)

    db_file = Path(db_path)
    if db_file.exists() and not force:
        click.echo(f"Database already exists at {db_path}. Use --force to overwrite.")
        return

    try:
        db_url = create_sample_database(db_path)
        logger.info("NORP sample database created", path=db_path, url=db_url)
        click.echo(f"✅ NORP sample database created at: {db_path}")
        click.echo(f"Database URL: {db_url}")
        click.echo(f"📊 Database includes: US Shootings, NYC Crime, Homelessness, Economic Data, Population, Food Access")
    except Exception as e:
        logger.error("Failed to create database", error=str(e))
        click.echo(f"❌ Failed to create database: {e}")
        sys.exit(1)


@main.command()
@click.option("--limit", default=10, help="Number of sample questions to show")
def sample_questions(limit: int):
    """Show sample questions for the NORP datasets."""
    logger = get_logger(__name__)

    try:
        questions = get_sample_questions()

        click.echo("📝 Sample Questions for NORP Social Science Datasets:")
        click.echo("=" * 60)

        for i, question in enumerate(questions[:limit], 1):
            click.echo(f"{i:2d}. {question}")

        if len(questions) > limit:
            click.echo(f"\n... and {len(questions) - limit} more questions available")

        click.echo(f"\n💡 Try these with: uv run text2sql query --question \"[question]\"")

    except Exception as e:
        logger.error("Failed to load sample questions", error=str(e))
        click.echo(f"❌ Failed to load sample questions: {e}")


@main.command()
@click.option("--question", prompt="Enter your question", help="Natural language question")
@click.option("--session-id", default="cli-session", help="Session ID for conversation")
@click.option("--base-url", default="http://127.0.0.1:8000", help="API base URL")
async def query(question: str, session_id: str, base_url: str):
    """Send a query to the Text2SQL API."""
    import httpx

    logger = get_logger(__name__)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/query",
                json={
                    "question": question,
                    "session_id": session_id,
                    "message_type": "human",
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                result = response.json()
                click.echo("🤖 SQL Query:")
                click.echo(result.get("sql_query", "No SQL query generated"))
                click.echo("\n📊 Results:")
                click.echo(result.get("query_results", "No results"))

                if result.get("execution_time"):
                    click.echo(f"\n⏱️  Execution Time: {result['execution_time']:.2f}s")

            else:
                click.echo(f"❌ API Error: {response.status_code} - {response.text}")

    except Exception as e:
        logger.error("Failed to send query", error=str(e))
        click.echo(f"❌ Error: {e}")


@main.command()
@click.option("--base-url", default="http://127.0.0.1:8000", help="API base URL")
async def health(base_url: str):
    """Check the health of the Text2SQL API."""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health", timeout=10.0)

            if response.status_code == 200:
                result = response.json()
                status = result.get("status", "unknown")

                if status == "healthy":
                    click.echo("✅ API is healthy")
                else:
                    click.echo(f"⚠️  API status: {status}")

                click.echo(f"Version: {result.get('version', 'unknown')}")

                services = result.get("services", {})
                for service, service_status in services.items():
                    icon = "✅" if service_status == "healthy" else "❌"
                    click.echo(f"{icon} {service}: {service_status}")

            else:
                click.echo(f"❌ API Error: {response.status_code} - {response.text}")

    except Exception as e:
        click.echo(f"❌ Connection Error: {e}")


@main.command()
@click.option("--session-id", help="Session ID to inspect")
@click.option("--base-url", default="http://127.0.0.1:8000", help="API base URL")
async def sessions(session_id: Optional[str], base_url: str):
    """List sessions or inspect a specific session."""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            if session_id:
                # Get specific session info
                response = await client.get(f"{base_url}/sessions/{session_id}/info")
                if response.status_code == 200:
                    info = response.json()
                    click.echo(f"Session: {info['session_id']}")
                    click.echo(f"Created: {info['created_at']}")
                    click.echo(f"Last Activity: {info['last_activity']}")
                    click.echo(f"Messages: {info['message_count']}")
                    click.echo(f"Active: {info['is_active']}")

                    # Get history
                    history_response = await client.get(f"{base_url}/sessions/{session_id}/history")
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        history = history_data.get("history", [])
                        click.echo(f"\nConversation History ({len(history)} messages):")
                        for msg in history[-10:]:  # Show last 10 messages
                            click.echo(f"[{msg['role']}] {msg['content'][:100]}...")
                else:
                    click.echo(f"❌ Session not found: {session_id}")
            else:
                # List all sessions
                response = await client.get(f"{base_url}/sessions")
                if response.status_code == 200:
                    result = response.json()
                    sessions_list = result.get("sessions", [])
                    click.echo(f"Active Sessions ({len(sessions_list)}):")
                    for s in sessions_list:
                        click.echo(f"  • {s}")
                else:
                    click.echo("❌ Failed to fetch sessions")

    except Exception as e:
        click.echo(f"❌ Error: {e}")


# Async command wrapper
def async_command(f):
    """Decorator to run async click commands."""
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


# Apply async wrapper to async commands
query = async_command(query)
health = async_command(health)
sessions = async_command(sessions)


if __name__ == "__main__":
    main()