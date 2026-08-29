import pytest
import os
import json
from backend.database.database import init_database, get_db_connection
from backend.database.seed import seed_foods, seed_default_user_and_profile, seed_today_meal_plan, DEFAULT_USER_ID

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_database()
    with get_db_connection() as conn:
        seed_foods(conn)
        seed_default_user_and_profile(conn)
        seed_today_meal_plan(conn)

def test_foods_table_seeded():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM foods")
        count = cursor.fetchone()[0]
        assert count >= 30

def test_user_profile_seeded():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (DEFAULT_USER_ID,))
        profile = cursor.fetchone()
        assert profile is not None
        assert profile["name"] == "Alex Morgan"
        assert profile["target_protein_g"] > 0
        assert profile["target_fiber_g"] > 0

def test_meal_plan_and_items():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meals WHERE user_id = ?", (DEFAULT_USER_ID,))
        meals = cursor.fetchall()
        assert len(meals) == 5  # breakfast, morning snack, lunch, evening snack, dinner
        
        # Verify items exist
        cursor.execute("SELECT COUNT(*) FROM meal_items")
        item_count = cursor.fetchone()[0]
        assert item_count > 5
