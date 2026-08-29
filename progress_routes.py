from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
from typing import Dict, Any, List
from backend.database.database import get_db_connection
from backend.database.seed import DEFAULT_USER_ID

router = APIRouter(prefix="/api/progress", tags=["progress"])

@router.get("/today")
def get_today_progress():
    today_str = date.today().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM daily_progress WHERE user_id = ? AND date = ?", (DEFAULT_USER_ID, today_str))
        prog = cursor.fetchone()
        
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (DEFAULT_USER_ID,))
        prof = cursor.fetchone()
        
        # Get meal-by-meal macro breakdown
        cursor.execute("""
            SELECT m.id, m.name, m.meal_type, m.scheduled_time, m.status,
                   m.calories, m.protein, m.fiber, m.carbs, m.fat
            FROM meals m
            JOIN meal_plans mp ON m.meal_plan_id = mp.id
            WHERE m.user_id = ? AND mp.date = ?
            ORDER BY m.scheduled_time ASC
        """, (DEFAULT_USER_ID, today_str))
        meal_rows = cursor.fetchall()
        
        meals_breakdown = [dict(m) for m in meal_rows]
        
        # Planned vs Consumed
        planned_protein = sum(m["protein"] for m in meals_breakdown)
        planned_fiber = sum(m["fiber"] for m in meals_breakdown)
        planned_calories = sum(m["calories"] for m in meals_breakdown)
        
        consumed_protein = sum(m["protein"] for m in meals_breakdown if m["status"] == "completed")
        consumed_fiber = sum(m["fiber"] for m in meals_breakdown if m["status"] == "completed")
        consumed_calories = sum(m["calories"] for m in meals_breakdown if m["status"] == "completed")
        
        # Water
        cursor.execute("SELECT SUM(amount_ml) FROM water_logs WHERE user_id = ? AND date = ?", (DEFAULT_USER_ID, today_str))
        water_val = cursor.fetchone()[0] or 0.0
        water_target = prof["target_water_ml"] if prof else 2500.0
        
        return {
            "date": today_str,
            "user_name": prof["name"] if prof else "Alex Morgan",
            "summary": {
                "meals_total": len(meals_breakdown),
                "meals_completed": sum(1 for m in meals_breakdown if m["status"] == "completed"),
                "meals_skipped": sum(1 for m in meals_breakdown if m["status"] == "skipped"),
                "adherence_score": round((sum(1 for m in meals_breakdown if m["status"] == "completed") / max(1, len(meals_breakdown))) * 100, 1),
                "protein": {
                    "consumed_g": round(consumed_protein, 1),
                    "planned_g": round(planned_protein, 1),
                    "target_g": round(prof["target_protein_g"] if prof else 75.0, 1),
                    "remaining_g": max(0.0, round((prof["target_protein_g"] if prof else 75.0) - consumed_protein, 1))
                },
                "fiber": {
                    "consumed_g": round(consumed_fiber, 1),
                    "planned_g": round(planned_fiber, 1),
                    "target_g": round(prof["target_fiber_g"] if prof else 30.0, 1),
                    "remaining_g": max(0.0, round((prof["target_fiber_g"] if prof else 30.0) - consumed_fiber, 1))
                },
                "calories": {
                    "consumed": round(consumed_calories, 1),
                    "planned": round(planned_calories, 1),
                    "target": round(prof["target_calories"] if prof else 2000.0, 1)
                },
                "water": {
                    "consumed_ml": round(water_val, 1),
                    "target_ml": round(water_target, 1),
                    "percentage": min(100.0, round((water_val / water_target) * 100, 1)) if water_target > 0 else 0
                }
            },
            "meals_breakdown": meals_breakdown
        }

@router.get("/weekly")
def get_weekly_progress():
    today = date.today()
    days_data = []
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for i in range(6, -1, -1):
            day_str = (today - timedelta(days=i)).isoformat()
            
            cursor.execute("SELECT * FROM daily_progress WHERE user_id = ? AND date = ?", (DEFAULT_USER_ID, day_str))
            row = cursor.fetchone()
            
            if row:
                days_data.append({
                    "date": day_str,
                    "day_name": (today - timedelta(days=i)).strftime("%a"),
                    "completed_meals": row["meals_completed"],
                    "total_meals": row["meals_total"],
                    "water_ml": row["water_consumed_ml"],
                    "protein_g": row["protein_consumed_g"],
                    "fiber_g": row["fiber_consumed_g"],
                    "adherence": row["adherence_score"]
                })
            else:
                # Simulated historical baseline for visual graphs if fresh install
                days_data.append({
                    "date": day_str,
                    "day_name": (today - timedelta(days=i)).strftime("%a"),
                    "completed_meals": 4 if i > 0 else 0,
                    "total_meals": 5,
                    "water_ml": 2250.0 if i > 0 else 0.0,
                    "protein_g": 78.0 if i > 0 else 0.0,
                    "fiber_g": 28.0 if i > 0 else 0.0,
                    "adherence": 80.0 if i > 0 else 0.0
                })
                
        # Aggregate stats
        avg_adherence = round(sum(d["adherence"] for d in days_data) / len(days_data), 1)
        avg_water = round(sum(d["water_ml"] for d in days_data) / len(days_data), 0)
        avg_protein = round(sum(d["protein_g"] for d in days_data) / len(days_data), 1)
        avg_fiber = round(sum(d["fiber_g"] for d in days_data) / len(days_data), 1)
        
        cursor.execute("SELECT COUNT(*) FROM substitutions WHERE meal_id IN (SELECT id FROM meals WHERE user_id = ?)", (DEFAULT_USER_ID,))
        sub_count = cursor.fetchone()[0]
        
        return {
            "days": days_data,
            "weekly_averages": {
                "adherence": avg_adherence,
                "water_ml": avg_water,
                "protein_g": avg_protein,
                "fiber_g": avg_fiber,
                "substitutions_used": sub_count
            }
        }
