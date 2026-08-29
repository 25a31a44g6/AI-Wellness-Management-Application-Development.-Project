from fastapi import APIRouter, HTTPException
from datetime import date, datetime
import uuid
from backend.database.database import get_db_connection
from backend.database.seed import DEFAULT_USER_ID
from backend.schemas.water_schema import WaterLogCreate, HydrationSummaryResponse, WaterLogItem
from backend.api.meal_routes import recalculate_daily_progress

router = APIRouter(prefix="/api/hydration", tags=["hydration"])

@router.get("/today", response_model=HydrationSummaryResponse)
def get_today_hydration():
    today_str = date.today().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get target from profile
        cursor.execute("SELECT target_water_ml FROM profiles WHERE user_id = ?", (DEFAULT_USER_ID,))
        profile_row = cursor.fetchone()
        target_ml = profile_row["target_water_ml"] if profile_row else 2500.0
        
        # Get logs
        cursor.execute("""
            SELECT * FROM water_logs 
            WHERE user_id = ? AND date = ? 
            ORDER BY timestamp DESC
        """, (DEFAULT_USER_ID, today_str))
        rows = cursor.fetchall()
        
        logs = [
            WaterLogItem(
                id=r["id"],
                amount_ml=r["amount_ml"],
                date=r["date"],
                timestamp=r["timestamp"],
                source=r["source"] or "quick_button"
            ) for r in rows
        ]
        
        consumed_ml = sum(l.amount_ml for l in logs)
        remaining_ml = max(0.0, target_ml - consumed_ml)
        percentage = round((consumed_ml / target_ml * 100.0), 1) if target_ml > 0 else 0.0
        
        return HydrationSummaryResponse(
            date=today_str,
            consumed_ml=round(consumed_ml, 1),
            target_ml=round(target_ml, 1),
            remaining_ml=round(remaining_ml, 1),
            percentage=min(100.0, percentage),
            logs=logs
        )

@router.post("/log")
def log_water(entry: WaterLogCreate):
    today_str = date.today().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        log_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO water_logs (id, user_id, amount_ml, date, timestamp, source)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (log_id, DEFAULT_USER_ID, entry.amount_ml, today_str, entry.source))
        
        recalculate_daily_progress(conn, DEFAULT_USER_ID, today_str)
        return {"status": "success", "log_id": log_id, "amount_ml": entry.amount_ml}

@router.delete("/{log_id}")
def delete_water_log(log_id: str):
    today_str = date.today().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM water_logs WHERE id = ? AND user_id = ?", (log_id, DEFAULT_USER_ID))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Water entry not found")
            
        recalculate_daily_progress(conn, DEFAULT_USER_ID, today_str)
        return {"status": "success", "message": "Water entry deleted"}
