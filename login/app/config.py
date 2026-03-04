"""
Application configuration settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/oauth_users"
    )

    # JWT Configuration
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "your-super-secret-key-change-this-in-production-min-32-chars"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    # OAuth redirect URI (callback URL)
    GOOGLE_REDIRECT_URI: str = f"{BACKEND_URL}/auth/google/callback"

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # CORS origins (allow frontend to make requests)
    CORS_ORIGINS: list = [
        FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
    ]

    # File Storage Configuration
    BASE_STORAGE_PATH: str = os.getenv(
        "BASE_STORAGE_PATH",
        str(Path(__file__).parent.parent / "storage")
    )
    CV_STORAGE_PATH: str = os.getenv(
        "CV_STORAGE_PATH",
        str(Path(BASE_STORAGE_PATH) / "cvs")
    )
    MAX_CV_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB in bytes


# Create settings instance
settings = Settings()
