# compute_stats.py
from interactions import get_session, Interaction
from sqlalchemy import func
import pandas as pd
from sklearn.cluster import KMeans
import asyncio

def compute_usage_stats_sync():
    db = get_session()
    # Compute total number of interactions
    total_interactions = db.query(func.count(Interaction.id)).scalar()
    # Compute total number of users
    total_users = db.query(Interaction.user_id).distinct().count()
    db.close()
    return {"total_interactions": total_interactions, "total_users": total_users}

async def compute_usage_stats():
    return await asyncio.to_thread(compute_usage_stats_sync)

def compute_interactions_stats_sync():
    db = get_session()
    # Compute interactions per user
    interactions_per_user = db.query(
        Interaction.user_id,
        func.count(Interaction.id).label('interaction_count')
    ).group_by(Interaction.user_id).all()
    db.close()
    # Convert to list of dicts
    results = [{"user_id": row[0], "interaction_count": row[1]} for row in interactions_per_user]
    return results

async def compute_interactions_stats():
    return await asyncio.to_thread(compute_interactions_stats_sync)

def compute_feedback_stats_sync():
    db = get_session()
    # Fetch interactions data
    interactions = db.query(Interaction).all()
    db.close()
    
    # Prepare data for clustering
    data = {}
    for interaction in interactions:
        user_id = interaction.user_id
        action = interaction.action
        if user_id not in data:
            data[user_id] = {}
        if action not in data[user_id]:
            data[user_id][action] = 0
        data[user_id][action] +=1

    # Create DataFrame
    df = pd.DataFrame.from_dict(data, orient='index').fillna(0)
    if df.empty:
        return {"message": "Not enough data to compute feedback stats."}

    # Perform clustering
    try:
        kmeans = KMeans(n_clusters=3)
        clusters = kmeans.fit_predict(df)
        df['cluster'] = clusters
    except Exception as e:
        return {"error": str(e)}

    # Return cluster assignments
    cluster_assignments = df['cluster'].to_dict()
    results = [{"user_id": user_id, "cluster": int(cluster)} for user_id, cluster in cluster_assignments.items()]
    return results

async def compute_feedback_stats():
    return await asyncio.to_thread(compute_feedback_stats_sync)


