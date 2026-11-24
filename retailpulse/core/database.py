"""
Database connection, session management, and safe query utilities.
"""
from contextlib import contextmanager
from typing import Generator, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from retailpulse.config import settings, DB_PATH
from retailpulse.core.logger import get_logger

logger = get_logger("retailpulse.db")

# Ensure parent directory exists for SQLite
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager for standalone database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()

def execute_raw_sql(query: str, params: dict | None = None) -> list[dict[str, Any]]:
    """Execute raw SQL query and return rows as list of dicts."""
    with SessionLocal() as session:
        result = session.execute(text(query), params or {})
        if result.returns_rows:
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
        return []
