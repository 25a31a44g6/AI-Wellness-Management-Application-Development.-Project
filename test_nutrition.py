import pytest
from backend.services.nutrition_service import (
    calculate_calories,
    calculate_protein,
    calculate_carbs,
    calculate_fat,
    calculate_fiber,
    calculate_food_nutrition,
    calculate_daily_estimated_targets
)

def test_deterministic_macro_calculations():
    # 50g of oats with 16.9g protein per 100g -> 8.45g rounded to 8.5g (or 8.45)
    protein = calculate_protein(16.9, 50.0)
    assert protein == 8.4 or protein == 8.5
    
    # 50g of oats with 10.6g fiber per 100g -> 5.3g
    fiber = calculate_fiber(10.6, 50.0)
    assert fiber == 5.3
    
    # 50g of oats with 389.0 kcal per 100g -> 194.5 kcal
    cals = calculate_calories(389.0, 50.0)
    assert cals == 194.5

def test_food_nutrition_breakdown():
    mock_food = {
        "food_id": "food_001",
        "name": "Rolled Oats",
        "category": "Grains",
        "standard_unit": "g",
        "raw_weight_unit_g": 1.0,
        "edible_weight_ratio": 1.0,
        "calories_per_100g": 389.0,
        "protein_per_100g": 16.9,
        "carbohydrates_per_100g": 66.3,
        "fat_per_100g": 6.9,
        "fiber_per_100g": 10.6,
        "prep_type": "raw"
    }
    
    result = calculate_food_nutrition(mock_food, 50.0, "g")
    assert result["food_id"] == "food_001"
    assert result["raw_weight_g"] == 50.0
    assert result["cooked_weight_g"] == 110.0  # 50 * 2.2 absorption
    assert result["nutrition"]["calories"] == 194.5
    assert result["nutrition"]["fiber"] == 5.3

def test_daily_estimated_targets():
    targets = calculate_daily_estimated_targets(
        weight_kg=70.0,
        height_cm=175.0,
        age=25,
        gender="Other",
        activity_level="Moderately Active"
    )
    assert targets["target_calories"] > 1800
    assert targets["target_protein_g"] >= 70.0
    assert targets["target_fiber_g"] >= 25.0
    assert targets["target_water_ml"] >= 2000.0
