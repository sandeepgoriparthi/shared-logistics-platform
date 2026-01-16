"""
Demand Forecasting Model

Uses a Temporal Fusion Transformer architecture for multi-horizon
forecasting of shipment demand by lane, time, and volume.

This enables proactive capacity positioning and dynamic pricing.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


@dataclass
class DemandForecast:
    """Forecast output"""
    lane: tuple[str, str]  # (origin_region, dest_region)
    date: datetime
    volume_p10: float  # 10th percentile
    volume_p50: float  # Median
    volume_p90: float  # 90th percentile
    confidence: float


class GatedResidualNetwork(nn.Module):
    """
    Gated Residual Network (GRN) - core building block of TFT

    Allows the model to skip over unused components via gating
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        output_size: int,
        dropout: float = 0.1,
        context_size: Optional[int] = None
    ):
        super().__init__()

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.context_size = context_size

        # Primary transformation
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, output_size)

        # Context projection if provided
        if context_size is not None:
            self.context_fc = nn.Linear(context_size, hidden_size, bias=False)

        # Gating
        self.gate_fc = nn.Linear(hidden_size, output_size)
        self.gate_norm = nn.LayerNorm(output_size)

        # Skip connection
        if input_size != output_size:
            self.skip_fc = nn.Linear(input_size, output_size)
        else:
            self.skip_fc = None

        self.dropout = nn.Dropout(dropout)
        self.elu = nn.ELU()

    def forward(self, x: torch.Tensor, context: Optional[torch.Tensor] = None):
        # Primary path
        hidden = self.fc1(x)

        if context is not None and self.context_size is not None:
            hidden = hidden + self.context_fc(context)

        hidden = self.elu(hidden)
        hidden = self.fc2(hidden)
        hidden = self.dropout(hidden)

        # Gating
        gate = torch.sigmoid(self.gate_fc(self.elu(self.fc1(x))))
        hidden = gate * hidden

        # Skip connection
        if self.skip_fc is not None:
            skip = self.skip_fc(x)
        else:
            skip = x

        return self.gate_norm(hidden + skip)


class VariableSelectionNetwork(nn.Module):
    """
    Variable Selection Network

    Learns which input features are most relevant for each prediction
    """

    def __init__(
        self,
        input_sizes: list[int],
        hidden_size: int,
        num_inputs: int,
        dropout: float = 0.1,
        context_size: Optional[int] = None
    ):
        super().__init__()

        self.hidden_size = hidden_size
        self.num_inputs = num_inputs

        # Individual GRNs for each input
        self.input_grns = nn.ModuleList([
            GatedResidualNetwork(
                input_size=size,
                hidden_size=hidden_size,
                output_size=hidden_size,
                dropout=dropout
            )
            for size in input_sizes
        ])

        # Softmax for variable weights
        self.weight_grn = GatedResidualNetwork(
            input_size=hidden_size * num_inputs,
            hidden_size=hidden_size,
            output_size=num_inputs,
            dropout=dropout,
            context_size=context_size
        )

    def forward(
        self,
        inputs: list[torch.Tensor],
        context: Optional[torch.Tensor] = None
    ):
        # Process each input through its GRN
        processed = [grn(inp) for grn, inp in zip(self.input_grns, inputs)]

        # Stack and concatenate for weight calculation
        stacked = torch.stack(processed, dim=-2)  # (batch, num_inputs, hidden)
        flattened = stacked.view(stacked.size(0), -1)

        # Calculate variable weights
        weights = F.softmax(self.weight_grn(flattened, context), dim=-1)
        weights = weights.unsqueeze(-1)  # (batch, num_inputs, 1)

        # Weighted combination
        combined = (stacked * weights).sum(dim=-2)

        return combined, weights.squeeze(-1)


