import logging
import shutil
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Food, Category
from ..schemas.food import FoodResponse, FoodCreate, FoodQueryParams
from ..config import settings

router = APIRouter(prefix="/foods", tags=["foods"])
logger = logging.getLogger(__name__)


def get_food_by_id(food_id: int, db: Session):
    return db.query(Food).filter(Food.id == food_id).first()


def get_category_by_name(large_category: str, small_category: str, db: Session):
    return db.query(Category).filter(
        Category.large_category == large_category,
        Category.small_category == small_category
    ).first()


def calculate_remaining_days(food: Food):
    expiry_date = food.storage_time + timedelta(days=food.expiry_days)
    return (expiry_date - datetime.now()).days


def handle_database_exception(e: Exception, db: Session, message: str):
    db.rollback()
    logger.error(f"Error occurred: {str(e)}")
    raise HTTPException(500, message)


@router.post("/", status_code=201)
def create_food(
        food_data: FoodCreate,
        db: Session = Depends(get_db)
):
    """创建食物"""
    category = get_category_by_name(food_data.category_large, food_data.category_small, db)
    if not category:
        raise HTTPException(status_code=400, detail="无效分类组合")

    db_food = Food(
        name=food_data.name,
        category_large=food_data.category_large,
        category_small=food_data.category_small,
        expiry_days=food_data.expiry_days,
        photo_path=food_data.photo_path,
        storage_time=datetime.now()
    )

    db.add(db_food)
    try:
        db.commit()
        db.refresh(db_food)
    except OperationalError as e:
        handle_database_exception(e, db, "数据库操作失败")

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
    save_path = f"{settings.UPLOAD_DIR}/{filename}"
    url_path = f"{settings.UPLOAD_URL_PREFIX}/{filename}"

    # 保存文件
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": filename, "path": url_path}


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
    db_food = get_food_by_id(food_id, db)
    if not db_food:
        raise HTTPException(status_code=404, detail="食物不存在")

    remaining_days = calculate_remaining_days(db_food)

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


@router.put("/{food_id}", response_model=FoodResponse)
def update_food(
        food_id: int,
        food_data: FoodCreate,
        db: Session = Depends(get_db)
):
    """更新指定食物"""
    db_food = get_food_by_id(food_id, db)
    if not db_food:
        raise HTTPException(status_code=404, detail="食物不存在")

    category = get_category_by_name(food_data.category_large, food_data.category_small, db)
    if not category:
        raise HTTPException(status_code=400, detail="无效分类组合")

    db_food.name = food_data.name
    db_food.category_large = food_data.category_large
    db_food.category_small = food_data.category_small
    db_food.expiry_days = food_data.expiry_days
    db_food.photo_path = food_data.photo_path

    try:
        db.commit()
        db.refresh(db_food)
    except OperationalError as e:
        handle_database_exception(e, db, "数据库操作失败")

    remaining_days = calculate_remaining_days(db_food)

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


@router.put("/{food_id}/undo_delete", response_model=FoodResponse)
def undo_delete_food(
        food_id: int,
        db: Session = Depends(get_db)
):
    """撤销删除指定食物"""
    db_food = get_food_by_id(food_id, db)
    if not db_food:
        raise HTTPException(status_code=404, detail="食物不存在")

    if not db_food.is_deleted:
        raise HTTPException(status_code=400, detail="食物未被删除")

    try:
        logger.info(f"Undoing deletion for food ID {food_id}.")
        db_food.is_deleted = False
        db.commit()
        logger.info(f"Food with ID {food_id} has been successfully undone deletion.")
        db.refresh(db_food)
        logger.info(f"Food with ID {food_id} has been successfully refresh to undo deletion.")
    except OperationalError as e:
        handle_database_exception(e, db, "数据库操作失败")
    except Exception as e:
        handle_database_exception(e, db, "未知失败")

    remaining_days = calculate_remaining_days(db_food)

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
    db_food = get_food_by_id(food_id, db)
    if not db_food:
        raise HTTPException(status_code=404, detail="食物不存在")

    try:
        db_food.is_deleted = True
        db.commit()
    except OperationalError as e:
        handle_database_exception(e, db, "数据库操作失败")

    return {"message": "食物删除成功"}
