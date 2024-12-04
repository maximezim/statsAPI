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
    get_interactions_by_user, init_db, create_user, login, get_user 
)

from jwtUtils import set_secret_key, role_required, create_access_token, get_current_user
from utils import compute_usage_stats, compute_interactions_stats, compute_feedback_stats
from fastapi.concurrency import run_in_threadpool

from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi.encoders import jsonable_encoder


redis_client = None
admin_credentials = {}  
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_client = redis.from_url("redis://redis", encoding="utf8", decode_responses=True)

    SECRET_KEY = secrets.token_urlsafe(32)
    set_secret_key(SECRET_KEY)
    logging.basicConfig(level=logging.INFO)
    logging.info("SECRET_KEY is set.")

    await run_in_threadpool(init_db)

    admin_username = "admin"
    admin_password = secrets.token_urlsafe(16)  

    admin_user = await run_in_threadpool(get_user, admin_username)
    if not admin_user:
        await run_in_threadpool(create_user, admin_username, admin_password, True)
        logging.info(f"Admin user '{admin_username}' created with password '{admin_password}'")
    else:
        logging.info(f"Admin user '{admin_username}' already exists.")


@app.post("/interactions/")
async def create_interaction(
    interaction: InteractionCreate,
    current_user: dict = Depends(get_current_user)
):
    await run_in_threadpool(insert_interaction, current_user['username'], interaction)
    await redis_client.delete("usage_stats")
    await redis_client.delete("interactions_stats")
    await redis_client.delete("feedback_stats")
    await redis_client.delete("interactions_all")
    await redis_client.delete(f"interactions_{current_user['username']}")
    return {"message": "Interaction enregistrée"}


@app.get("/interactions/", dependencies=[Depends(role_required("admin"))])
async def read_interactions():
    cache_key = "interactions_all"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    interactions = await run_in_threadpool(get_all_interactions)
    interactions_data = jsonable_encoder(interactions)
    await redis_client.set(cache_key, json.dumps(interactions_data), ex=300)  # Cache for 5 minutes
    return interactions_data

@app.get("/interactions/{username}", dependencies=[Depends(role_required("admin"))])
async def read_user_interactions(username: str):
    cache_key = f"interactions_{username}"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    interactions = await run_in_threadpool(get_interactions_by_user, username)
    interactions_data = jsonable_encoder(interactions)
    await redis_client.set(cache_key, json.dumps(interactions_data), ex=300)  # Cache for 5 minutes
    return interactions_data


@app.get("/stats/usage", dependencies=[Depends(role_required("admin"))])
async def get_usage_stats():
    cache_key = "usage_stats"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return {"usage_stats": json.loads(cached_data)}
    usage_stats = await compute_usage_stats()
    await redis_client.set(cache_key, json.dumps(usage_stats), ex=3600)  # Cache for 1 hour
    return {"usage_stats": usage_stats}

@app.get("/stats/interactions", dependencies=[Depends(role_required("admin"))])
async def get_interactions_stats():
    cache_key = "interactions_stats"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return {"interactions_stats": json.loads(cached_data)}
    interaction_stats = await compute_interactions_stats()
    await redis_client.set(cache_key, json.dumps(interaction_stats), ex=1800)  # Cache for 30 minutes
    return {"interactions_stats": interaction_stats}

@app.get("/stats/feedback", dependencies=[Depends(role_required("admin"))])
async def get_feedback_stats():
    cache_key = "feedback_stats"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return {"feedback_stats": json.loads(cached_data)}
    feedback_stats = await compute_feedback_stats()
    await redis_client.set(cache_key, json.dumps(feedback_stats), ex=7200)  # Cache for 2 hours
    return {"feedback_stats": feedback_stats}

@app.post("/create_user")
async def create_user_end(user: CreateUserRequest):
    try:
        created_user = await run_in_threadpool(create_user, user.username, user.password, False)
        return {"message": "User created", "username": created_user.username}
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    except SQLAlchemyError as e:
        # Handle other SQLAlchemy exceptions
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        # Handle unexpected exceptions
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/login", response_model=Token)
async def login_end(user: Login):
    user_in_db = await run_in_threadpool(login, user.username, user.password)
    if not user_in_db:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    role = "admin" if user_in_db.isAdmin else "user"
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user_in_db.username, "role": role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


