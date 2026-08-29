from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class UserProfileBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Alex Morgan"})
    age: int = Field(26, ge=10, le=120)
    gender: Optional[str] = "Other"
    height_cm: float = Field(175.0, ge=80.0, le=250.0)
    weight_kg: float = Field(68.0, ge=30.0, le=300.0)
    activity_level: str = Field("Moderately Active", json_schema_extra={"example": "Sedentary, Lightly Active, Moderately Active, Very Active"})
    dietary_pref: str = Field("Flexitarian", json_schema_extra={"example": "Vegetarian, Vegan, Non-Vegetarian, Flexitarian, Eggetarian"})
    allergies: List[str] = Field(default_factory=list)
    disliked_foods: List[str] = Field(default_factory=list)
    favorite_foods: List[str] = Field(default_factory=list)
    wake_time: str = "06:30"
    sleep_time: str = "22:30"
    work_start: str = "09:00"
    work_end: str = "17:00"
    exercise_time: Optional[str] = "18:00"
    preferred_meal_times: Dict[str, str] = Field(default_factory=lambda: {
        "breakfast": "08:00",
        "morning_snack": "11:00",
        "lunch": "13:30",
        "evening_snack": "17:00",
        "dinner": "20:00"
    })
    cooking_facility: str = "Full Kitchen"
    food_availability: str = "Standard Groceries"

class UserProfileResponse(UserProfileBase):
    id: str
    user_id: str
    target_calories: float
    target_protein_g: float
    target_fiber_g: float
    target_water_ml: float
