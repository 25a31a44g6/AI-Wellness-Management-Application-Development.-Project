import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

DATABASE_PATH = os.environ.get("DATABASE_URL", "sqlite:///./data/wellness.db").replace("sqlite:///", "")

def get_db_path() -> str:
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    return DATABASE_PATH

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initializes the database schema if tables do not exist."""
    db_path = get_db_path()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. User Profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                height_cm REAL,
                weight_kg REAL,
                activity_level TEXT,
                dietary_pref TEXT,
                allergies TEXT DEFAULT '[]',
                disliked_foods TEXT DEFAULT '[]',
                favorite_foods TEXT DEFAULT '[]',
                wake_time TEXT DEFAULT '06:30',
                sleep_time TEXT DEFAULT '22:30',
                work_start TEXT DEFAULT '09:00',
                work_end TEXT DEFAULT '17:00',
                exercise_time TEXT DEFAULT '18:00',
                preferred_meal_times TEXT DEFAULT '{}',
                cooking_facility TEXT DEFAULT 'Full Kitchen',
                food_availability TEXT DEFAULT 'Standard Groceries',
                target_calories REAL DEFAULT 2000.0,
                target_protein_g REAL DEFAULT 75.0,
                target_fiber_g REAL DEFAULT 30.0,
                target_water_ml REAL DEFAULT 2500.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 3. Foods table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS foods (
                food_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                standard_unit TEXT DEFAULT 'g',
                raw_weight_unit_g REAL DEFAULT 1.0,
                edible_weight_ratio REAL DEFAULT 1.0,
                calories_per_100g REAL NOT NULL,
                protein_per_100g REAL NOT NULL,
                carbohydrates_per_100g REAL NOT NULL,
                fat_per_100g REAL NOT NULL,
                fiber_per_100g REAL NOT NULL,
                serving_desc TEXT,
                prep_type TEXT DEFAULT 'raw',
                allergens TEXT DEFAULT 'none'
            )
        """)
        
        # 4. Meal Plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meal_plans (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                total_calories REAL DEFAULT 0.0,
                total_protein REAL DEFAULT 0.0,
                total_carbs REAL DEFAULT 0.0,
                total_fat REAL DEFAULT 0.0,
                total_fiber REAL DEFAULT 0.0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 5. Meals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id TEXT PRIMARY KEY,
                meal_plan_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                meal_type TEXT NOT NULL,
                name TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                completed_at TIMESTAMP,
                calories REAL DEFAULT 0.0,
                protein REAL DEFAULT 0.0,
                carbs REAL DEFAULT 0.0,
                fat REAL DEFAULT 0.0,
                fiber REAL DEFAULT 0.0,
                prep_notes TEXT,
                FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 6. Meal Items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meal_items (
                id TEXT PRIMARY KEY,
                meal_id TEXT NOT NULL,
                food_id TEXT NOT NULL,
                food_name TEXT NOT NULL,
                raw_quantity REAL NOT NULL,
                cooked_quantity REAL,
                unit TEXT DEFAULT 'g',
                calories REAL DEFAULT 0.0,
                protein REAL DEFAULT 0.0,
                carbs REAL DEFAULT 0.0,
                fat REAL DEFAULT 0.0,
                fiber REAL DEFAULT 0.0,
                substitution_for TEXT,
                FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE CASCADE,
                FOREIGN KEY (food_id) REFERENCES foods(food_id)
            )
        """)
        
        # 7. Water Logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS water_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                amount_ml REAL NOT NULL,
                date TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'quick_button',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 8. Meal Logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meal_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                meal_id TEXT NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE CASCADE
            )
        """)
        
        # 9. Daily Progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_progress (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                meals_completed INTEGER DEFAULT 0,
                meals_total INTEGER DEFAULT 0,
                water_consumed_ml REAL DEFAULT 0.0,
                water_target_ml REAL DEFAULT 2500.0,
                protein_consumed_g REAL DEFAULT 0.0,
                protein_target_g REAL DEFAULT 75.0,
                fiber_consumed_g REAL DEFAULT 0.0,
                fiber_target_g REAL DEFAULT 30.0,
                calories_consumed REAL DEFAULT 0.0,
                calories_target REAL DEFAULT 2000.0,
                adherence_score REAL DEFAULT 0.0,
                summary_notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, date),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 10. Schedule table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                event_name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                event_type TEXT DEFAULT 'routine',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 11. Agent Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                details TEXT,
                resolution TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 12. Substitutions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS substitutions (
                id TEXT PRIMARY KEY,
                meal_id TEXT NOT NULL,
                original_food_id TEXT NOT NULL,
                original_food_name TEXT NOT NULL,
                substituted_food_id TEXT NOT NULL,
                substituted_food_name TEXT NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE CASCADE
            )
        """)
