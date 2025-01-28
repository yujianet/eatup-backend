from datetime import datetime
from pydantic import BaseModel, field_validator, Field
from sqlalchemy.orm import Session


class FoodCreate(BaseModel):
    name: str = Field(..., description="食物名称")
    category_large: str = Field(..., examples=["蔬菜"], description="大分类名称")
    category_small: str = Field(..., examples=["叶菜"], description="小分类名称")
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
    include_deleted: bool = False  # 新增字段

    @classmethod
    @field_validator('page_size')
    def validate_page_size(cls, v: int) -> int:
        if v > 100:
            raise ValueError("每页最多100条")
        return v