from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from ..models import Food, Category
from ..database import get_db
import shutil
from datetime import datetime, timedelta
from ..schemas.food import FoodResponse, FoodCreate, FoodQueryParams

router = APIRouter(prefix="/foods", tags=["foods"])


@router.post("/", status_code=201)
def create_food(
        food_data: FoodCreate,
        db: Session = Depends(get_db)
):
    """创建食物"""
    # 验证分类是否存在
    category = db.query(Category).filter(
        Category.large_category == food_data.category_large,
        Category.small_category == food_data.category_small
    ).first()

    if not category:
        raise HTTPException(
            status_code=400,
            detail=f"无效分类组合"
        )

    # 创建食物记录
    db_food = Food(
        name=food_data.name,
        category_large=food_data.category_large,
        category_small=food_data.category_small,
        expiry_days=food_data.expiry_days,
        photo_path=food_data.photo_path,
        storage_time=datetime.now()
    )

    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food


# 新增图片上传接口
ALLOWED_TYPES = ["image/jpeg", "image/png"]


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "仅支持JPEG/PNG格式")

    # 生成唯一文件名：时间戳_原文件名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    save_path = f"static/uploads/{filename}"

    # 保存文件
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": filename, "path": save_path}


@router.get("/", summary="获取食物列表（分页排序）",
            description="支持排序字段：storage_time（入库时间）, expiry_days（保质期天数）, remaining_days（剩余天数）")
def get_foods(
        query: FoodQueryParams = Depends(),
        db: Session = Depends(get_db)
):
    """获取食物列表"""
    # 参数验证
    valid_sort_fields = ["storage_time", "expiry_days", "remaining_days"]
    if query.sort_by not in valid_sort_fields:
        raise HTTPException(400, f"排序字段必须是 {valid_sort_fields} 之一")

    if query.order not in ["asc", "desc"]:
        raise HTTPException(400, "排序方式必须是 asc 或 desc")

    # 构建基础查询
    base_query = db.query(Food)

    # 根据 include_deleted 参数调整查询条件
    if not query.include_deleted:
        base_query = base_query.filter(Food.is_deleted == False)

    # 处理剩余天数排序
    if query.sort_by == "remaining_days":
        # 使用SQLAlchemy核心表达式
        remaining_days_expr = (
                Food.expiry_days -
                (func.julianday(func.datetime('now')) - func.julianday(Food.storage_time))
        ).label("remaining_days")
        order_clause = remaining_days_expr.desc() if query.order == "desc" else remaining_days_expr.asc()
        base_query = base_query.add_columns(remaining_days_expr)
    else:
        # 普通字段排序
        column = getattr(Food, query.sort_by)
        order_clause = desc(column) if query.order == "desc" else column.asc()

    # 执行分页查询
    try:
        result = (
            base_query
            .order_by(order_clause)
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
            .all()
        )
    except OperationalError as e:
        raise HTTPException(500, f"数据库查询错误: {str(e)}")

    # 处理结果集
    if query.sort_by == "remaining_days":
        foods = [row[0] for row in result]
    else:
        foods = result

    # 获取总数（需要独立查询）
    total_query = db.query(func.count(Food.id))
    if not query.include_deleted:
        total_query = total_query.filter(Food.is_deleted == False)
    total = total_query.scalar()

    # 将SQLAlchemy模型转换为Pydantic响应模型
    response_data = []
    for food in foods:
        expiry_date = food.storage_time + timedelta(days=food.expiry_days)
        remaining_days = (expiry_date - datetime.now()).days

        response_data.append(FoodResponse(
            id=food.id,
            name=food.name,
            category_large=food.category_large,
            category_small=food.category_small,
            expiry_days=food.expiry_days,
            photo_path=food.photo_path,
            storage_time=food.storage_time,
            remaining_days=remaining_days
        ))

    return {
        "data": response_data,
        "pagination": {
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
            "total_pages": (total + query.page_size - 1) // query.page_size
        }
    }


@router.get("/{food_id}", response_model=FoodResponse)
def get_food_detail(
        food_id: int,
        db: Session = Depends(get_db)
):
    """获取单个食物详情"""
    # 查询食物
    db_food = db.query(Food).filter(Food.id == food_id).first()

    if not db_food:
        raise HTTPException(status_code=404, detail="食物不存在")

    # 计算剩余天数
    expiry_date = db_food.storage_time + timedelta(days=db_food.expiry_days)
    remaining_days = (expiry_date - datetime.now()).days

    return FoodResponse(
        id=db_food.id,
        name=db_food.name,
        category_large=db_food.category_large,
        category_small=db_food.category_small,
        expiry_days=db_food.expiry_days,
        photo_path=db_food.photo_path,
        storage_time=db_food.storage_time,
        remaining_days=remaining_days
    )


@router.delete("/{food_id}")
def delete_food(
        food_id: int,
        db: Session = Depends(get_db)
):
    """删除指定食物"""
    # 查询食物是否存在
    db_food = db.query(Food).filter(Food.id == food_id).first()
    if not db_food:
        raise HTTPException(status_code=404, detail="食物不存在")

    # 执行软删除操作
    try:
        db_food.is_deleted = True  # 更新软删除字段
        db.commit()
    except OperationalError as e:
        db.rollback()
        raise HTTPException(500, f"数据库操作失败: {str(e)}")

    return {"message": "食物删除成功"}