from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.database.database import get_db_connection
from backend.schemas.nutrition_schema import FoodItemBase, QuantityCalculationRequest, QuantityCalculationResponse
from backend.services.nutrition_service import calculate_food_nutrition

router = APIRouter(prefix="/api/foods", tags=["foods"])

@router.get("", response_model=List[FoodItemBase])
def search_foods(
    query: Optional[str] = Query(None, description="Search by food name or category"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sql = "SELECT * FROM foods WHERE 1=1"
        params = []
        
        if query:
            sql += " AND (name LIKE ? OR category LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        if category:
            sql += " AND category = ?"
            params.append(category)
            
        sql += " ORDER BY category, name LIMIT 50"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@router.get("/{food_id}", response_model=FoodItemBase)
def get_food_by_id(food_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM foods WHERE food_id = ?", (food_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Food item not found")
        return dict(row)

@router.post("/calculate", response_model=QuantityCalculationResponse)
def calculate_portion(req: QuantityCalculationRequest):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM foods WHERE food_id = ?", (req.food_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Food item not found")
        
        food_dict = dict(row)
        res = calculate_food_nutrition(food_dict, req.quantity, req.unit or "g")
        return res
