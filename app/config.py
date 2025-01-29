from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"
    UPLOAD_DIR: str = "/static/uploads"
    UPLOAD_URL_PREFIX: str = "/static"


settings = Settings()
