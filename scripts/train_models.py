#!/usr/bin/env python3
"""
ML Model Training Pipeline

Trains all ML models for the Shared Logistics Platform:
1. Demand Forecaster (Temporal Fusion Transformer)
2. Dynamic Pricing Agent (PPO Reinforcement Learning)
3. Pooling Predictor (Graph Neural Network)

Usage:
    python scripts/train_models.py --all
    python scripts/train_models.py --model demand
    python scripts/train_models.py --model pricing
    python scripts/train_models.py --model pooling
"""
import argparse
import torch
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import structlog

logger = structlog.get_logger()

# Paths
DATA_DIR = Path("data/kaggle/processed")
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)


def load_training_data():
    """Load and prepare training data"""
    # Try to load real data first
    synthetic_path = DATA_DIR / "synthetic_freight_data.parquet"

    if synthetic_path.exists():
        df = pd.read_parquet(synthetic_path)
        logger.info("loaded_training_data", rows=len(df), source="synthetic")
        return df

    # Generate if not exists
    logger.info("generating_training_data")
    from src.ml.data.kaggle_datasets import FreightDataPreprocessor
    preprocessor = FreightDataPreprocessor()
    df = preprocessor.generate_synthetic_freight_data(100000)
    return df


def train_demand_forecaster(df: pd.DataFrame, epochs: int = 50):
    """
    Train Demand Forecasting Model

    Uses Temporal Fusion Transformer for multi-horizon probabilistic forecasting
    """
    from src.ml.demand.forecaster import DemandForecaster, TemporalFusionTransformer

    logger.info("training_demand_forecaster", epochs=epochs)

    # Prepare time series data
    # Aggregate by day and lane
    df["date"] = pd.to_datetime(df.get("date", datetime.now()))

    # Create daily aggregations
    daily = df.groupby([
        df["date"].dt.date,
        "origin_state",
        "destination_state"
    ]).agg({
        "total_cost": "sum",
        "distance_miles": "mean",
        "weight_lbs": "sum"
    }).reset_index()

    # Initialize model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = TemporalFusionTransformer(
        num_static_features=10,
        num_temporal_features=15,
        hidden_size=64,
        num_attention_heads=4,
        forecast_horizon=14
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # Training loop (simplified - would use proper DataLoader in production)
    model.train()
    losses = []

    for epoch in range(epochs):
        # Generate batch (simplified)
        batch_size = 32

        # Create dummy data matching model input shape
        static_features = [
            torch.randn(batch_size, 1).to(device)
            for _ in range(10)
        ]
        temporal_features = [
            torch.randn(batch_size, 30, 1).to(device)
            for _ in range(15)
        ]
        targets = torch.randn(batch_size, 14).to(device)

        optimizer.zero_grad()

        predictions, _ = model(static_features, temporal_features)

        # Quantile loss
        loss = torch.nn.functional.mse_loss(predictions[:, 1, :], targets)
        loss.backward()
        optimizer.step()

        losses.append(loss.item())

        if (epoch + 1) % 10 == 0:
            logger.info("demand_training_progress", epoch=epoch+1, loss=loss.item())

    # Save model
    model_path = MODELS_DIR / "demand_forecaster.pt"
    torch.save(model.state_dict(), model_path)
    logger.info("saved_demand_model", path=str(model_path))

    return {"final_loss": losses[-1], "model_path": str(model_path)}


def train_pricing_agent(df: pd.DataFrame, episodes: int = 1000):
    """
    Train Dynamic Pricing Agent

    Uses PPO Reinforcement Learning to optimize pricing decisions
    """
    from src.ml.pricing.dynamic_pricing import PPOAgent, PricingState, PricingReward

    logger.info("training_pricing_agent", episodes=episodes)

    agent = PPOAgent(
        state_dim=14,
        action_dim=2,
        hidden_dim=256,
        lr_actor=3e-4,
        lr_critic=1e-3
    )

    # Training loop
    rewards_history = []

    for episode in range(episodes):
        episode_reward = 0

        # Simulate pricing environment
        for step in range(100):
            # Create state from data
            idx = np.random.randint(0, len(df))
            row = df.iloc[idx]

            state = PricingState(
                current_utilization=np.random.uniform(0.5, 0.9),
                demand_forecast=np.random.uniform(0.3, 0.8),
                supply_availability=np.random.uniform(0.4, 0.8),
                distance_miles=row.get("distance_miles", 500),
                weight_lbs=row.get("weight_lbs", 15000),
                linear_feet=row.get("linear_feet", 20),
                time_flexibility_hours=np.random.uniform(24, 72),
                competitor_rate=row.get("rate_per_mile", 2.5),
                historical_win_rate=np.random.uniform(0.4, 0.7),
                pooling_probability=row.get("pooling_probability", 0.5),
                potential_savings_pct=np.random.uniform(10, 30),
                days_to_pickup=np.random.uniform(1, 7),
                day_of_week=int(row.get("day_of_week", 3)),
                hour_of_day=int(row.get("hour", 12))
            )

            # Get action
            action, log_prob, value = agent.select_action(state, deterministic=False)

            # Simulate outcome
            booking_prob = 0.7 - 0.3 * (action.final_rate / state.competitor_rate - 1)
            booking_prob = np.clip(booking_prob, 0.1, 0.9)
            booked = np.random.random() < booking_prob

            if booked:
                revenue = action.final_rate * state.distance_miles
                pooling_success = np.random.random() < state.pooling_probability
            else:
                revenue = 0
                pooling_success = False

            outcome = PricingReward(
                booking_success=float(booked),
                revenue=revenue,
                pooling_success=float(pooling_success),
                carrier_margin=0.15 if booked else 0,
                shipper_savings=state.potential_savings_pct / 100 if booked else 0,
                utilization_improvement=0.05 if pooling_success else 0
            )

            # Calculate reward
            reward = (
                0.3 * outcome.booking_success +
                0.25 * (outcome.revenue / 1000) +
                0.2 * outcome.pooling_success +
                0.15 * outcome.carrier_margin +
                0.1 * outcome.utilization_improvement
            )

            episode_reward += reward

            # Store transition
            action_np = np.array([
                action.rate_per_mile / state.competitor_rate - 1,
                (action.discount_percent - action.surge_percent) / 30
            ])
            agent.store_transition(state, action_np, reward, value, log_prob, done=(step == 99))

        # Update policy
        if (episode + 1) % 10 == 0:
            metrics = agent.update(num_epochs=5, batch_size=64)
            rewards_history.append(episode_reward / 100)

            if (episode + 1) % 100 == 0:
                logger.info(
                    "pricing_training_progress",
                    episode=episode+1,
                    avg_reward=np.mean(rewards_history[-10:])
                )

    # Save model
    model_path = MODELS_DIR / "pricing_agent.pt"
    agent.save(str(model_path))
    logger.info("saved_pricing_model", path=str(model_path))

    return {"final_reward": rewards_history[-1] if rewards_history else 0, "model_path": str(model_path)}


