from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"
    UPLOAD_DIR: str = "static/uploads"

    class Config:
        env_file = ".env"


settings = Settings()
