from datetime import datetime
from pydantic import BaseModel, field_validator, Field

class FoodCreate(BaseModel):
    food_name: str = Field(..., description="食物名称")
    expiry_days: int
    photo_path: str

class FoodResponse(FoodCreate):
    food_id: int
    storage_time: datetime
    remaining_days: int
    remaining_level: int

class FoodQueryParams(BaseModel):
    offset: int = 0  # 新增字段
    limit: int = 10  # 新增字段
    sort_by: str = "storage_time"
    order: str = "desc"
    include_deleted: bool = False  # 新增字段

    @classmethod
    @field_validator('limit')
    def validate_limit(cls, v: int) -> int:
        if v > 100:
            raise ValueError("每页最多100条")
        return v