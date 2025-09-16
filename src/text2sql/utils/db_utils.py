"""
Database utilities for creating sample data and managing SQLite databases.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any

from ..core.logging import get_logger

logger = get_logger(__name__)


def create_sample_database(db_path: str = "data/sample.db") -> str:
    """Create a sample SQLite database with demo data."""
    logger.info("Creating sample database", path=db_path)

    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create employees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                salary REAL NOT NULL,
                hire_date DATE NOT NULL,
                gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
                age INTEGER CHECK(age > 0),
                email TEXT UNIQUE
            )
        """)

        # Create departments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                budget REAL NOT NULL,
                location TEXT NOT NULL,
                manager_id INTEGER,
                FOREIGN KEY (manager_id) REFERENCES employees (id)
            )
        """)

        # Create projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                budget REAL NOT NULL,
                status TEXT CHECK(status IN ('Planning', 'In Progress', 'Completed', 'On Hold')),
                FOREIGN KEY (department_id) REFERENCES departments (id)
            )
        """)

        # Create employee_projects junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employee_projects (
                employee_id INTEGER,
                project_id INTEGER,
                role TEXT NOT NULL,
                hours_allocated REAL DEFAULT 0,
                PRIMARY KEY (employee_id, project_id),
                FOREIGN KEY (employee_id) REFERENCES employees (id),
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)

        # Insert sample data
        _insert_sample_data(cursor)

        conn.commit()
        logger.info("Sample database created successfully", path=db_path)

        return f"sqlite:///{db_path}"

    except Exception as e:
        logger.error("Failed to create sample database", error=str(e))
        conn.rollback()
        raise

    finally:
        conn.close()


