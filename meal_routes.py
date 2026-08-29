from fastapi import APIRouter, HTTPException, Body
from datetime import date, datetime
import uuid
from typing import Optional, Dict, Any, List
from backend.database.database import get_db_connection
from backend.database.seed import DEFAULT_USER_ID, seed_today_meal_plan
from backend.schemas.meal_schema import MealPlanResponse, MealSchema, MealItemSchema, MealActionRequest
from backend.services.nutrition_service import calculate_food_nutrition

router = APIRouter(prefix="/api/meals", tags=["meals"])

def recalculate_daily_progress(conn, user_id: str, date_str: str):
    """Internal helper to synchronize daily_progress totals with completed meals and water."""
    cursor = conn.cursor()
    # Sum completed meals nutrition
    cursor.execute("""
        SELECT 
            COUNT(*) as total_meals,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
            SUM(CASE WHEN status = 'completed' THEN calories ELSE 0 END) as sum_cals,
            SUM(CASE WHEN status = 'completed' THEN protein ELSE 0 END) as sum_protein,
            SUM(CASE WHEN status = 'completed' THEN fiber ELSE 0 END) as sum_fiber
        FROM meals 
        WHERE user_id = ? AND meal_plan_id IN (
            SELECT id FROM meal_plans WHERE user_id = ? AND date = ?
        )
    """, (user_id, user_id, date_str))
    
    meal_stats = cursor.fetchone()
    total_meals = meal_stats["total_meals"] or 0
    completed_meals = meal_stats["completed_count"] or 0
    cals_consumed = round(meal_stats["sum_cals"] or 0.0, 1)
    protein_consumed = round(meal_stats["sum_protein"] or 0.0, 1)
    fiber_consumed = round(meal_stats["sum_fiber"] or 0.0, 1)
    
    # Calculate water consumed
    cursor.execute("SELECT SUM(amount_ml) FROM water_logs WHERE user_id = ? AND date = ?", (user_id, date_str))
    water_row = cursor.fetchone()
    water_consumed = round(water_row[0] or 0.0, 1)
    
    # Calculate adherence score
    adherence = 0.0
    if total_meals > 0:
        adherence = round((completed_meals / total_meals) * 100.0, 1)
        
    cursor.execute("""
        UPDATE daily_progress SET
            meals_completed = ?,
            meals_total = ?,
            calories_consumed = ?,
            protein_consumed_g = ?,
            fiber_consumed_g = ?,
            water_consumed_ml = ?,
            adherence_score = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND date = ?
    """, (
        completed_meals, total_meals, cals_consumed, protein_consumed,
        fiber_consumed, water_consumed, adherence, user_id, date_str
    ))

@router.get("/today", response_model=MealPlanResponse)
def get_today_meal_plan():
    today_str = date.today().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        seed_today_meal_plan(conn)  # Ensure exists
        
        cursor.execute("SELECT * FROM meal_plans WHERE user_id = ? AND date = ? ORDER BY created_at DESC LIMIT 1", (DEFAULT_USER_ID, today_str))
        plan_row = cursor.fetchone()
        if not plan_row:
            raise HTTPException(status_code=404, detail="No meal plan found for today")
            
        plan_data = dict(plan_row)
        
        # Fetch meals
        cursor.execute("SELECT * FROM meals WHERE meal_plan_id = ? ORDER BY scheduled_time ASC", (plan_data["id"],))
        meal_rows = cursor.fetchall()
        
        meals_list = []
        for m in meal_rows:
            m_dict = dict(m)
            # Fetch items
            cursor.execute("SELECT * FROM meal_items WHERE meal_id = ?", (m_dict["id"],))
            item_rows = cursor.fetchall()
            m_dict["items"] = [dict(item) for item in item_rows]
            meals_list.append(m_dict)
            
        plan_data["meals"] = meals_list
        return plan_data

