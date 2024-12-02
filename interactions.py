from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import os

Base = declarative_base()

class Interaction(Base):
    __tablename__ = 'interactions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    action = Column(String)
    timestamp = Column(DateTime)

class InteractionCreate(BaseModel):
    user_id: int
    action: str
    timestamp: datetime

def get_database_url():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    print(f"DATABASE_URL: {db_url}")  # Debugging
    return db_url

def get_engine():
    db_url = get_database_url()
    print(f"Connecting to database URL: {db_url}")  # Debugging
    return create_engine(db_url)

def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def init_db():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

def insert_interaction(interaction: InteractionCreate):
    db: Session = get_session()
    try:
        db_interaction = Interaction(
            user_id=interaction.user_id,
            action=interaction.action,
            timestamp=interaction.timestamp
        )
        db.add(db_interaction)
        db.commit()
        db.refresh(db_interaction)
        return db_interaction
    finally:
        db.close()

def get_all_interactions():
    db: Session = get_session()
    try:
        interactions = db.query(Interaction).all()
        return interactions
    finally:
        db.close()

def get_interactions_by_user(user_id: int):
    db: Session = get_session()
    try:
        interactions = db.query(Interaction).filter(Interaction.user_id == user_id).all()
        return interactions
    finally:
        db.close()
