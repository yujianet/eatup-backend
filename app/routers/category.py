from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Category
from ..schemas.category import CategoriesResponse, CategoryUpsertRequest

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoriesResponse)
def get_categories(db: Session = Depends(get_db)):
    """获取所有分类（按大分类分组）"""
    all_categories = db.query(Category).all()

    # 构建两级字典结构
    response_data = {}
    for cat in all_categories:
        if cat.large_category not in response_data:
            response_data[cat.large_category] = {}
        response_data[cat.large_category][cat.small_category] = cat.expiry_days

    return {"categories": response_data}


@router.post("/upsert")
def upsert_category(
        request: CategoryUpsertRequest,
        db: Session = Depends(get_db)
):
    """创建或更新分类"""
    # 查找是否已存在相同分类
    category = db.query(Category).filter(
        Category.large_category == request.large_category,
        Category.small_category == request.small_category
    ).first()

    if category:
        # 更新现有分类的保质期
        category.expiry_days = request.expiry_days
    else:
        # 创建新分类
        category = Category(
            large_category=request.large_category,
            small_category=request.small_category,
            expiry_days=request.expiry_days
        )
        db.add(category)

    db.commit()
    return {"message": "分类更新成功"}