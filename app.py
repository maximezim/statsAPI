# app.py
import os
import logging
import secrets
import json

from fastapi import FastAPI, Depends, HTTPException, status
import redis.asyncio as redis  

from interactions import (
    InteractionCreate, insert_interaction, get_all_interactions, 
    get_interactions_by_user, init_db  
)
from jwtUtils import set_secret_key, role_required
from compute_stats import compute_usage_stats, compute_interactions_stats, compute_feedback_stats
from fastapi.concurrency import run_in_threadpool

redis_client = None  
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_client = redis.from_url("redis://redis", encoding="utf8", decode_responses=True)
    
    # Generate SECRET_KEY
    SECRET_KEY = secrets.token_urlsafe(32)
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    
    # Set SECRET_KEY in jwtUtils
    set_secret_key(SECRET_KEY)
    
    # Log SECRET_KEY in Docker logs
    logging.basicConfig(level=logging.INFO)
    logging.info(f"SECRET_KEY: {SECRET_KEY}")
    
    # Initialize the database
    init_db()

@app.post("/interactions/")
async def create_interaction(interaction: InteractionCreate):
    await run_in_threadpool(insert_interaction, interaction)
    return {"message": "Interaction enregistrée"}

@app.get("/interactions/", dependencies=[Depends(role_required("admin"))])
async def read_interactions():
    interactions = await run_in_threadpool(get_all_interactions)
    return interactions

@app.get("/interactions/{user_id}", dependencies=[Depends(role_required("admin"))])
async def read_user_interactions(user_id: int):
    interactions = await run_in_threadpool(get_interactions_by_user, user_id)
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
