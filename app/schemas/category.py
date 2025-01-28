from pydantic import BaseModel, field_validator


class CategoriesResponse(BaseModel):
    categories: dict[str, dict[str, int]]  # 两级字典结构
    # 结构示例：
    # {
    #   "蔬菜": {"叶菜": 3, "根茎": 7},
    #   "水果": {"浆果": 5, "柑橘": 10}
    # }


class CategoryUpsertRequest(BaseModel):
    large_category: str
    small_category: str
    expiry_days: int

    @classmethod
    @field_validator('expiry_days')
    def validate_expiry_days(cls, v):
        if v <= 0:
            raise ValueError("保质期必须为正整数")
        return v
