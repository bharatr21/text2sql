"""
Unit tests for database service.
"""

import pytest

from text2sql.services.database_service import DatabaseService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_service_initialization(database_service: DatabaseService):
    """Test database service initialization."""
    assert database_service is not None
    assert database_service.langchain_db is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_table_names(database_service: DatabaseService):
    """Test getting table names."""
    tables = await database_service.get_table_names()

    assert isinstance(tables, list)
    assert len(tables) > 0
    assert "employees" in tables
    assert "departments" in tables
    assert "projects" in tables


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_table_info(database_service: DatabaseService):
    """Test getting table information."""
    table_info = await database_service.get_table_info()

    assert isinstance(table_info, str)
    assert "employees" in table_info
    assert "departments" in table_info
    assert "CREATE TABLE" in table_info


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_query(database_service: DatabaseService):
    """Test executing a simple query."""
    results = await database_service.execute_query("SELECT COUNT(*) as count FROM employees")

    assert isinstance(results, list)
    assert len(results) == 1
    assert "count" in results[0]
    assert results[0]["count"] > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check(database_service: DatabaseService):
    """Test database health check."""
    is_healthy = await database_service.health_check()
    assert is_healthy is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_query_with_parameters(database_service: DatabaseService):
    """Test executing a query with parameters."""
    results = await database_service.execute_query(
        "SELECT name FROM employees WHERE department = :dept",
        parameters={"dept": "Engineering"}
    )

    assert isinstance(results, list)
    assert len(results) > 0
    for result in results:
        assert "name" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_query_error_handling(database_service: DatabaseService):
    """Test error handling for invalid queries."""
    with pytest.raises(Exception):
        await database_service.execute_query("SELECT * FROM non_existent_table")