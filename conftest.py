import sys
import os
import pytest

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.database import init_database, get_db_connection, DATABASE_PATH
from backend.database.seed import seed_all

@pytest.fixture(autouse=True)
def clean_database():
    """Ensure each test starts with a freshly seeded database."""
    init_database()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM substitutions")
        cursor.execute("DELETE FROM agent_events")
        cursor.execute("DELETE FROM meal_logs")
        cursor.execute("DELETE FROM water_logs")
        cursor.execute("DELETE FROM daily_progress")
        cursor.execute("DELETE FROM meal_items")
        cursor.execute("DELETE FROM meals")
        cursor.execute("DELETE FROM meal_plans")
        cursor.execute("DELETE FROM profiles")
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM foods")
    seed_all()
    yield
