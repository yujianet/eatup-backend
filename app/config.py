import pathlib
import sys
from os import getenv

from pydantic_settings import BaseSettings

current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"
    UPLOAD_DIR: str = "/static/uploads"
    UPLOAD_URL_PREFIX: str = "/static"
    AI_IMAGE_API_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    AI_IMAGE_API_KEY: str = "sk-37744c431af14ae9bd964490b0d8d652"
    AI_IMAGE_MODEL: str = "qwen2.5-vl-3b-instruct"

class TestSettings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"
    UPLOAD_DIR: str = str(project_root / 'static' / 'uploads')
    UPLOAD_URL_PREFIX: str = "/static"
    AI_IMAGE_API_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    AI_IMAGE_API_KEY: str = "sk-37744c431af14ae9bd964490b0d8d652"
    AI_IMAGE_MODEL: str = "qwen2.5-vl-3b-instruct"

if getenv("TESTING", "False"):
    settings = TestSettings()
    print("Running in test mode")
else:
    settings = Settings()
    print("Running in production mode")

sys.path.append(str(project_root))
