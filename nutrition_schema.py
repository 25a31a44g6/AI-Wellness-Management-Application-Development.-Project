from pydantic import BaseModel, Field
from typing import Optional, List

class FoodItemBase(BaseModel):
    food_id: str
    name: str
    category: str
    standard_unit: str = "g"
    raw_weight_unit_g: float = 1.0
    edible_weight_ratio: float = 1.0
    calories_per_100g: float
    protein_per_100g: float
    carbohydrates_per_100g: float
    fat_per_100g: float
    fiber_per_100g: float
    serving_desc: Optional[str] = None
    prep_type: str = "raw"
    allergens: str = "none"

class NutritionBreakdown(BaseModel):
    calories: float = Field(..., description="Energy in kcal")
    protein: float = Field(..., description="Protein in grams")
    carbohydrates: float = Field(..., description="Carbohydrates in grams")
    fat: float = Field(..., description="Fat in grams")
    fiber: float = Field(..., description="Dietary fiber in grams")

class QuantityCalculationRequest(BaseModel):
    food_id: str
    quantity: float
    unit: Optional[str] = "g"

class QuantityCalculationResponse(BaseModel):
    food_id: str
    food_name: str
    raw_quantity: float
    unit: str
    raw_weight_g: float
    cooked_weight_g: Optional[float] = None
    nutrition: NutritionBreakdown
