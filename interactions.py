# interactions.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, UUID, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import NullPool
from pydantic import BaseModel
from datetime import datetime
import os
import bcrypt
from typing import Optional
import logging

Base = declarative_base()

class Interaction(Base):
    __tablename__ = 'interactions'
    id = Column(Integer, primary_key=True, index=True)  
    username = Column(String)
    action = Column(String)
    timestamp = Column(DateTime)


class User(Base):
    __tablename__ = 'users'
    username = Column(String, primary_key=True, index=True)
    password = Column(String)
    isAdmin = Column(Boolean)
    location = Column(String)  

class CreateUserRequest(BaseModel):
    username: str
    password: str

class Login(BaseModel):
    username: str
    password: str

class InteractionCreate(BaseModel):
    action: str

class ValidCookieAndUser(BaseModel):
    valid: bool
    username: Optional[str]

class Token(BaseModel):
    access_token: str
    token_type: str

class Location(BaseModel):
    latitude: float
    longitude: float

class InteractionsList(BaseModel):
    interactions: str
    username: str

def get_database_url():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return db_url

engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,      
    pool_size=20,             
    max_overflow=0,           
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_session() -> Session:
    return SessionLocal()

def init_db():
    Base.metadata.create_all(bind=engine)

def insert_interaction(username: str, interaction: InteractionCreate):
    db = get_session()
    try:
        db_interaction = Interaction(
            username=username,
            action=interaction.action,
            timestamp=datetime.now()
        )
        db.add(db_interaction)
        db.commit()
        db.refresh(db_interaction)
        return db_interaction
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

def get_all_interactions():
    db = get_session()
    try:
        interactions = db.query(Interaction).all()
        return list(interactions)
    except Exception as e:
        logging.error(f"Error retrieving all interactions: {e}")
        raise
    finally:
        db.close()

def get_interactions_by_user(username: str):
    db = get_session()
    try:
        interactions = db.query(Interaction).filter(Interaction.username == username).all()
        return list(interactions)
    except Exception as e:
        logging.error(f"Error retrieving interactions for user {username}: {e}")
        raise
    finally:
        db.close()

def create_user(username: str, password: str, isAdmin: bool = False):
    db = get_session()
    try:
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise IntegrityError("Username already exists", None, None)

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db_user = User(
            username=username,
            password=hashed_password,
            isAdmin=isAdmin
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError as ie:
        db.rollback()
        logging.error(f"Integrity error creating user {username}: {ie}")
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating user {username}: {e}")
        raise
    finally:
        db.close()

def login(username: str, password: str):
    db = get_session()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            db.expunge(user)
            return user
        return None
    except Exception as e:
        logging.error(f"Error during login for user {username}: {e}")
        raise
    finally:
        db.close()

def get_user(username: str):
    db = get_session()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            db.expunge(user)
        return user
    except Exception as e:
        logging.error(f"Error retrieving user {username}: {e}")
        raise
    finally:
        db.close()
