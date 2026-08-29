from pydantic import BaseModel, Field
from typing import Optional, List

class MealItemSchema(BaseModel):
    id: Optional[str] = None
    food_id: str
    food_name: str
    raw_quantity: float
    cooked_quantity: Optional[float] = None
    unit: str = "g"
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    substitution_for: Optional[str] = None

class MealSchema(BaseModel):
    id: str
    meal_plan_id: str
    meal_type: str
    name: str
    scheduled_time: str
    status: str = "pending"
    completed_at: Optional[str] = None
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    prep_notes: Optional[str] = None
    items: List[MealItemSchema] = Field(default_factory=list)

class MealPlanResponse(BaseModel):
    id: str
    user_id: str
    date: str
    status: str
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    total_fiber: float
    notes: Optional[str] = None
    meals: List[MealSchema] = Field(default_factory=list)

class MealActionRequest(BaseModel):
    notes: Optional[str] = None
