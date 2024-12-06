# compute_stats.py
from interactions import get_session, Interaction
from sqlalchemy import func
import pandas as pd
from sklearn.cluster import KMeans
import asyncio
from collections import defaultdict
import numpy as np
from sklearn.preprocessing import LabelEncoder

def compute_usage_stats_sync():
    db = get_session()
    # Compute total number of interactions
    total_interactions = db.query(func.count(Interaction.id)).scalar()
    # Compute total number of users
    total_users = db.query(Interaction.username).distinct().count()
    db.close()
    return {"total_interactions": total_interactions, "total_users": total_users}

async def compute_usage_stats():
    return await asyncio.to_thread(compute_usage_stats_sync)

def compute_interactions_stats_sync():
    db = get_session()
    # Compute interactions per user
    interactions_per_user = db.query(
        Interaction.username,
        func.count(Interaction.id).label('interaction_count')
    ).group_by(Interaction.username).all()
    db.close()
    # Convert to list of dicts
    results = [{"username": row[0], "interaction_count": row[1]} for row in interactions_per_user]
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
        username = interaction.username
        action = interaction.action
        if username not in data:
            data[username] = {}
        if action not in data[username]:
            data[username][action] = 0
        data[username][action] +=1

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
    results = [{"username": username, "cluster": int(cluster)} for username, cluster in cluster_assignments.items()]
    return results

async def compute_feedback_stats():
    return await asyncio.to_thread(compute_feedback_stats_sync)


def predict_next_action_sync(username):
    try:
        db = get_session()
        # Fetch interactions for the user, ordered by timestamp
        user_interactions = db.query(Interaction).filter_by(username=username).order_by(Interaction.timestamp).all()
        db.close()

        if not user_interactions:
            return {"message": f"Aucune interaction trouvée pour l'utilisateur {username}"}

        # Extract the sequence of actions
        actions_sequence = [interaction.action for interaction in user_interactions]

        # Build the list of unique actions
        all_actions = list(set(actions_sequence))

        # Encode actions as integers
        le = LabelEncoder()
        le.fit(all_actions)
        encoded_actions = le.transform(actions_sequence)

        # Build the transition matrix
        n_actions = len(le.classes_)
        transition_matrix = np.zeros((n_actions, n_actions))

        for (current_action, next_action) in zip(encoded_actions[:-1], encoded_actions[1:]):
            transition_matrix[current_action][next_action] += 1

        # Normalize the transition matrix to get probabilities
        row_sums = transition_matrix.sum(axis=1)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        transition_prob_matrix = transition_matrix / row_sums[:, np.newaxis]

        # Get the last action performed by the user
        last_action = actions_sequence[-1]
        last_action_encoded = le.transform([last_action])[0]

        # Predict the next action
        next_action_probs = transition_prob_matrix[last_action_encoded]

        if np.all(next_action_probs == 0):
            return {"message": f"Aucune donnée de transition disponible après l'action '{last_action}' pour l'utilisateur {username}"}

        predicted_next_action_encoded = np.argmax(next_action_probs)
        predicted_next_action = le.inverse_transform([predicted_next_action_encoded])[0]
        probability = next_action_probs[predicted_next_action_encoded]

    except Exception as e:
        return {"error": str(e)}
    
    return {
        "username": username,
        "last_action": last_action,
        "predicted_next_action": predicted_next_action,
        "probability": float(probability)
    }

async def predict_next_action(username):
    return await asyncio.to_thread(predict_next_action_sync, username)