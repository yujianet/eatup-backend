from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import engine
from .models import Food, Category
from .routers import food, category

# 创建数据库表
Food.metadata.create_all(bind=engine)

app = FastAPI()

# 挂载子路由
app.include_router(food.router)
app.include_router(category.router)
app.mount("/static", StaticFiles(directory="static"), name="static")


def init_categories(db: Session):
    if db.query(Category).count() == 0:
        # 初始化数据（大分类冗余存储）
        default_data = [
            {'large': '蔬菜', 'small': '叶菜', 'days': 3},
            {'large': '蔬菜', 'small': '根茎', 'days': 7},
            {'large': '水果', 'small': '浆果', 'days': 5},
            {'large': '水果', 'small': '柑橘', 'days': 10}
        ]

        for item in default_data:
            category = Category(
                large_category=item['large'],
                small_category=item['small'],
                expiry_days=item['days']
            )
            db.add(category)
        db.commit()