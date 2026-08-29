from fastapi import APIRouter, HTTPException, Depends
import json
import sqlite3
from typing import Dict, Any
from backend.database.database import get_db_connection
from backend.database.seed import DEFAULT_USER_ID
from backend.schemas.user_schema import UserProfileBase, UserProfileResponse
from backend.services.nutrition_service import calculate_daily_estimated_targets

router = APIRouter(prefix="/api/profile", tags=["profile"])

@router.get("", response_model=UserProfileResponse)
def get_profile():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (DEFAULT_USER_ID,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        data = dict(row)
        data["allergies"] = json.loads(data["allergies"] or "[]")
        data["disliked_foods"] = json.loads(data["disliked_foods"] or "[]")
        data["favorite_foods"] = json.loads(data["favorite_foods"] or "[]")
        data["preferred_meal_times"] = json.loads(data["preferred_meal_times"] or "{}")
        return data

@router.put("", response_model=UserProfileResponse)
def update_profile(profile_in: UserProfileBase):
    targets = calculate_daily_estimated_targets(
        weight_kg=profile_in.weight_kg,
        height_cm=profile_in.height_cm,
        age=profile_in.age,
        gender=profile_in.gender,
        activity_level=profile_in.activity_level
    )
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE profiles SET
                name = ?, age = ?, gender = ?, height_cm = ?, weight_kg = ?,
                activity_level = ?, dietary_pref = ?, allergies = ?,
                disliked_foods = ?, favorite_foods = ?, wake_time = ?, sleep_time = ?,
                work_start = ?, work_end = ?, exercise_time = ?, preferred_meal_times = ?,
                cooking_facility = ?, food_availability = ?, target_calories = ?,
                target_protein_g = ?, target_fiber_g = ?, target_water_ml = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (
            profile_in.name, profile_in.age, profile_in.gender, profile_in.height_cm,
            profile_in.weight_kg, profile_in.activity_level, profile_in.dietary_pref,
            json.dumps(profile_in.allergies), json.dumps(profile_in.disliked_foods),
            json.dumps(profile_in.favorite_foods), profile_in.wake_time, profile_in.sleep_time,
            profile_in.work_start, profile_in.work_end, profile_in.exercise_time,
            json.dumps(profile_in.preferred_meal_times), profile_in.cooking_facility,
            profile_in.food_availability, targets["target_calories"], targets["target_protein_g"],
            targets["target_fiber_g"], targets["target_water_ml"], DEFAULT_USER_ID
        ))
        
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (DEFAULT_USER_ID,))
        row = cursor.fetchone()
        data = dict(row)
        data["allergies"] = json.loads(data["allergies"] or "[]")
        data["disliked_foods"] = json.loads(data["disliked_foods"] or "[]")
        data["favorite_foods"] = json.loads(data["favorite_foods"] or "[]")
        data["preferred_meal_times"] = json.loads(data["preferred_meal_times"] or "{}")
        return data
