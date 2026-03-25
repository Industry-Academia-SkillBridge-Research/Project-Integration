from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"
    CORS_ORIGINS: str = "http://localhost:5173"
    UPLOAD_DIR: str = "backend/uploads"

    model_config = ConfigDict(extra='ignore', env_file=".env")

settings = Settings()
