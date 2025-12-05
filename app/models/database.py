"""
Database initialization and connection
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.face_model import Base
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/face_recognition.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database tables
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")


def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
