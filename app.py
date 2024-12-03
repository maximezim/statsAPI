# app.py
import os
import logging
import secrets
import json
import uuid 

from fastapi import FastAPI, Depends, HTTPException, status
import redis.asyncio as redis  

from interactions import (
    InteractionCreate, Token, Location, CreateUserRequest, Login, insert_interaction, get_all_interactions, 
    get_interactions_by_user, init_db, create_user, login
)
from jwtUtils import set_secret_key, role_required, create_access_token
from utils import compute_usage_stats, compute_interactions_stats, compute_feedback_stats
from fastapi.concurrency import run_in_threadpool

from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

redis_client = None
admin_credentials = {}  
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_client = redis.from_url("redis://redis", encoding="utf8", decode_responses=True)
    
    SECRET_KEY = secrets.token_urlsafe(32)
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    
    # Set SECRET_KEY in jwtUtils
    set_secret_key(SECRET_KEY)
    logging.basicConfig(level=logging.INFO)
    logging.info(f"SECRET_KEY: {SECRET_KEY}")

    password = secrets.token_urlsafe(16)
    admin_credentials['username'] = "admin"
    admin_credentials['password'] = password
    logging.info(f"Admin credentials: {admin_credentials}")
    
    init_db()

@app.post("/interactions/")
async def create_interaction(interaction: InteractionCreate):
    await run_in_threadpool(insert_interaction, interaction)
    return {"message": "Interaction enregistrée"}

@app.get("/interactions/", dependencies=[Depends(role_required("admin"))])
async def read_interactions():
    interactions = await run_in_threadpool(get_all_interactions)
    return interactions

@app.get("/interactions/{username}", dependencies=[Depends(role_required("admin"))])
async def read_user_interactions(username: str):
    interactions = await run_in_threadpool(get_interactions_by_user, username)
    return interactions

@app.get("/stats/usage", dependencies=[Depends(role_required("admin"))])
async def get_usage_stats():
    cached_data = await redis_client.get("usage_stats")
    if cached_data:
        return {"usage_stats": json.loads(cached_data)}
    usage_stats = await compute_usage_stats()
    await redis_client.set("usage_stats", json.dumps(usage_stats), ex=3600)
    return {"usage_stats": usage_stats}

@app.get("/stats/interactions", dependencies=[Depends(role_required("admin"))])
async def get_interactions_stats():
    interaction_stats = await compute_interactions_stats()
    return {"interactions_stats": interaction_stats}

@app.get("/stats/feedback", dependencies=[Depends(role_required("admin"))])
async def get_feedback_stats():
    feedback_stats = await compute_feedback_stats()
    return {"feedback_stats": feedback_stats}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password
    
    if (username != admin_credentials['username']) or (password != admin_credentials['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)  
    access_token = create_access_token(
        data={"sub": username, "role": "admin"},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/create_user")
async def create_user_end(user: CreateUserRequest):
    created_user = await run_in_threadpool(create_user, user.username, user.password, False)
    return {"message": "User created", "username": created_user.username}


@app.post("/login")
async def login_end(user: Login):
    user = await run_in_threadpool(login,user.username, user.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "User logged in"}
