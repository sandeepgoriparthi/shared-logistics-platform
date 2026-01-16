"""
Dynamic Pricing Model using Deep Reinforcement Learning

Uses Proximal Policy Optimization (PPO) to learn optimal pricing
that balances:
- Maximizing revenue
- Increasing pooling probability
- Maintaining carrier satisfaction
- Ensuring shipper cost savings

This is a key differentiator from competitors who use static pricing.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Normal
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from collections import deque
import structlog

logger = structlog.get_logger()


@dataclass
class PricingState:
    """State representation for pricing decision"""
    # Market conditions
    current_utilization: float  # 0-1
    demand_forecast: float  # Predicted demand (normalized)
    supply_availability: float  # Available carrier capacity (normalized)

    # Shipment specifics
    distance_miles: float
    weight_lbs: float
    linear_feet: float
    time_flexibility_hours: float

    # Competition
    competitor_rate: float  # Market rate per mile
    historical_win_rate: float  # Our win rate at current price

    # Pooling potential
    pooling_probability: float  # ML-predicted probability of pooling
    potential_savings_pct: float  # If pooled

    # Time factors
    days_to_pickup: float
    day_of_week: int  # 0-6
    hour_of_day: int  # 0-23

    def to_tensor(self) -> torch.Tensor:
        """Convert to normalized tensor"""
        return torch.tensor([
            self.current_utilization,
            self.demand_forecast,
            self.supply_availability,
            min(self.distance_miles / 1000, 1),
            min(self.weight_lbs / 45000, 1),
            min(self.linear_feet / 53, 1),
            min(self.time_flexibility_hours / 72, 1),
            min(self.competitor_rate / 5, 1),
            self.historical_win_rate,
            self.pooling_probability,
            self.potential_savings_pct,
            min(self.days_to_pickup / 14, 1),
            self.day_of_week / 6,
            self.hour_of_day / 23
        ], dtype=torch.float32)


@dataclass
class PricingAction:
    """Pricing action output"""
    rate_per_mile: float
    discount_percent: float
    surge_percent: float
    final_rate: float

    @property
    def final_price_per_mile(self) -> float:
        return self.final_rate


@dataclass
class PricingReward:
    """Reward signal components"""
    booking_success: float  # 1 if booked, 0 otherwise
    revenue: float  # Actual revenue earned
    pooling_success: float  # 1 if successfully pooled
    carrier_margin: float  # Carrier profit margin
    shipper_savings: float  # Savings vs market rate
    utilization_improvement: float  # Change in capacity utilization


class ActorNetwork(nn.Module):
    """
    Actor network that outputs pricing decisions

    Outputs mean and std for continuous price adjustment
    """

    def __init__(
        self,
        state_dim: int = 14,
        hidden_dim: int = 256,
        action_dim: int = 2  # rate adjustment, discount
    ):
        super().__init__()

        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, hidden_dim)

        # Output layers for action mean and log_std
        self.mean_layer = nn.Linear(hidden_dim, action_dim)
        self.log_std_layer = nn.Linear(hidden_dim, action_dim)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0)

    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))

        mean = self.mean_layer(x)
        log_std = self.log_std_layer(x)

        # Clamp log_std for stability
        log_std = torch.clamp(log_std, -20, 2)

        return mean, log_std

    def get_action(
        self,
        state: torch.Tensor,
        deterministic: bool = False
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        mean, log_std = self.forward(state)
        std = log_std.exp()

        if deterministic:
            action = mean
        else:
            dist = Normal(mean, std)
            action = dist.sample()

        # Calculate log probability
        log_prob = Normal(mean, std).log_prob(action).sum(dim=-1)

        return action, log_prob


class CriticNetwork(nn.Module):
    """
    Critic network that estimates state value
    """

    def __init__(
        self,
        state_dim: int = 14,
        hidden_dim: int = 256
    ):
        super().__init__()

        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, hidden_dim)
        self.value_layer = nn.Linear(hidden_dim, 1)

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        value = self.value_layer(x)
        return value


class PPOAgent:
    """
    Proximal Policy Optimization agent for dynamic pricing

    PPO is chosen because:
    - Stable training with clipped objective
    - Works well with continuous action spaces
    - Sample efficient compared to other policy gradient methods
    """

    def __init__(
        self,
        state_dim: int = 14,
        action_dim: int = 2,
        hidden_dim: int = 256,
        lr_actor: float = 3e-4,
        lr_critic: float = 1e-3,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        entropy_coef: float = 0.01,
        value_coef: float = 0.5,
        max_grad_norm: float = 0.5,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.entropy_coef = entropy_coef
        self.value_coef = value_coef
        self.max_grad_norm = max_grad_norm

        # Networks
        self.actor = ActorNetwork(state_dim, hidden_dim, action_dim).to(device)
        self.critic = CriticNetwork(state_dim, hidden_dim).to(device)

        # Optimizers
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=lr_actor)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=lr_critic)

        # Experience buffer
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.dones = []

    def select_action(
        self,
        state: PricingState,
        deterministic: bool = False
    ) -> Tuple[PricingAction, float]:
        """Select pricing action given current state"""
        state_tensor = state.to_tensor().unsqueeze(0).to(self.device)

        with torch.no_grad():
            action, log_prob = self.actor.get_action(state_tensor, deterministic)
            value = self.critic(state_tensor)

        action = action.cpu().numpy()[0]
        log_prob = log_prob.cpu().item()
        value = value.cpu().item()

        # Convert action to pricing decision
        # Action[0]: rate adjustment (-0.5 to +0.5 relative to base)
        # Action[1]: discount/surge (-0.3 to +0.3)
        rate_adjustment = np.tanh(action[0]) * 0.5
        discount_surge = np.tanh(action[1]) * 0.3

        base_rate = state.competitor_rate
        adjusted_rate = base_rate * (1 + rate_adjustment)

        if state.pooling_probability > 0.7:
            # High pooling probability - offer discount
            final_rate = adjusted_rate * (1 - abs(discount_surge))
            discount = abs(discount_surge) * 100
            surge = 0
        else:
            # Low pooling - may apply surge
            final_rate = adjusted_rate * (1 + max(0, discount_surge))
            discount = 0
            surge = max(0, discount_surge) * 100

        pricing_action = PricingAction(
            rate_per_mile=adjusted_rate,
            discount_percent=discount,
            surge_percent=surge,
            final_rate=final_rate
        )

        return pricing_action, log_prob, value

    def store_transition(
        self,
        state: PricingState,
        action: np.ndarray,
        reward: float,
        value: float,
        log_prob: float,
        done: bool
    ):
        """Store transition in buffer"""
        self.states.append(state.to_tensor())
        self.actions.append(torch.tensor(action, dtype=torch.float32))
        self.rewards.append(reward)
        self.values.append(value)
        self.log_probs.append(log_prob)
        self.dones.append(done)

    def compute_gae(self, next_value: float) -> Tuple[torch.Tensor, torch.Tensor]:
        """Compute Generalized Advantage Estimation"""
        advantages = []
        returns = []
        gae = 0

        values = self.values + [next_value]

        for step in reversed(range(len(self.rewards))):
            delta = (
                self.rewards[step] +
                self.gamma * values[step + 1] * (1 - self.dones[step]) -
                values[step]
            )
            gae = delta + self.gamma * self.gae_lambda * (1 - self.dones[step]) * gae
            advantages.insert(0, gae)
            returns.insert(0, gae + values[step])

        advantages = torch.tensor(advantages, dtype=torch.float32)
        returns = torch.tensor(returns, dtype=torch.float32)

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        return advantages, returns

    def update(self, num_epochs: int = 10, batch_size: int = 64):
        """Update actor and critic using PPO"""
        if len(self.states) < batch_size:
            return {}

        # Get final value for GAE computation
        with torch.no_grad():
            final_state = self.states[-1].unsqueeze(0).to(self.device)
            next_value = self.critic(final_state).cpu().item()

        advantages, returns = self.compute_gae(next_value)

        # Convert to tensors
        states = torch.stack(self.states).to(self.device)
        actions = torch.stack(self.actions).to(self.device)
        old_log_probs = torch.tensor(self.log_probs, dtype=torch.float32).to(self.device)
        advantages = advantages.to(self.device)
        returns = returns.to(self.device)

        # Training metrics
        total_actor_loss = 0
        total_critic_loss = 0
        total_entropy = 0

        for _ in range(num_epochs):
            # Random permutation for mini-batches
            indices = torch.randperm(len(states))

            for start in range(0, len(states), batch_size):
                end = start + batch_size
                batch_indices = indices[start:end]

                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]

                # Actor loss
                mean, log_std = self.actor(batch_states)
                std = log_std.exp()
                dist = Normal(mean, std)

                new_log_probs = dist.log_prob(batch_actions).sum(dim=-1)
                entropy = dist.entropy().sum(dim=-1).mean()

                ratio = (new_log_probs - batch_old_log_probs).exp()

                # Clipped surrogate objective
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(
                    ratio,
                    1 - self.clip_epsilon,
                    1 + self.clip_epsilon
                ) * batch_advantages

                actor_loss = -torch.min(surr1, surr2).mean()
                actor_loss = actor_loss - self.entropy_coef * entropy

                # Critic loss
                values = self.critic(batch_states).squeeze()
                critic_loss = F.mse_loss(values, batch_returns)

                # Update actor
                self.actor_optimizer.zero_grad()
                actor_loss.backward()
                nn.utils.clip_grad_norm_(self.actor.parameters(), self.max_grad_norm)
                self.actor_optimizer.step()

                # Update critic
                self.critic_optimizer.zero_grad()
                critic_loss.backward()
                nn.utils.clip_grad_norm_(self.critic.parameters(), self.max_grad_norm)
                self.critic_optimizer.step()

                total_actor_loss += actor_loss.item()
                total_critic_loss += critic_loss.item()
                total_entropy += entropy.item()

        # Clear buffer
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.dones = []

        num_updates = num_epochs * (len(states) // batch_size + 1)

        return {
            "actor_loss": total_actor_loss / num_updates,
            "critic_loss": total_critic_loss / num_updates,
            "entropy": total_entropy / num_updates
        }

    def save(self, path: str):
        """Save model weights"""
        torch.save({
            "actor": self.actor.state_dict(),
            "critic": self.critic.state_dict(),
            "actor_optimizer": self.actor_optimizer.state_dict(),
            "critic_optimizer": self.critic_optimizer.state_dict()
        }, path)

    def load(self, path: str):
        """Load model weights"""
        checkpoint = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(checkpoint["actor"])
        self.critic.load_state_dict(checkpoint["critic"])
        self.actor_optimizer.load_state_dict(checkpoint["actor_optimizer"])
        self.critic_optimizer.load_state_dict(checkpoint["critic_optimizer"])


class DynamicPricingEngine:
    """
    High-level dynamic pricing interface

    Features:
    - Real-time price optimization
    - Market-aware adjustments
    - Pooling incentive integration
    - A/B testing support
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        base_rate_per_mile: float = 2.50,
        min_rate_per_mile: float = 1.50,
        max_rate_per_mile: float = 5.00
    ):
        self.agent = PPOAgent()
        self.base_rate = base_rate_per_mile
        self.min_rate = min_rate_per_mile
        self.max_rate = max_rate_per_mile

        if model_path:
            self.agent.load(model_path)

        # Pricing history for analysis
        self.pricing_history = deque(maxlen=10000)

    def get_price(
        self,
        state: PricingState,
        deterministic: bool = True
    ) -> PricingAction:
        """Get optimal price for a shipment"""
        action, log_prob, value = self.agent.select_action(state, deterministic)

        # Clamp final rate to bounds
        action.final_rate = np.clip(action.final_rate, self.min_rate, self.max_rate)

        # Store for analysis
        self.pricing_history.append({
            "state": state,
            "action": action,
            "value": value
        })

        return action

    def compute_reward(
        self,
        state: PricingState,
        action: PricingAction,
        outcome: PricingReward
    ) -> float:
        """Compute composite reward for RL training"""
        # Weight different objectives
        reward = (
            0.30 * outcome.booking_success +
            0.25 * (outcome.revenue / (state.distance_miles * self.base_rate)) +
            0.20 * outcome.pooling_success +
            0.15 * outcome.carrier_margin +
            0.10 * outcome.utilization_improvement
        )

        # Penalty for extreme prices
        if action.final_rate < self.min_rate * 1.1:
            reward -= 0.1
        if action.final_rate > self.max_rate * 0.9:
            reward -= 0.1

        return reward

    def train_step(
        self,
        state: PricingState,
        outcome: PricingReward,
        done: bool = False
    ):
        """Single training step with observed outcome"""
        action, log_prob, value = self.agent.select_action(state, deterministic=False)
        reward = self.compute_reward(state, action, outcome)

        # Convert action to numpy for storage
        action_np = np.array([
            np.arctanh(np.clip((action.rate_per_mile / state.competitor_rate - 1) * 2, -0.99, 0.99)),
            np.arctanh(np.clip((action.discount_percent - action.surge_percent) / 30, -0.99, 0.99))
        ])

        self.agent.store_transition(state, action_np, reward, value, log_prob, done)

        return action, reward

    def update_model(self) -> dict:
        """Update model with collected experience"""
        return self.agent.update()

    def save_model(self, path: str):
        """Save pricing model"""
        self.agent.save(path)

    def load_model(self, path: str):
        """Load pricing model"""
        self.agent.load(path)
