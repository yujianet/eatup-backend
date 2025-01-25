from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..models import Food
from ..database import get_db

router = APIRouter(prefix="/foods", tags=["foods"])

# 创建食物
@router.post("/")
def create_food(name: str, category_large: str, category_small: str,
                expiry_days: int, db: Session = Depends(get_db)):
    db_food = Food(
        name=name,
        category_large=category_large,
        category_small=category_small,
        expiry_days=expiry_days,
        photo_path="temp_path"  # 后续替换为实际路径
    )
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food

# 获取食物列表
@router.get("/")
def get_foods(db: Session = Depends(get_db)):
    return db.query(Food).all()