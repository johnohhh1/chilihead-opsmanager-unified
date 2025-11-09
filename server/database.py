"""Database connection and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv
from typing import Generator

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://openinbox:devpass123@localhost:5432/openinbox_dev")

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Disable connection pooling for development
    echo=False,  # Set to True to see SQL queries in console
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get a database session.
    
    Usage:
        @app.get("/tasks")
        def get_tasks(db: Session = Depends(get_db)):
            tasks = db.query(Task).all()
            return tasks
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("[OK] Database initialized successfully!")


if __name__ == "__main__":
    # Test connection
    print(f"Testing connection to: {DATABASE_URL}")
    try:
        with engine.connect() as conn:
            print("[OK] Database connection successful!")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
