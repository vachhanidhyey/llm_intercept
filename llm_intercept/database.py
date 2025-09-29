"""Database initialization and management."""

import os
from sqlmodel import SQLModel, create_engine, Session


def get_database_url() -> str:
    """Get database URL from environment or use default."""
    return os.getenv("DATABASE_URL", "sqlite:///./llm_intercept.db")


def get_engine():
    """Create and return database engine."""
    database_url = get_database_url()
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, echo=False)


def init_db(engine):
    """Initialize database tables."""
    SQLModel.metadata.create_all(engine)


def get_session(engine):
    """Get database session."""
    return Session(engine)