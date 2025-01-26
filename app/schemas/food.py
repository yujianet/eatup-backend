from datetime import datetime

from pydantic import BaseModel, field_validator


class FoodCreate(BaseModel):
    name: str
    category_large: str
    category_small: str
    expiry_days: int
    photo_path: str


class FoodResponse(FoodCreate):
    id: int
    storage_time: datetime
    remaining_days: int


class FoodQueryParams(BaseModel):
    page: int = 1
    page_size: int = 10
    sort_by: str = "storage_time"
    order: str = "desc"

    @classmethod
    @field_validator('page_size')
    def validate_page_size(cls, v: int) -> int:
        if v > 100:
            raise ValueError("每页最多100条")
        return v
