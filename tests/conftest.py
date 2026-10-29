"""
conftest.py — Shared fixtures for the entire test suite.

This file runs automatically. Any fixture defined here is available
to every test file without needing to import it.

Two types of fixtures here:
  1. API fixtures  — wait for the API server, provide base URL
  2. DB fixtures   — connect directly to PostgreSQL for data validation
"""
import pytest
import requests
import psycopg2
import time
import os


# ─── Configuration ───────────────────────────────────────
# These come from docker-compose.yml environment variables.

API_URL = os.environ.get("API_URL", "http://api:5000")

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "db"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "testdb"),
    "user": os.environ.get("DB_USER", "testuser"),
    "password": os.environ.get("DB_PASSWORD", "testpass"),
}


# ─── API Fixtures ────────────────────────────────────────

def wait_for_api(retries=15, delay=2):
    """Poll the health endpoint until the API + DB are both up."""
    for attempt in range(retries):
        try:
            r = requests.get(f"{API_URL}/health", timeout=3)
            if r.status_code == 200:
                print(f"API ready after {attempt + 1} attempt(s)")
                return
        except requests.ConnectionError:
            pass
        print(f"API not ready, retrying in {delay}s... ({attempt + 1}/{retries})")
        time.sleep(delay)
    raise Exception("API never became ready")


@pytest.fixture(scope="session", autouse=True)
def api_ready():
    """Runs once before all tests — waits for the full stack to be up."""
    wait_for_api()


@pytest.fixture
def api_url():
    """Provides the base API URL to any test that needs it."""
    return API_URL


# ─── Database Fixtures ───────────────────────────────────

@pytest.fixture
def db_connection():
    """
    Provides a direct PostgreSQL connection for database-level testing.

    Usage in tests:
        def test_something(db_connection):
            cur = db_connection.cursor()
            cur.execute("SELECT ...")

    The connection is automatically closed after the test finishes.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    yield conn            # <-- test runs here
    conn.close()          # <-- cleanup after test


@pytest.fixture
def db_cursor(db_connection):
    """
    Provides a cursor (shortcut so tests don't need to create one).

    Usage in tests:
        def test_something(db_cursor):
            db_cursor.execute("SELECT * FROM products")
            rows = db_cursor.fetchall()
    """
    cur = db_connection.cursor()
    yield cur
    cur.close()
