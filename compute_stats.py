# compute_stats.py
from interactions import get_session, Interaction
from sqlalchemy import func
import pandas as pd
from sklearn.cluster import KMeans
import asyncio
from collections import defaultdict

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


def predict_next_action_sync(user_id):
    db = get_session()
    # Fetch interactions for the user, ordered by timestamp
    user_interactions = db.query(Interaction).filter_by(user_id=user_id).order_by(Interaction.timestamp).all()
    db.close()

    if not user_interactions:
        return {"message": f"No interactions found for user_id {user_id}"}

    # Build transition counts
    transitions = defaultdict(lambda: defaultdict(int))
    previous_action = None
    for interaction in user_interactions:
        current_action = interaction.action
        if previous_action is not None:
            transitions[previous_action][current_action] += 1
        previous_action = current_action

    # If the user has only one action in history
    if previous_action is None:
        return {"message": f"Not enough data to predict next action for user_id {user_id}"}

    # Get the last action the user performed
    last_action = user_interactions[-1].action

    # Predict the next action based on the most frequent transition
    next_actions = transitions.get(last_action, {})
    if not next_actions:
        return {"message": f"No subsequent actions found after action '{last_action}' for user_id {user_id}"}

    predicted_action = max(next_actions, key=next_actions.get)
    return {
        "user_id": user_id,
        "last_action": last_action,
        "predicted_next_action": predicted_action
    }

async def predict_next_action(user_id):
    return await asyncio.to_thread(predict_next_action_sync, user_id)