def _insert_sample_data(cursor):
    """Insert sample data into the database."""

    # Insert departments
    departments = [
        ("Engineering", 2000000, "San Francisco", None),
        ("Marketing", 800000, "New York", None),
        ("Sales", 1200000, "Chicago", None),
        ("HR", 600000, "Austin", None),
        ("Finance", 900000, "Boston", None),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO departments (name, budget, location, manager_id) VALUES (?, ?, ?, ?)",
        departments
    )

    # Insert employees
    employees = [
        ("Alice Johnson", "Engineering", 120000, "2020-01-15", "Female", 30, "alice.johnson@company.com"),
        ("Bob Smith", "Engineering", 115000, "2019-03-22", "Male", 32, "bob.smith@company.com"),
        ("Carol Davis", "Marketing", 85000, "2021-06-10", "Female", 28, "carol.davis@company.com"),
        ("David Wilson", "Sales", 95000, "2020-09-05", "Male", 35, "david.wilson@company.com"),
        ("Eve Brown", "HR", 75000, "2022-01-20", "Female", 26, "eve.brown@company.com"),
        ("Frank Miller", "Finance", 90000, "2019-11-12", "Male", 40, "frank.miller@company.com"),
        ("Grace Lee", "Engineering", 125000, "2018-07-08", "Female", 34, "grace.lee@company.com"),
        ("Henry Garcia", "Marketing", 88000, "2021-04-15", "Male", 29, "henry.garcia@company.com"),
        ("Ivy Rodriguez", "Sales", 98000, "2020-12-03", "Female", 31, "ivy.rodriguez@company.com"),
        ("Jack Taylor", "Engineering", 110000, "2022-02-28", "Male", 27, "jack.taylor@company.com"),
        ("Karen Anderson", "HR", 82000, "2019-08-14", "Female", 33, "karen.anderson@company.com"),
        ("Leo Martinez", "Finance", 95000, "2021-10-07", "Male", 36, "leo.martinez@company.com"),
        ("Mia Thompson", "Engineering", 130000, "2017-05-20", "Female", 37, "mia.thompson@company.com"),
        ("Nathan White", "Marketing", 92000, "2020-07-25", "Male", 30, "nathan.white@company.com"),
        ("Olivia Harris", "Sales", 105000, "2018-12-11", "Female", 38, "olivia.harris@company.com"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO employees (name, department, salary, hire_date, gender, age, email) VALUES (?, ?, ?, ?, ?, ?, ?)",
        employees
    )

    # Insert projects
    projects = [
        ("Website Redesign", 1, "2023-01-01", "2023-06-30", 500000, "Completed"),
        ("Mobile App Development", 1, "2023-03-15", "2023-12-31", 800000, "In Progress"),
        ("Marketing Campaign Q4", 2, "2023-10-01", "2023-12-31", 300000, "In Progress"),
        ("Sales Training Program", 3, "2023-02-01", "2023-05-31", 150000, "Completed"),
        ("HR System Upgrade", 4, "2023-06-01", "2023-09-30", 200000, "In Progress"),
        ("Financial Audit", 5, "2023-01-15", "2023-03-15", 100000, "Completed"),
        ("Cloud Migration", 1, "2023-08-01", "2024-02-29", 1200000, "In Progress"),
        ("Customer Portal", 1, "2023-11-01", "2024-04-30", 600000, "Planning"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO projects (name, department_id, start_date, end_date, budget, status) VALUES (?, ?, ?, ?, ?, ?)",
        projects
    )

    # Insert employee-project relationships
    employee_projects = [
        (1, 1, "Lead Developer", 40),  # Alice on Website Redesign
        (2, 1, "Backend Developer", 35),  # Bob on Website Redesign
        (7, 1, "Frontend Developer", 30),  # Grace on Website Redesign
        (1, 2, "Technical Lead", 40),  # Alice on Mobile App
        (10, 2, "Developer", 40),  # Jack on Mobile App
        (13, 2, "Senior Developer", 35),  # Mia on Mobile App
        (3, 3, "Marketing Manager", 40),  # Carol on Marketing Campaign
        (8, 3, "Marketing Specialist", 30),  # Henry on Marketing Campaign
        (4, 4, "Sales Manager", 20),  # David on Sales Training
        (9, 4, "Sales Specialist", 25),  # Ivy on Sales Training
        (5, 5, "Project Manager", 30),  # Eve on HR System
        (11, 5, "HR Specialist", 20),  # Karen on HR System
        (6, 6, "Financial Analyst", 40),  # Frank on Financial Audit
        (12, 6, "Finance Manager", 30),  # Leo on Financial Audit
        (1, 7, "Architecture Lead", 25),  # Alice on Cloud Migration
        (2, 7, "DevOps Engineer", 40),  # Bob on Cloud Migration
        (13, 7, "Senior Engineer", 30),  # Mia on Cloud Migration
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO employee_projects (employee_id, project_id, role, hours_allocated) VALUES (?, ?, ?, ?)",
        employee_projects
    )


def get_sample_data() -> Dict[str, List[Dict[str, Any]]]:
    """Get sample data for testing without creating a database."""
    return {
        "employees": [
            {"id": 1, "name": "Alice Johnson", "department": "Engineering", "salary": 120000, "gender": "Female", "age": 30},
            {"id": 2, "name": "Bob Smith", "department": "Engineering", "salary": 115000, "gender": "Male", "age": 32},
            {"id": 3, "name": "Carol Davis", "department": "Marketing", "salary": 85000, "gender": "Female", "age": 28},
            {"id": 4, "name": "David Wilson", "department": "Sales", "salary": 95000, "gender": "Male", "age": 35},
            {"id": 5, "name": "Eve Brown", "department": "HR", "salary": 75000, "gender": "Female", "age": 26},
        ],
        "departments": [
            {"id": 1, "name": "Engineering", "budget": 2000000, "location": "San Francisco"},
            {"id": 2, "name": "Marketing", "budget": 800000, "location": "New York"},
            {"id": 3, "name": "Sales", "budget": 1200000, "location": "Chicago"},
            {"id": 4, "name": "HR", "budget": 600000, "location": "Austin"},
            {"id": 5, "name": "Finance", "budget": 900000, "location": "Boston"},
        ],
        "projects": [
            {"id": 1, "name": "Website Redesign", "department_id": 1, "budget": 500000, "status": "Completed"},
            {"id": 2, "name": "Mobile App Development", "department_id": 1, "budget": 800000, "status": "In Progress"},
            {"id": 3, "name": "Marketing Campaign Q4", "department_id": 2, "budget": 300000, "status": "In Progress"},
        ]
    }