class TemporalFusionTransformer(nn.Module):
    """
    Temporal Fusion Transformer for Demand Forecasting

    Key components:
    1. Variable Selection - learns important features
    2. LSTM Encoder - processes historical data
    3. Multi-head Attention - captures long-range dependencies
    4. Quantile outputs - provides uncertainty estimates
    """

    def __init__(
        self,
        num_static_features: int = 10,
        num_temporal_features: int = 15,
        hidden_size: int = 64,
        num_attention_heads: int = 4,
        num_lstm_layers: int = 2,
        dropout: float = 0.1,
        num_quantiles: int = 3,
        forecast_horizon: int = 14
    ):
        super().__init__()

        self.hidden_size = hidden_size
        self.forecast_horizon = forecast_horizon
        self.num_quantiles = num_quantiles

        # Static variable selection
        self.static_vsn = VariableSelectionNetwork(
            input_sizes=[1] * num_static_features,
            hidden_size=hidden_size,
            num_inputs=num_static_features,
            dropout=dropout
        )

        # Static context enrichment
        self.static_context_grn = GatedResidualNetwork(
            input_size=hidden_size,
            hidden_size=hidden_size,
            output_size=hidden_size,
            dropout=dropout
        )

        # Temporal variable selection
        self.temporal_vsn = VariableSelectionNetwork(
            input_sizes=[1] * num_temporal_features,
            hidden_size=hidden_size,
            num_inputs=num_temporal_features,
            dropout=dropout,
            context_size=hidden_size
        )

        # LSTM encoder
        self.lstm_encoder = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_lstm_layers,
            dropout=dropout if num_lstm_layers > 1 else 0,
            batch_first=True
        )

        # Self-attention for long-range dependencies
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=num_attention_heads,
            dropout=dropout,
            batch_first=True
        )
        self.attention_norm = nn.LayerNorm(hidden_size)

        # Output layers for quantile regression
        self.output_grn = GatedResidualNetwork(
            input_size=hidden_size,
            hidden_size=hidden_size,
            output_size=hidden_size,
            dropout=dropout
        )

        self.quantile_outputs = nn.ModuleList([
            nn.Linear(hidden_size, forecast_horizon)
            for _ in range(num_quantiles)
        ])

    def forward(
        self,
        static_features: list[torch.Tensor],
        temporal_features: list[torch.Tensor]
    ):
        batch_size = static_features[0].size(0)
        seq_len = temporal_features[0].size(1)

        # Static processing
        static_embedding, static_weights = self.static_vsn(static_features)
        static_context = self.static_context_grn(static_embedding)

        # Temporal processing
        temporal_list = []
        for t in range(seq_len):
            step_features = [f[:, t:t+1, :].squeeze(1) for f in temporal_features]
            step_embedding, _ = self.temporal_vsn(step_features, static_context)
            temporal_list.append(step_embedding)

        temporal_embedding = torch.stack(temporal_list, dim=1)

        # LSTM encoding
        lstm_out, _ = self.lstm_encoder(temporal_embedding)

        # Self-attention
        attention_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        attention_out = self.attention_norm(lstm_out + attention_out)

        # Take last timestep for forecasting
        final_state = attention_out[:, -1, :]

        # Output processing
        output_embedding = self.output_grn(final_state)

        # Quantile predictions
        quantile_predictions = [
            q_layer(output_embedding)
            for q_layer in self.quantile_outputs
        ]

        # Stack: (batch, num_quantiles, forecast_horizon)
        predictions = torch.stack(quantile_predictions, dim=1)

        return predictions, static_weights


