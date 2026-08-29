import csv
import os
import json
import uuid
from datetime import datetime, date
from backend.database.database import get_db_connection, init_database
from backend.services.nutrition_service import calculate_food_nutrition

DEFAULT_USER_ID = "user_001"

def seed_foods(conn):
    """Seed foods table from data/foods.csv."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM foods")
    if cursor.fetchone()[0] > 0:
        return

    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "foods.csv")
    if not os.path.exists(csv_path):
        return

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO foods (
                    food_id, name, category, standard_unit, raw_weight_unit_g,
                    edible_weight_ratio, calories_per_100g, protein_per_100g,
                    carbohydrates_per_100g, fat_per_100g, fiber_per_100g,
                    serving_desc, prep_type, allergens
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["food_id"],
                row["name"],
                row["category"],
                row.get("standard_unit", "g"),
                float(row.get("raw_weight_unit_g", 1.0)),
                float(row.get("edible_weight_ratio", 1.0)),
                float(row["calories_per_100g"]),
                float(row["protein_per_100g"]),
                float(row["carbohydrates_per_100g"]),
                float(row["fat_per_100g"]),
                float(row["fiber_per_100g"]),
                row.get("serving_desc", ""),
                row.get("prep_type", "raw"),
                row.get("allergens", "none")
            ))

def seed_default_user_and_profile(conn):
    """Seed a default user and personalized wellness profile."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE id = ?", (DEFAULT_USER_ID,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (id, name, email)
            VALUES (?, ?, ?)
        """, (DEFAULT_USER_ID, "Alex Morgan", "alex.wellness@example.com"))

    cursor.execute("SELECT COUNT(*) FROM profiles WHERE user_id = ?", (DEFAULT_USER_ID,))
    if cursor.fetchone()[0] == 0:
        allergies = json.dumps([])
        disliked_foods = json.dumps(["bitter gourd", "excessive oil"])
        favorite_foods = json.dumps(["Oats", "Greek Yogurt", "Paneer", "Almonds", "Chicken Breast"])
        preferred_meal_times = json.dumps({
            "breakfast": "08:00",
            "morning_snack": "11:00",
            "lunch": "13:30",
            "evening_snack": "17:00",
            "dinner": "20:00"
        })

        cursor.execute("""
            INSERT INTO profiles (
                id, user_id, name, age, gender, height_cm, weight_kg,
                activity_level, dietary_pref, allergies, disliked_foods, favorite_foods,
                wake_time, sleep_time, work_start, work_end, exercise_time,
                preferred_meal_times, cooking_facility, food_availability,
                target_calories, target_protein_g, target_fiber_g, target_water_ml
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            DEFAULT_USER_ID,
            "Alex Morgan",
            26,
            "Non-binary / Other",
            175.0,
            68.0,
            "Moderately Active",
            "Flexitarian / High-Protein",
            allergies,
            disliked_foods,
            favorite_foods,
            "06:45",
            "23:00",
            "09:00",
            "17:30",
            "18:00",
            preferred_meal_times,
            "Full Kitchen (Stove, Microwave, Refrigerator)",
            "Fresh Groceries, Supermarket, Weekly Farmers Market",
            2100.0,
            90.0,
            32.0,
            2750.0
        ))

