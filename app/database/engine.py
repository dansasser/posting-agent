from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Define the path for the SQLite database.
# It will be created in the root of the project.
DATABASE_URL = "sqlite:///./facebook_agent.db"

# Create the SQLAlchemy engine.
# `check_same_thread` is needed only for SQLite. It's not needed for other databases.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a sessionmaker to manage database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency function to get a database session.
    Ensures the session is always closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()