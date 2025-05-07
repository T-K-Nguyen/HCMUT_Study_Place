from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL (using SQLite for simplicity)
DATABASE_URL = "sqlite:///room_booking.db"

# Create engine
engine = create_engine(DATABASE_URL, echo=True)  # echo=True for debugging

# Create base class for declarative models
Base = declarative_base()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()