@router.post("/{meal_id}/complete")
def complete_meal(meal_id: str, action: MealActionRequest = None):
    today_str = date.today().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meals WHERE id = ?", (meal_id,))
        meal = cursor.fetchone()
        if not meal:
            raise HTTPException(status_code=404, detail="Meal not found")
            
        new_status = "completed" if meal["status"] != "completed" else "pending"
        completed_at = datetime.now().isoformat() if new_status == "completed" else None
        
        cursor.execute("UPDATE meals SET status = ?, completed_at = ? WHERE id = ?", (new_status, completed_at, meal_id))
        
        # Log event
        cursor.execute("""
            INSERT INTO meal_logs (id, user_id, meal_id, date, status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), DEFAULT_USER_ID, meal_id, today_str, new_status, action.notes if action else "Toggled status"))
        
        recalculate_daily_progress(conn, DEFAULT_USER_ID, today_str)
        return {"status": "success", "meal_id": meal_id, "new_status": new_status}

@router.post("/{meal_id}/skip")
def skip_meal(meal_id: str, action: MealActionRequest = None):
    today_str = date.today().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meals WHERE id = ?", (meal_id,))
        meal = cursor.fetchone()
        if not meal:
            raise HTTPException(status_code=404, detail="Meal not found")
            
        cursor.execute("UPDATE meals SET status = 'skipped', completed_at = NULL WHERE id = ?", (meal_id,))
        
        # Log event
        cursor.execute("""
            INSERT INTO meal_logs (id, user_id, meal_id, date, status, notes)
            VALUES (?, ?, ?, ?, 'skipped', ?)
        """, (str(uuid.uuid4()), DEFAULT_USER_ID, meal_id, today_str, action.notes if action else "Marked skipped by user"))
        
        # Add agent event log for adaptive triggering
        cursor.execute("""
            INSERT INTO agent_events (id, user_id, event_type, agent_name, details)
            VALUES (?, ?, 'meal_skipped', 'MealAgent', ?)
        """, (str(uuid.uuid4()), DEFAULT_USER_ID, f"User skipped meal: {meal['name']} ({meal['meal_type']})"))
        
        recalculate_daily_progress(conn, DEFAULT_USER_ID, today_str)
        return {"status": "success", "meal_id": meal_id, "message": "Meal marked as skipped"}

@router.post("/{meal_id}/substitute")
def substitute_meal_item(
    meal_id: str,
    original_food_id: str = Body(..., embed=True),
    substitute_food_id: str = Body(..., embed=True),
    substitute_quantity: float = Body(..., embed=True),
    reason: Optional[str] = Body("User preference / ingredient unavailable", embed=True)
):
    today_str = date.today().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check meal and item
        cursor.execute("SELECT * FROM meals WHERE id = ?", (meal_id,))
        meal = cursor.fetchone()
        if not meal:
            raise HTTPException(status_code=404, detail="Meal not found")
            
        cursor.execute("SELECT * FROM meal_items WHERE meal_id = ? AND food_id = ?", (meal_id, original_food_id))
        item = cursor.fetchone()
        if not item:
            raise HTTPException(status_code=404, detail="Original food item not found in this meal")
            
        cursor.execute("SELECT * FROM foods WHERE food_id = ?", (substitute_food_id,))
        new_food = cursor.fetchone()
        if not new_food:
            raise HTTPException(status_code=404, detail="Substitute food not found in database")
            
        new_food_dict = dict(new_food)
        calc_result = calculate_food_nutrition(new_food_dict, substitute_quantity, new_food_dict.get("standard_unit", "g"))
        nutr = calc_result["nutrition"]
        
        # Update meal_item
        cursor.execute("""
            UPDATE meal_items SET
                food_id = ?,
                food_name = ?,
                raw_quantity = ?,
                cooked_quantity = ?,
                unit = ?,
                calories = ?,
                protein = ?,
                carbs = ?,
                fat = ?,
                fiber = ?,
                substitution_for = ?
            WHERE id = ?
        """, (
            new_food_dict["food_id"], new_food_dict["name"], substitute_quantity,
            calc_result["cooked_weight_g"], calc_result["unit"],
            nutr["calories"], nutr["protein"], nutr["carbohydrates"],
            nutr["fat"], nutr["fiber"], item["food_name"], item["id"]
        ))
        
        # Re-sum all items for this meal
        cursor.execute("""
            SELECT SUM(calories) as c, SUM(protein) as p, SUM(carbs) as cb, SUM(fat) as f, SUM(fiber) as fb
            FROM meal_items WHERE meal_id = ?
        """, (meal_id,))
        meal_sums = cursor.fetchone()
        
        cursor.execute("""
            UPDATE meals SET
                calories = ?, protein = ?, carbs = ?, fat = ?, fiber = ?
                WHERE id = ?
        """, (
            round(meal_sums["c"] or 0, 1), round(meal_sums["p"] or 0, 1),
            round(meal_sums["cb"] or 0, 1), round(meal_sums["f"] or 0, 1),
            round(meal_sums["fb"] or 0, 1), meal_id
        ))
        
        # Re-sum whole meal plan
        cursor.execute("""
            SELECT SUM(calories) as c, SUM(protein) as p, SUM(carbs) as cb, SUM(fat) as f, SUM(fiber) as fb
            FROM meals WHERE meal_plan_id = ?
        """, (meal["meal_plan_id"],))
        plan_sums = cursor.fetchone()
        
        cursor.execute("""
            UPDATE meal_plans SET
                total_calories = ?, total_protein = ?, total_carbs = ?, total_fat = ?, total_fiber = ?
            WHERE id = ?
        """, (
            round(plan_sums["c"] or 0, 1), round(plan_sums["p"] or 0, 1),
            round(plan_sums["cb"] or 0, 1), round(plan_sums["f"] or 0, 1),
            round(plan_sums["fb"] or 0, 1), meal["meal_plan_id"]
        ))
        
        # Record substitution history
        cursor.execute("""
            INSERT INTO substitutions (
                id, meal_id, original_food_id, original_food_name,
                substituted_food_id, substituted_food_name, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), meal_id, original_food_id, item["food_name"],
            new_food_dict["food_id"], new_food_dict["name"], reason
        ))
        
        recalculate_daily_progress(conn, DEFAULT_USER_ID, today_str)
        return {
            "status": "success",
            "message": f"Successfully substituted {item['food_name']} with {new_food_dict['name']}",
            "meal_id": meal_id,
            "new_nutrition": nutr
        }