class DemandForecaster:
    """
    High-level interface for demand forecasting

    Features:
    - Multi-horizon forecasting (1-14 days)
    - Uncertainty quantification via quantile regression
    - Lane-specific predictions (origin-destination pairs)
    - Incorporates external factors (weather, economics, seasonality)
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        self.model = TemporalFusionTransformer().to(device)

        if model_path:
            self.load_model(model_path)

        # Feature preprocessing
        self.static_features = [
            "origin_region",
            "dest_region",
            "lane_volume_avg",
            "lane_volume_std",
            "shipper_count",
            "carrier_count",
            "avg_rate",
            "competition_index",
            "infrastructure_score",
            "economic_index"
        ]

        self.temporal_features = [
            "historical_volume",
            "day_of_week",
            "month",
            "quarter",
            "is_holiday",
            "weather_severity",
            "fuel_price",
            "economic_indicator",
            "competitor_rates",
            "capacity_utilization",
            "booking_lead_time",
            "cancellation_rate",
            "on_time_rate",
            "damage_rate",
            "carrier_availability"
        ]

        # H3 resolution for lane definition
        self.h3_resolution = 4  # ~20km hexagons

    def prepare_features(
        self,
        lane: tuple[str, str],
        historical_data: dict,
        forecast_date: datetime
    ) -> tuple[list[torch.Tensor], list[torch.Tensor]]:
        """Prepare features for model input"""
        # Static features (example values - in production, fetch from database)
        static = [
            torch.tensor([[hash(lane[0]) % 100 / 100]], dtype=torch.float32),
            torch.tensor([[hash(lane[1]) % 100 / 100]], dtype=torch.float32),
            torch.tensor([[historical_data.get("avg_volume", 50) / 100]], dtype=torch.float32),
            torch.tensor([[historical_data.get("std_volume", 20) / 100]], dtype=torch.float32),
            torch.tensor([[historical_data.get("shipper_count", 100) / 1000]], dtype=torch.float32),
            torch.tensor([[historical_data.get("carrier_count", 50) / 500]], dtype=torch.float32),
            torch.tensor([[historical_data.get("avg_rate", 2.5) / 5]], dtype=torch.float32),
            torch.tensor([[historical_data.get("competition", 0.5)]], dtype=torch.float32),
            torch.tensor([[historical_data.get("infrastructure", 0.7)]], dtype=torch.float32),
            torch.tensor([[historical_data.get("economic", 0.6)]], dtype=torch.float32),
        ]

        # Temporal features (30-day lookback)
        lookback = 30
        temporal = []

        for _ in range(len(self.temporal_features)):
            # Generate dummy temporal data (in production, fetch real data)
            feature_values = torch.randn(1, lookback, 1) * 0.1 + 0.5
            temporal.append(feature_values)

        return static, temporal

    def predict(
        self,
        lane: tuple[str, str],
        historical_data: dict,
        forecast_date: datetime
    ) -> list[DemandForecast]:
        """Generate demand forecast for a lane"""
        self.model.eval()

        with torch.no_grad():
            static_features, temporal_features = self.prepare_features(
                lane, historical_data, forecast_date
            )

            # Move to device
            static_features = [f.to(self.device) for f in static_features]
            temporal_features = [f.to(self.device) for f in temporal_features]

            predictions, weights = self.model(static_features, temporal_features)

            # Convert to numpy
            predictions = predictions.cpu().numpy()[0]  # (num_quantiles, horizon)

        # Build forecast objects
        forecasts = []
        for day in range(self.model.forecast_horizon):
            forecast = DemandForecast(
                lane=lane,
                date=forecast_date + timedelta(days=day + 1),
                volume_p10=float(predictions[0, day]),
                volume_p50=float(predictions[1, day]),
                volume_p90=float(predictions[2, day]),
                confidence=0.8 - 0.02 * day  # Confidence decreases with horizon
            )
            forecasts.append(forecast)

        return forecasts

    def train(
        self,
        train_loader: torch.utils.data.DataLoader,
        val_loader: torch.utils.data.DataLoader,
        epochs: int = 100,
        learning_rate: float = 0.001
    ):
        """Train the forecasting model"""
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)

        # Quantile loss
        quantiles = [0.1, 0.5, 0.9]

        def quantile_loss(predictions, targets):
            losses = []
            for i, q in enumerate(quantiles):
                errors = targets - predictions[:, i, :]
                losses.append(torch.max(q * errors, (q - 1) * errors).mean())
            return sum(losses)

        best_val_loss = float('inf')

        for epoch in range(epochs):
            self.model.train()
            train_loss = 0

            for batch in train_loader:
                static, temporal, targets = batch
                static = [s.to(self.device) for s in static]
                temporal = [t.to(self.device) for t in temporal]
                targets = targets.to(self.device)

                optimizer.zero_grad()
                predictions, _ = self.model(static, temporal)
                loss = quantile_loss(predictions, targets)
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            # Validation
            self.model.eval()
            val_loss = 0

            with torch.no_grad():
                for batch in val_loader:
                    static, temporal, targets = batch
                    static = [s.to(self.device) for s in static]
                    temporal = [t.to(self.device) for t in temporal]
                    targets = targets.to(self.device)

                    predictions, _ = self.model(static, temporal)
                    loss = quantile_loss(predictions, targets)
                    val_loss += loss.item()

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self.save_model("best_demand_model.pt")

            logger.info(
                "demand_forecaster_epoch",
                epoch=epoch,
                train_loss=train_loss / len(train_loader),
                val_loss=val_loss / len(val_loader)
            )

    def save_model(self, path: str):
        """Save model weights"""
        torch.save(self.model.state_dict(), path)

    def load_model(self, path: str):
        """Load model weights"""
        self.model.load_state_dict(torch.load(path, map_location=self.device))
