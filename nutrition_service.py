from typing import Dict, Any, List, Optional

def calculate_calories(calories_per_100g: float, weight_in_grams: float) -> float:
    """Calculates calories based on raw edible weight in grams."""
    return round((calories_per_100g * weight_in_grams) / 100.0, 1)

def calculate_protein(protein_per_100g: float, weight_in_grams: float) -> float:
    """Calculates protein grams based on raw edible weight in grams."""
    return round((protein_per_100g * weight_in_grams) / 100.0, 1)

def calculate_carbs(carbs_per_100g: float, weight_in_grams: float) -> float:
    """Calculates carbohydrates grams based on raw edible weight in grams."""
    return round((carbs_per_100g * weight_in_grams) / 100.0, 1)

def calculate_fat(fat_per_100g: float, weight_in_grams: float) -> float:
    """Calculates fat grams based on raw edible weight in grams."""
    return round((fat_per_100g * weight_in_grams) / 100.0, 1)

def calculate_fiber(fiber_per_100g: float, weight_in_grams: float) -> float:
    """Calculates fiber grams based on raw edible weight in grams."""
    return round((fiber_per_100g * weight_in_grams) / 100.0, 1)

def calculate_food_nutrition(food: Dict[str, Any], quantity: float, unit: str = "g") -> Dict[str, Any]:
    """
    Deterministically computes complete macro & micro breakdown for given food item and quantity.
    Handles units: 'g', 'ml', 'piece', 'scoop'.
    """
    raw_unit_weight = float(food.get("raw_weight_unit_g", 1.0))
    edible_ratio = float(food.get("edible_weight_ratio", 1.0))
    standard_unit = food.get("standard_unit", "g")
    
    # If quantity is specified in grams directly, unit weight is 1.0g
    if unit.lower() == "g":
        effective_weight_g = quantity
    elif unit.lower() in ["piece", "scoop", "item", "slice"]:
        effective_weight_g = quantity * raw_unit_weight
    elif unit.lower() == "ml":
        effective_weight_g = quantity * raw_unit_weight  # density adjusted (e.g. 1.03 for milk)
    else:
        effective_weight_g = quantity
        
    raw_edible_grams = effective_weight_g * edible_ratio
    
    calories = calculate_calories(float(food["calories_per_100g"]), raw_edible_grams)
    protein = calculate_protein(float(food["protein_per_100g"]), raw_edible_grams)
    carbs = calculate_carbs(float(food["carbohydrates_per_100g"]), raw_edible_grams)
    fat = calculate_fat(float(food["fat_per_100g"]), raw_edible_grams)
    fiber = calculate_fiber(float(food["fiber_per_100g"]), raw_edible_grams)
    
    prep_type = food.get("prep_type", "raw")
    cooked_weight = None
    if prep_type == "raw":
        category = food.get("category", "")
        if category in ["Grains", "Pulses"]:
            cooked_weight = round(effective_weight_g * 2.2, 1)  # standard water absorption factor
        elif category in ["Poultry", "Seafood"]:
            cooked_weight = round(effective_weight_g * 0.8, 1)  # moisture loss
        else:
            cooked_weight = round(effective_weight_g, 1)
    else:
        cooked_weight = round(effective_weight_g, 1)
            
    return {
        "food_id": food["food_id"],
        "food_name": food["name"],
        "raw_quantity": quantity,
        "unit": unit,
        "raw_weight_g": round(effective_weight_g, 1),
        "edible_weight_g": round(raw_edible_grams, 1),
        "cooked_weight_g": cooked_weight,
        "nutrition": {
            "calories": calories,
            "protein": protein,
            "carbohydrates": carbs,
            "fat": fat,
            "fiber": fiber
        }
    }

def calculate_daily_estimated_targets(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: Optional[str] = "Other",
    activity_level: str = "Moderately Active"
) -> Dict[str, float]:
    """
    Computes evidence-based daily wellness targets using standard BMR (Mifflin-St Jeor)
    and empirical protein/fiber/water distribution benchmarks.
    """
    if gender and gender.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    elif gender and gender.lower() == "female":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 78

    activity_multipliers = {
        "sedentary": 1.2,
        "lightly active": 1.375,
        "moderately active": 1.55,
        "very active": 1.725,
        "extra active": 1.9
    }
    
    mult = activity_multipliers.get(activity_level.lower(), 1.4)
    target_calories = round(bmr * mult, 0)
    
    target_protein = round(weight_kg * (1.4 if "active" in activity_level.lower() else 1.1), 1)
    target_fiber = round(min(38.0, max(25.0, (target_calories / 1000.0) * 14.0)), 1)
    target_water_ml = round(min(4000.0, max(2000.0, weight_kg * 35.0 + 350.0)), 0)
    
    return {
        "target_calories": target_calories,
        "target_protein_g": target_protein,
        "target_fiber_g": target_fiber,
        "target_water_ml": target_water_ml
    }
