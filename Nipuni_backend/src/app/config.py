from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env from root
env_file_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_file_path)

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    CORS_ORIGINS: str = "http://localhost:5173"
    UPLOAD_DIR: str = "backend/uploads"

    model_config = ConfigDict(
        extra='ignore',
        env_file=str(env_file_path)
    )

settings = Settings()
