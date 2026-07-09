"""
SQLAlchemy database setup for BCG Healthcare Platform
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from healthcare_backend.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a SQLAlchemy session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist."""
    # Import models so they register with Base metadata
    from healthcare_backend.models import user, patient, scan, alert, monitoring_session  # noqa
    Base.metadata.create_all(bind=engine)