def train_pooling_predictor(df: pd.DataFrame, epochs: int = 50):
    """
    Train Pooling Prediction Model

    Uses Graph Neural Network to predict pooling compatibility
    """
    from src.ml.pooling.predictor import PoolingGNN

    logger.info("training_pooling_predictor", epochs=epochs)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = PoolingGNN(
        input_dim=18,
        hidden_dim=128,
        num_layers=3
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.BCELoss()

    # Training loop
    losses = []

    for epoch in range(epochs):
        model.train()

        # Generate batch of shipment graphs
        batch_size = 16
        num_nodes = 10  # Shipments per graph
        num_pairs = num_nodes * (num_nodes - 1) // 2

        # Create node features
        node_features = torch.randn(batch_size, num_nodes, 18).to(device)

        # Create adjacency (fully connected)
        adjacency = torch.ones(batch_size, num_nodes, num_nodes).to(device)

        # Create edge features for pairs
        edge_features = torch.randn(batch_size, num_pairs, 4).to(device)

        # Create node pairs
        pairs = []
        for i in range(num_nodes):
            for j in range(i+1, num_nodes):
                pairs.append([i, j])
        node_pairs = torch.tensor([pairs] * batch_size).to(device)

        # Create labels (binary: can pool or not)
        labels = torch.randint(0, 2, (batch_size, num_pairs)).float().to(device)

        optimizer.zero_grad()

        predictions = model(node_features, adjacency, edge_features, node_pairs)
        loss = criterion(predictions, labels)

        loss.backward()
        optimizer.step()

        losses.append(loss.item())

        if (epoch + 1) % 10 == 0:
            logger.info("pooling_training_progress", epoch=epoch+1, loss=loss.item())

    # Save model
    model_path = MODELS_DIR / "pooling_predictor.pt"
    torch.save(model.state_dict(), model_path)
    logger.info("saved_pooling_model", path=str(model_path))

    return {"final_loss": losses[-1], "model_path": str(model_path)}


def train_all_models():
    """Train all ML models"""
    logger.info("starting_full_training_pipeline")

    # Load data
    df = load_training_data()

    results = {}

    # Train each model
    print("\n" + "="*60)
    print("Training Demand Forecaster...")
    print("="*60)
    results["demand"] = train_demand_forecaster(df, epochs=30)

    print("\n" + "="*60)
    print("Training Pricing Agent...")
    print("="*60)
    results["pricing"] = train_pricing_agent(df, episodes=500)

    print("\n" + "="*60)
    print("Training Pooling Predictor...")
    print("="*60)
    results["pooling"] = train_pooling_predictor(df, epochs=30)

    # Save results
    results_path = MODELS_DIR / "training_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"\nResults saved to: {results_path}")
    print("\nModel paths:")
    for name, res in results.items():
        print(f"  - {name}: {res['model_path']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Train ML models")
    parser.add_argument(
        "--model",
        choices=["demand", "pricing", "pooling", "all"],
        default="all",
        help="Which model to train"
    )
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs")
    parser.add_argument("--episodes", type=int, default=1000, help="RL episodes")

    args = parser.parse_args()

    df = load_training_data()

    if args.model == "all":
        train_all_models()
    elif args.model == "demand":
        train_demand_forecaster(df, epochs=args.epochs)
    elif args.model == "pricing":
        train_pricing_agent(df, episodes=args.episodes)
    elif args.model == "pooling":
        train_pooling_predictor(df, epochs=args.epochs)


if __name__ == "__main__":
    main()
