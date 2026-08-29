from pydantic import BaseModel, Field
from typing import Optional, List

class WaterLogCreate(BaseModel):
    amount_ml: float = Field(..., gt=0, le=3000, json_schema_extra={"example": 250.0})
    source: Optional[str] = "quick_button"

class WaterLogItem(BaseModel):
    id: str
    amount_ml: float
    date: str
    timestamp: str
    source: str

class HydrationSummaryResponse(BaseModel):
    date: str
    consumed_ml: float
    target_ml: float
    remaining_ml: float
    percentage: float
    logs: List[WaterLogItem] = Field(default_factory=list)
