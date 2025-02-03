import pathlib
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# 获取当前文件的绝对路径，并逐级向上直到找到项目的根目录
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from app.database.database import engine
from app.database.models import Food
from app.routers import router
from app.config import settings

# 创建数据库表
Food.metadata.create_all(bind=engine)

app = FastAPI()

# 挂载子路由
app.include_router(router)
app.mount(settings.UPLOAD_URL_PREFIX, StaticFiles(directory=settings.UPLOAD_DIR), name="static")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)