def seed_today_meal_plan(conn):
    """Seed today's default balanced meal plan if none exists."""
    today_str = date.today().isoformat()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM meal_plans WHERE user_id = ? AND date = ?", (DEFAULT_USER_ID, today_str))
    existing = cursor.fetchone()
    if existing:
        return

    meal_plan_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO meal_plans (id, user_id, date, status, notes)
        VALUES (?, ?, ?, 'active', 'Personalized daily plan balanced for steady energy and optimal protein-fiber distribution.')
    """, (meal_plan_id, DEFAULT_USER_ID, today_str))

    cursor.execute("SELECT * FROM foods")
    food_map = {row["food_id"]: dict(row) for row in cursor.fetchall()}

    planned_meals_spec = [
        {
            "meal_type": "breakfast",
            "name": "High-Fiber Oatmeal Bowl with Greek Yogurt & Chia",
            "time": "08:00",
            "prep_notes": "Combine rolled oats with warm water or milk, top with Greek yogurt, sliced banana, chia seeds, and chopped almonds.",
            "items": [
                ("food_001", 50.0, "g"),     # Oats 50g
                ("food_014", 100.0, "g"),    # Greek Yogurt 100g
                ("food_023", 1.0, "piece"),  # 1 Banana (118g)
                ("food_021", 10.0, "g"),     # Chia Seeds 10g
                ("food_019", 15.0, "g")      # Almonds 15g
            ]
        },
        {
            "meal_type": "morning_snack",
            "name": "Fresh Sprouted Moong Salad with Lemon & Cucumber",
            "time": "11:00",
            "prep_notes": "Toss sprouted moong with diced cucumber, carrot, fresh herbs, and a squeeze of lemon.",
            "items": [
                ("food_010", 100.0, "g"),    # Sprouted Moong 100g
                ("food_030", 80.0, "g"),     # Cucumber 80g
                ("food_029", 40.0, "g")      # Carrot 40g
            ]
        },
        {
            "meal_type": "lunch",
            "name": "Yellow Dal & Paneer Bowl with Brown Rice & Steamed Greens",
            "time": "13:30",
            "prep_notes": "Simmer yellow lentils with turmeric and cumin. Serve with brown rice, sautéed paneer cubes, and steamed spinach.",
            "items": [
                ("food_006", 45.0, "g"),     # Moong Dal 45g (raw)
                ("food_002", 60.0, "g"),     # Brown Rice 60g (raw)
                ("food_012", 60.0, "g"),     # Paneer 60g
                ("food_027", 100.0, "g")     # Spinach 100g (raw)
            ]
        },
        {
            "meal_type": "evening_snack",
            "name": "Crispy Roasted Peanuts & Crisp Apple",
            "time": "17:00",
            "prep_notes": "Enjoy lightly roasted peanuts alongside a crisp sliced fresh apple for sustained pre-workout energy.",
            "items": [
                ("food_034", 25.0, "g"),     # Roasted Peanuts 25g
                ("food_024", 1.0, "piece")   # 1 Apple (150g)
            ]
        },
        {
            "meal_type": "dinner",
            "name": "Herb Grilled Chicken / Tofu Medley with Warm Quinoa & Roasted Broccoli",
            "time": "20:00",
            "prep_notes": "Pan-sear seasoned chicken breast (or tofu for plant-based option) with garlic herbs, paired with fluffy quinoa and broccoli.",
            "items": [
                ("food_017", 120.0, "g"),    # Chicken breast 120g
                ("food_004", 50.0, "g"),     # Quinoa 50g (raw)
                ("food_028", 120.0, "g")     # Broccoli 120g (raw)
            ]
        }
    ]

    total_plan_cals = 0.0
    total_plan_prot = 0.0
    total_plan_carbs = 0.0
    total_plan_fat = 0.0
    total_plan_fiber = 0.0

    for meal_data in planned_meals_spec:
        meal_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO meals (
                id, meal_plan_id, user_id, meal_type, name, scheduled_time,
                status, calories, protein, carbs, fat, fiber, prep_notes
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', 0, 0, 0, 0, 0, ?)
        """, (
            meal_id, meal_plan_id, DEFAULT_USER_ID, meal_data["meal_type"],
            meal_data["name"], meal_data["time"], meal_data["prep_notes"]
        ))

        meal_cals = 0.0
        meal_prot = 0.0
        meal_carbs = 0.0
        meal_fat = 0.0
        meal_fiber = 0.0

        for food_id, raw_qty, unit in meal_data["items"]:
            food_info = food_map.get(food_id)
            if not food_info:
                continue
            
            calc_res = calculate_food_nutrition(food_info, raw_qty, unit)
            nutr = calc_res["nutrition"]

            meal_cals += nutr["calories"]
            meal_prot += nutr["protein"]
            meal_carbs += nutr["carbohydrates"]
            meal_fat += nutr["fat"]
            meal_fiber += nutr["fiber"]

            item_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO meal_items (
                    id, meal_id, food_id, food_name, raw_quantity, cooked_quantity,
                    unit, calories, protein, carbs, fat, fiber
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id, meal_id, food_id, food_info["name"], raw_qty,
                calc_res["cooked_weight_g"], unit, nutr["calories"], nutr["protein"],
                nutr["carbohydrates"], nutr["fat"], nutr["fiber"]
            ))

        cursor.execute("""
            UPDATE meals SET
                calories = ?, protein = ?, carbs = ?, fat = ?, fiber = ?
            WHERE id = ?
        """, (
            round(meal_cals, 1), round(meal_prot, 1), round(meal_carbs, 1),
            round(meal_fat, 1), round(meal_fiber, 1), meal_id
        ))

        total_plan_cals += meal_cals
        total_plan_prot += meal_prot
        total_plan_carbs += meal_carbs
        total_plan_fat += meal_fat
        total_plan_fiber += meal_fiber

    cursor.execute("""
        UPDATE meal_plans
        SET total_calories = ?, total_protein = ?, total_carbs = ?, total_fat = ?, total_fiber = ?
        WHERE id = ?
    """, (
        round(total_plan_cals, 1), round(total_plan_prot, 1),
        round(total_plan_carbs, 1), round(total_plan_fat, 1),
        round(total_plan_fiber, 1), meal_plan_id
    ))

    cursor.execute("""
        INSERT OR IGNORE INTO daily_progress (
            id, user_id, date, meals_completed, meals_total,
            water_consumed_ml, water_target_ml, protein_consumed_g,
            protein_target_g, fiber_consumed_g, fiber_target_g,
            calories_consumed, calories_target, adherence_score, summary_notes
        ) VALUES (?, ?, ?, 0, 5, 0.0, 2750.0, 0.0, ?, 0.0, ?, 0.0, ?, 0.0, 'Initial daily plan generated.')
    """, (
        str(uuid.uuid4()), DEFAULT_USER_ID, today_str,
        round(total_plan_prot, 1), round(total_plan_fiber, 1), round(total_plan_cals, 1)
    ))

def seed_all():
    init_database()
    with get_db_connection() as conn:
        seed_foods(conn)
        seed_default_user_and_profile(conn)
        seed_today_meal_plan(conn)
    print("Database initialization and seeding completed successfully.")

if __name__ == "__main__":
    seed_all()
