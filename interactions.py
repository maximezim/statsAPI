# interactions.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, UUID, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import os
import bcrypt

Base = declarative_base()

class Interaction(Base):
    __tablename__ = 'interactions'
    username = Column(String, primary_key=True, index=True)
    action = Column(String)
    timestamp = Column(DateTime)

class User(Base):
    __tablename__ = 'users'
    username = Column(String, primary_key=True, index=True)
    password = Column(String)
    isAdmin = Column(Boolean)
    Location = Column(String)

class CreateUserRequest(BaseModel):
    username: str
    password: str

class Login(BaseModel):
    username: str
    password: str

class InteractionCreate(BaseModel):
    action: str
    timestamp: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class Location(BaseModel):
    latitude: float
    longitude: float

def get_database_url():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return db_url

def get_engine():
    db_url = get_database_url()
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
            username=interaction.username,
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

def get_interactions_by_user(username: str):
    db: Session = get_session()
    try:
        interactions = db.query(Interaction).filter(Interaction.username == username).all()
        return interactions
    finally:
        db.close()

def create_user(username: str, password: str, isAdmin: Boolean=False):
    db: Session = get_session()
    try:
        passw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        db_user = User(
            username=username,
            password=passw.decode('utf-8'),
            isAdmin=isAdmin
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    finally:
        db.close()

def login(username: str, password: str):
    db: Session = get_session()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return user
        return None
    finally:
        db.close()