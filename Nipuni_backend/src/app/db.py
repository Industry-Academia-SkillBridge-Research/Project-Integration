import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from root .env file
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(f"DATABASE_URL not found. Looked at: {env_path}")

# Create engine with MySQL-optimized settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # Verify connections before using
    pool_recycle=3600,        # Recycle connections after 1 hour
    pool_size=10,             # Connection pool size
    max_overflow=20,          # Additional connections if pool is full
    echo=False,               # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()