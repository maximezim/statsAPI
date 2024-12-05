# compute_stats.py
from interactions import get_session, Interaction
from sqlalchemy import func
import pandas as pd
from sklearn.cluster import KMeans
import asyncio
from collections import defaultdict
from pomegranate import HiddenMarkovModel, State, DiscreteDistribution

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
    db = get_session()
    # Fetch interactions for the user, ordered by timestamp
    user_interactions = db.query(Interaction).filter_by(username=username).order_by(Interaction.timestamp).all()
    db.close()

    if not user_interactions:
        return {"message": f"No interactions found for username {username}"}

    # Build transition counts
    transitions = defaultdict(lambda: defaultdict(int))
    previous_action = None
    for interaction in user_interactions:
        current_action = interaction.action
        if previous_action is not None:
            transitions[previous_action][current_action] += 1
        previous_action = current_action

    # Calculate transition probabilities
    transition_prob = {}
    for prev_action, next_actions in transitions.items():
        total = sum(next_actions.values())
        transition_prob[prev_action] = {action: count / total for action, count in next_actions.items()}

    # Get the last action the user performed
    last_action = user_interactions[-1].action

    # Predict the next action based on transition probabilities
    if last_action not in transition_prob:
        return {"message": f"No transition data available after action '{last_action}' for username {username}"}

    next_actions = transition_prob[last_action]
    predicted_action = max(next_actions, key=next_actions.get)
    probability = next_actions[predicted_action]

    return {
        "username": username,
        "last_action": last_action,
        "predicted_next_action": predicted_action,
        "probability": probability
    }

async def predict_next_action(username):
    return await asyncio.to_thread(predict_next_action_sync, username)


def train_markov_model():
    db = get_session()
    interactions = db.query(Interaction).order_by(Interaction.timestamp).all()
    db.close()

    # Organize interactions per user
    user_sequences = defaultdict(list)
    for interaction in interactions:
        user_sequences[interaction.username].append(interaction.action)

    # Prepare data for training
    sequences = [sequence for sequence in user_sequences.values() if len(sequence) > 1]

    if not sequences:
        logging.warning("Not enough data to train the Markov model.")
        return None

    # Define the model
    model = HiddenMarkovModel()

    # Extract unique actions
    action_set = set(action for sequence in sequences for action in sequence)
    distributions = {action: DiscreteDistribution({action: 1.0}) for action in action_set}

    states = {action: State(distributions[action], name=action) for action in action_set}

    # Add states to the model
    for state in states.values():
        model.add_state(state)

    # Define transitions based on the data
    transition_counts = defaultdict(lambda: defaultdict(int))
    for sequence in sequences:
        for i in range(len(sequence) - 1):
            current_action = sequence[i]
            next_action = sequence[i + 1]
            transition_counts[current_action][next_action] += 1

    # Add transitions to the model with probabilities
    for current_action, next_actions in transition_counts.items():
        total = sum(next_actions.values())
        for next_action, count in next_actions.items():
            probability = count / total
            model.add_transition(states[current_action], states[next_action], probability)

    # Finalize the model
    model.bake()
    return model

def predict_next_action_ml(username, model):
    db = get_session()
    user_interactions = db.query(Interaction).filter_by(username=username).order_by(Interaction.timestamp).all()
    db.close()

    if not user_interactions:
        return {"message": f"No interactions found for username {username}"}

    last_action = user_interactions[-1].action

    if last_action not in model.states:
        return {"message": f"Action '{last_action}' not in model states."}

    # Predict the next action using the model
    try:
        # Get transition probabilities from the current state
        current_state = model.states[last_action]
        transitions = current_state.transitions

        if not transitions:
            return {"message": f"No transitions available from action '{last_action}'."}

        # Find the transition with the highest probability
        predicted_transition = max(transitions, key=lambda t: t.probability)
        predicted_action = predicted_transition.to_state.name
        probability = predicted_transition.probability

        return {
            "username": username,
            "last_action": last_action,
            "predicted_next_action": predicted_action,
            "probability": probability
        }
    except Exception as e:
        return {"error": str(e)}


  
async def predict_next_action(username):
    return await asyncio.to_thread(predict_next_action_sync, username)

async def predict_next_action_ml_async(username, model):
    return await asyncio.to_thread(predict_next_action_ml, username, model)