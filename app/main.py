from fastapi import FastAPI
from .database import engine
from .models import Food
from .routers import food, category

# 创建数据库表
Food.metadata.create_all(bind=engine)

app = FastAPI()

# 挂载子路由
app.include_router(food.router)
app.include_router(category.router)