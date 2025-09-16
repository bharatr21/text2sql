"""
Database utilities for creating sample data and managing SQLite databases.
Includes both corporate sample data and NORP (social science) datasets.
"""

import sqlite3
import csv
from pathlib import Path
from typing import Dict, List, Any

from ..core.logging import get_logger

logger = get_logger(__name__)


def create_sample_database(db_path: str = "data/sample.db") -> str:
    """Create a sample SQLite database with NORP social science data."""
    logger.info("Creating NORP sample database", path=db_path)

    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create NORP (social science) tables
        _create_norp_tables(cursor)
        _insert_norp_data(cursor)

        conn.commit()
        logger.info("NORP sample database created successfully", path=db_path)

        return f"sqlite:///{db_path}"

    except Exception as e:
        logger.error("Failed to create sample database", error=str(e))
        conn.rollback()
        raise

    finally:
        conn.close()




def _create_norp_tables(cursor):
    """Create NORP social science data tables."""

    # US Shootings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS us_shootings (
            incident_id INTEGER PRIMARY KEY,
            address TEXT,
            incident_date DATE,
            state TEXT,
            city_or_country TEXT,
            victims_killed INTEGER,
            victims_injured INTEGER,
            suspects_injured INTEGER,
            suspects_killed INTEGER,
            suspects_arrested INTEGER
        )
    """)

    # Homelessness demographics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS homelessness_demographics (
            calendar_year TEXT,
            location TEXT,
            age_group TEXT,
            experiencing_homelessness_count INTEGER
        )
    """)

    # NYC Crime data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nyc_crime_data (
            crime_id INTEGER PRIMARY KEY,
            report TEXT,
            crime_date DATE,
            crime_time TIME,
            crime_class TEXT,
            crime_type TEXT,
            area_name TEXT,
            latitude REAL,
            longitude REAL
        )
    """)

    # Economic income and benefits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS economic_income_and_benefits (
            year INTEGER,
            id TEXT,
            zipcode TEXT,
            total_households INTEGER,
            median_household_income REAL,
            mean_household_income REAL
        )
    """)

    # US Population table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS us_population (
            census_year INTEGER,
            state TEXT,
            population_count INTEGER
        )
    """)

    # US Population by County table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS us_population_county (
            population_count INTEGER,
            county TEXT
        )
    """)

    # Food access table (simplified - original has 80+ columns)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_access (
            census_tract INTEGER,
            state TEXT,
            county TEXT,
            urban BOOLEAN,
            population_2010 INTEGER,
            low_income_tracts BOOLEAN,
            poverty_rate REAL,
            median_family_income REAL,
            low_access_population_1_mile REAL,
            low_access_population_10_miles REAL,
            low_access_population_20_miles REAL
        )
    """)




def _insert_norp_data(cursor):
    """Insert NORP social science sample data."""

    # US Shootings data
    us_shootings_data = [
        (92194, "Rockingham Street and Berkley Avenue Extended", "2014-01-01", "Virginia", "Norfolk", 2, 2, 0, 0, 0),
        (92704, "Farmers Boulevard and 133rd Avenue", "2014-01-03", "New York", "Queens", 1, 3, 0, 0, 0),
        (94514, "829 Parade St", "2014-01-05", "Pennsylvania", "Erie", 1, 3, 0, 0, 0),
        (95146, "3430 W. Capitol Street", "2014-01-11", "Mississippi", "Jackson", 0, 4, 0, 0, 0),
        (95500, "3600 block of Highway 80 W", "2014-01-12", "Louisiana", "Tallulah", 0, 6, 0, 0, 8),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO us_shootings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        us_shootings_data
    )

    # Homelessness demographics data
    homelessness_data = [
        ("2017", "California", "25-34", 28654),
        ("2017", "California", "35-44", 25831),
        ("2017", "California", "45-54", 27651),
        ("2017", "California", "55-64", 23396),
        ("2017", "California", "65+", 7111),
        ("2018", "California", "25-34", 29200),
        ("2018", "California", "35-44", 26100),
        ("2018", "California", "45-54", 28000),
        ("2018", "New York", "25-34", 15420),
        ("2018", "New York", "35-44", 14230),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO homelessness_demographics VALUES (?, ?, ?, ?)",
        homelessness_data
    )

    # NYC Crime data
    nyc_crime_data = [
        (1, "RPT0012345", "2024-01-01", "14:30:00", "Felony", "Assault", "Manhattan", 40.712776, -74.005974),
        (2, "RPT0012346", "2024-01-02", "09:15:00", "Misdemeanor", "Theft", "Brooklyn", 40.678178, -73.944158),
        (3, "RPT0012347", "2024-01-03", "20:45:00", "Violation", "Disorderly Conduct", "Queens", 40.728224, -73.794852),
        (4, "RPT0012348", "2024-01-04", "11:00:00", "Felony", "Robbery", "Bronx", 40.844782, -73.864827),
        (5, "RPT0012349", "2024-01-05", "22:10:00", "Misdemeanor", "Trespass", "Staten Island", 40.579532, -74.150201),
        (6, "RPT0012350", "2024-01-06", "17:25:00", "Felony", "Drug Possession", "Manhattan", 40.715957, -74.011170),
        (7, "RPT0012351", "2024-01-07", "05:45:00", "Violation", "Public Intoxication", "Brooklyn", 40.680875, -73.950942),
        (8, "RPT0012352", "2024-01-08", "18:35:00", "Misdemeanor", "Vandalism", "Queens", 40.721622, -73.791907),
        (9, "RPT0012353", "2024-01-09", "08:55:00", "Felony", "Burglary", "Bronx", 40.844144, -73.866348),
        (10, "RPT0012354", "2024-01-10", "21:15:00", "Misdemeanor", "Petty Theft", "Staten Island", 40.570342, -74.134756),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO nyc_crime_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        nyc_crime_data
    )

    # Economic income and benefits data
    economic_data = [
        (2021, "ID0001", "10001", 3500, 75000, 82000),
        (2021, "ID0002", "10002", 4200, 68000, 77000),
        (2021, "ID0003", "10003", 5000, 62000, 71000),
        (2021, "ID0004", "10004", 3200, 84000, 92000),
        (2021, "ID0005", "10005", 4500, 73000, 80500),
        (2022, "ID0006", "10001", 3550, 76000, 83000),
        (2022, "ID0007", "10002", 4250, 69000, 78000),
        (2022, "ID0008", "10003", 5050, 63000, 72000),
        (2022, "ID0009", "10004", 3250, 85000, 93000),
        (2022, "ID0010", "10005", 4550, 74000, 81500),
        (2023, "ID0011", "10001", 3600, 77000, 84000),
        (2023, "ID0012", "10002", 4300, 70000, 79000),
        (2023, "ID0013", "10003", 5100, 64000, 73000),
        (2023, "ID0014", "10004", 3300, 86000, 94000),
        (2023, "ID0015", "10005", 4600, 75000, 82500),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO economic_income_and_benefits VALUES (?, ?, ?, ?, ?, ?)",
        economic_data
    )

    # US Population data
    us_population_data = [
        (2020, "California", 39538223),
        (2020, "Texas", 29145505),
        (2020, "Florida", 21538187),
        (2020, "New York", 20201249),
        (2020, "Pennsylvania", 13002700),
        (2021, "California", 39237836),
        (2021, "Texas", 29527941),
        (2021, "Florida", 22610726),
        (2021, "New York", 19835913),
        (2021, "Pennsylvania", 12964056),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO us_population VALUES (?, ?, ?)",
        us_population_data
    )

    # US Population by County data
    us_population_county_data = [
        (10000000, "Los Angeles County, CA"),
        (2633516, "Cook County, IL"),
        (2228718, "Harris County, TX"),
        (1860669, "Maricopa County, AZ"),
        (1576876, "San Diego County, CA"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO us_population_county VALUES (?, ?)",
        us_population_county_data
    )

    # Food access data (simplified sample)
    food_access_data = [
        (6001950100, "Alabama", "Autauga County", 0, 54571, 0, 0.12, 52345.67, 123.45, 456.78, 789.01),
        (6001950200, "Alabama", "Autauga County", 1, 12345, 1, 0.25, 38920.33, 234.56, 567.89, 890.12),
        (6001950300, "Alabama", "Baldwin County", 0, 67890, 0, 0.08, 67543.21, 345.67, 678.90, 901.23),
        (6001950400, "California", "Los Angeles County", 1, 89012, 1, 0.18, 45678.90, 456.78, 789.01, 123.45),
        (6001950500, "California", "Orange County", 1, 56789, 0, 0.06, 89012.34, 567.89, 890.12, 234.56),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO food_access VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        food_access_data
    )


def get_sample_data() -> Dict[str, List[Dict[str, Any]]]:
    """Get NORP sample data for testing without creating a database."""
    return {
        "us_shootings": [
            {"incident_id": 92194, "address": "Rockingham Street", "state": "Virginia", "city_or_country": "Norfolk", "victims_killed": 2, "victims_injured": 2},
            {"incident_id": 92704, "address": "Farmers Boulevard", "state": "New York", "city_or_country": "Queens", "victims_killed": 1, "victims_injured": 3},
            {"incident_id": 94514, "address": "829 Parade St", "state": "Pennsylvania", "city_or_country": "Erie", "victims_killed": 1, "victims_injured": 3},
        ],
        "nyc_crime_data": [
            {"crime_id": 1, "crime_class": "Felony", "crime_type": "Assault", "area_name": "Manhattan"},
            {"crime_id": 2, "crime_class": "Misdemeanor", "crime_type": "Theft", "area_name": "Brooklyn"},
            {"crime_id": 3, "crime_class": "Violation", "crime_type": "Disorderly Conduct", "area_name": "Queens"},
        ],
        "economic_income_and_benefits": [
            {"year": 2021, "zipcode": "10001", "median_household_income": 75000, "mean_household_income": 82000},
            {"year": 2022, "zipcode": "10001", "median_household_income": 76000, "mean_household_income": 83000},
            {"year": 2023, "zipcode": "10001", "median_household_income": 77000, "mean_household_income": 84000},
        ],
        "homelessness_demographics": [
            {"calendar_year": "2017", "location": "California", "age_group": "25-34", "experiencing_homelessness_count": 28654},
            {"calendar_year": "2017", "location": "California", "age_group": "35-44", "experiencing_homelessness_count": 25831},
            {"calendar_year": "2018", "location": "New York", "age_group": "25-34", "experiencing_homelessness_count": 15420},
        ],
        "us_population": [
            {"census_year": 2020, "state": "California", "population_count": 39538223},
            {"census_year": 2020, "state": "Texas", "population_count": 29145505},
            {"census_year": 2021, "state": "California", "population_count": 39237836},
        ],
        "food_access": [
            {"census_tract": 6001950100, "state": "Alabama", "county": "Autauga County", "poverty_rate": 0.12},
            {"census_tract": 6001950400, "state": "California", "county": "Los Angeles County", "poverty_rate": 0.18},
        ]
    }


def get_sample_questions_from_csv(csv_path: str = "data/norp_llm_test_prompts.csv") -> List[str]:
    """Load sample questions from CSV file."""
    questions = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                questions.append(row['Query'])
    except FileNotFoundError:
        logger.warning("CSV file not found, using fallback questions", path=csv_path)
        return get_fallback_questions()
    except Exception as e:
        logger.error("Error reading CSV file", error=str(e), path=csv_path)
        return get_fallback_questions()

    return questions


def get_fallback_questions() -> List[str]:
    """Get fallback sample questions for NORP datasets."""
    return [
        # Population
        "What was the population of Alabama in the 2010 Census?",
        "Which state had the highest population in the 2010 Census?",
        "List all states with a population greater than 5 million in 2010.",
        "What is the total population of all states combined in 2010?",
        "What is the population of Los Angeles County?",

        # Crime & Shootings
        "How many shooting incidents occurred in New York?",
        "Which state had the highest number of victims killed in shootings?",
        "Get a list of all shooting incidents in 2014 where at least 2 victims were killed.",
        "Retrieve all shootings in Queens, New York, along with the number of injured victims.",
        "List all shootings where more than 5 people were injured.",
        "For each state, get the total number of suspects arrested in shooting incidents.",

        # NYC Crime Data
        "Get all criminal records from NYC where the crime classification is 'Felony'.",
        "How many incidents of Assault occurred in Manhattan?",
        "List all crime types reported in Queens along with their classifications.",
        "Get the number of crimes reported in Brooklyn for January 2024.",
        "Which area had the highest number of crime incidents in January 2024?",
        "Find all burglary cases reported in the Bronx.",

        # Homelessness
        "What is the number of individuals experiencing homelessness in California?",
        "List the top 5 locations with the highest number of homeless individuals.",
        "Get the homelessness count for different age groups in New York.",
        "Which state has the highest number of people experiencing homelessness?",

        # Food Access & Poverty
        "Which counties have the highest poverty rates?",
        "List the top 10 counties with the lowest access to food.",
        "Get a list of census tracts where more than 50% of the population has low food access.",
        "Which states have the highest number of food-insecure households?",

        # Correlational Analysis
        "Compare the population of New York and Texas over the last three census years.",
        "Find the correlation between homelessness and poverty rates in different states.",
        "Get the number of shooting incidents per 1 million residents in each state.",
        "Compare the number of felony crimes with the population of each borough in NYC.",
        "Which areas with high homelessness rates also have high crime rates?",
    ]


def get_sample_questions() -> List[str]:
    """Get sample questions, trying CSV first, then fallback."""
    return get_sample_questions_from_csv()