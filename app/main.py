from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import engine
from .models import Food, Category
from .routers import food, category
from .config import settings

# 创建数据库表
Food.metadata.create_all(bind=engine)

app = FastAPI()

# 挂载子路由
app.include_router(food.router)
app.include_router(category.router)
app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)