"""
Pooling Prediction Model

Uses Graph Neural Networks to predict the probability of successful
pooling between shipments. This is key for:
- Real-time pooling decisions
- Pricing (higher pooling prob = lower price)
- Capacity planning

The GNN captures the complex relationships between shipments in
the pooling network.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class ShipmentFeatures:
    """Features extracted from a shipment for pooling prediction"""
    # Geographic
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float
    distance_miles: float

    # Temporal
    pickup_window_start: float  # Hours from now
    pickup_window_end: float
    delivery_window_start: float
    delivery_window_end: float
    time_flexibility: float

    # Physical
    weight_lbs: float
    linear_feet: float
    pallet_count: int
    stackable: bool

    # Requirements
    equipment_type: int  # Encoded
    commodity_type: int
    requires_liftgate: bool
    requires_appointment: bool

    def to_tensor(self) -> torch.Tensor:
        """Convert to normalized tensor"""
        return torch.tensor([
            self.origin_lat / 90,
            self.origin_lon / 180,
            self.dest_lat / 90,
            self.dest_lon / 180,
            min(self.distance_miles / 1000, 1),
            min(self.pickup_window_start / 72, 1),
            min(self.pickup_window_end / 72, 1),
            min(self.delivery_window_start / 168, 1),
            min(self.delivery_window_end / 168, 1),
            min(self.time_flexibility / 72, 1),
            min(self.weight_lbs / 45000, 1),
            min(self.linear_feet / 53, 1),
            min(self.pallet_count / 26, 1),
            float(self.stackable),
            self.equipment_type / 4,
            self.commodity_type / 6,
            float(self.requires_liftgate),
            float(self.requires_appointment)
        ], dtype=torch.float32)


@dataclass
class PoolingPrediction:
    """Prediction output for a pair of shipments"""
    shipment_1_id: str
    shipment_2_id: str
    pooling_probability: float
    compatibility_score: float
    estimated_savings_pct: float
    confidence: float
    factors: dict


class GraphConvolutionLayer(nn.Module):
    """
    Graph Convolution Layer for shipment network

    Aggregates information from neighboring shipments
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        aggregation: str = "mean"
    ):
        super().__init__()

        self.in_features = in_features
        self.out_features = out_features
        self.aggregation = aggregation

        # Transformation matrices
        self.W_self = nn.Linear(in_features, out_features)
        self.W_neighbor = nn.Linear(in_features, out_features)

        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Linear(2 * out_features, out_features),
            nn.ReLU(),
            nn.Linear(out_features, 1)
        )

    def forward(
        self,
        node_features: torch.Tensor,
        adjacency: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            node_features: (batch, num_nodes, in_features)
            adjacency: (batch, num_nodes, num_nodes) - edge weights

        Returns:
            updated_features: (batch, num_nodes, out_features)
        """
        batch_size, num_nodes, _ = node_features.shape

        # Self transformation
        h_self = self.W_self(node_features)

        # Neighbor transformation
        h_neighbor = self.W_neighbor(node_features)

        # Attention-weighted aggregation
        # Expand for pairwise attention computation
        h_i = h_self.unsqueeze(2).expand(-1, -1, num_nodes, -1)
        h_j = h_neighbor.unsqueeze(1).expand(-1, num_nodes, -1, -1)

        # Concatenate for attention
        h_concat = torch.cat([h_i, h_j], dim=-1)
        attention_scores = self.attention(h_concat).squeeze(-1)

        # Mask with adjacency (only attend to connected nodes)
        attention_scores = attention_scores.masked_fill(adjacency == 0, -1e9)
        attention_weights = F.softmax(attention_scores, dim=-1)

        # Apply attention to neighbor features
        h_neighbor_weighted = torch.bmm(attention_weights, h_neighbor)

        # Combine self and neighbor information
        output = F.relu(h_self + h_neighbor_weighted)

        return output


class EdgePredictor(nn.Module):
    """
    Predicts edge probability (pooling compatibility) between nodes
    """

    def __init__(self, node_features: int, hidden_dim: int = 128):
        super().__init__()

        self.edge_mlp = nn.Sequential(
            nn.Linear(2 * node_features + 4, hidden_dim),  # +4 for edge features
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def forward(
        self,
        node_features: torch.Tensor,
        edge_features: torch.Tensor,
        node_pairs: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            node_features: (batch, num_nodes, features)
            edge_features: (batch, num_pairs, 4) - distance, time overlap, etc.
            node_pairs: (batch, num_pairs, 2) - indices of node pairs

        Returns:
            probabilities: (batch, num_pairs)
        """
        batch_size = node_features.shape[0]
        num_pairs = node_pairs.shape[1]

        # Gather node features for each pair
        # This is a bit complex due to batching
        features_i = []
        features_j = []

        for b in range(batch_size):
            idx_i = node_pairs[b, :, 0]
            idx_j = node_pairs[b, :, 1]
            features_i.append(node_features[b, idx_i])
            features_j.append(node_features[b, idx_j])

        features_i = torch.stack(features_i)  # (batch, num_pairs, features)
        features_j = torch.stack(features_j)

        # Concatenate node and edge features
        pair_features = torch.cat([features_i, features_j, edge_features], dim=-1)

        # Predict probability
        probabilities = self.edge_mlp(pair_features).squeeze(-1)

        return probabilities


class PoolingGNN(nn.Module):
    """
    Graph Neural Network for Pooling Prediction

    Architecture:
    1. Node embedding layer
    2. Multiple graph convolution layers
    3. Edge prediction layer

    The model learns which shipment pairs can be efficiently pooled.
    """

    def __init__(
        self,
        input_dim: int = 18,
        hidden_dim: int = 128,
        num_layers: int = 3,
        dropout: float = 0.2
    ):
        super().__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim

        # Initial embedding
        self.node_embedding = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        # Graph convolution layers
        self.conv_layers = nn.ModuleList([
            GraphConvolutionLayer(hidden_dim, hidden_dim)
            for _ in range(num_layers)
        ])

        # Layer normalization
        self.layer_norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim)
            for _ in range(num_layers)
        ])

        # Edge predictor
        self.edge_predictor = EdgePredictor(hidden_dim, hidden_dim)

        # Dropout
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        node_features: torch.Tensor,
        adjacency: torch.Tensor,
        edge_features: torch.Tensor,
        node_pairs: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            node_features: (batch, num_nodes, input_dim)
            adjacency: (batch, num_nodes, num_nodes)
            edge_features: (batch, num_pairs, 4)
            node_pairs: (batch, num_pairs, 2)

        Returns:
            pooling_probabilities: (batch, num_pairs)
        """
        # Embed nodes
        h = self.node_embedding(node_features)

        # Apply graph convolutions with residual connections
        for conv, norm in zip(self.conv_layers, self.layer_norms):
            h_new = conv(h, adjacency)
            h_new = self.dropout(h_new)
            h = norm(h + h_new)  # Residual connection

        # Predict edge probabilities
        probabilities = self.edge_predictor(h, edge_features, node_pairs)

        return probabilities


class PoolingPredictor:
    """
    High-level interface for pooling prediction

    Features:
    - Batch prediction for efficiency
    - Feature engineering for shipment pairs
    - Confidence estimation
    - Explanation of pooling factors
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        self.model = PoolingGNN().to(device)

        if model_path:
            self.load_model(model_path)

    def compute_edge_features(
        self,
        shipment_1: ShipmentFeatures,
        shipment_2: ShipmentFeatures
    ) -> torch.Tensor:
        """Compute features for the edge between two shipments"""
        # Geographic compatibility
        # Origin-to-origin and dest-to-dest distances
        from math import radians, cos, sin, asin, sqrt

        def haversine(lat1, lon1, lat2, lon2):
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            return 2 * 3956 * asin(sqrt(a))

        origin_distance = haversine(
            shipment_1.origin_lat, shipment_1.origin_lon,
            shipment_2.origin_lat, shipment_2.origin_lon
        )
        dest_distance = haversine(
            shipment_1.dest_lat, shipment_1.dest_lon,
            shipment_2.dest_lat, shipment_2.dest_lon
        )

        # Time window overlap
        pickup_overlap = max(0, min(shipment_1.pickup_window_end, shipment_2.pickup_window_end) -
                           max(shipment_1.pickup_window_start, shipment_2.pickup_window_start))

        delivery_overlap = max(0, min(shipment_1.delivery_window_end, shipment_2.delivery_window_end) -
                              max(shipment_1.delivery_window_start, shipment_2.delivery_window_start))

        return torch.tensor([
            min(origin_distance / 100, 1),
            min(dest_distance / 100, 1),
            min(pickup_overlap / 24, 1),
            min(delivery_overlap / 48, 1)
        ], dtype=torch.float32)

    def predict_pair(
        self,
        shipment_1: ShipmentFeatures,
        shipment_2: ShipmentFeatures
    ) -> PoolingPrediction:
        """Predict pooling probability for a single pair"""
        self.model.eval()

        with torch.no_grad():
            # Build mini-graph with 2 nodes
            node_features = torch.stack([
                shipment_1.to_tensor(),
                shipment_2.to_tensor()
            ]).unsqueeze(0).to(self.device)

            # Simple adjacency (fully connected)
            adjacency = torch.ones(1, 2, 2).to(self.device)

            # Edge features
            edge_features = self.compute_edge_features(shipment_1, shipment_2)
            edge_features = edge_features.unsqueeze(0).unsqueeze(0).to(self.device)

            # Node pairs (just one pair)
            node_pairs = torch.tensor([[[0, 1]]]).to(self.device)

            # Predict
            probability = self.model(
                node_features, adjacency, edge_features, node_pairs
            ).cpu().item()

        # Calculate additional metrics
        compatibility_score = self._compute_compatibility_score(shipment_1, shipment_2)
        estimated_savings = self._estimate_savings(shipment_1, shipment_2, probability)
        factors = self._explain_factors(shipment_1, shipment_2)

        return PoolingPrediction(
            shipment_1_id="",  # To be filled by caller
            shipment_2_id="",
            pooling_probability=probability,
            compatibility_score=compatibility_score,
            estimated_savings_pct=estimated_savings,
            confidence=min(0.95, probability + 0.1) if probability > 0.5 else max(0.05, probability - 0.1),
            factors=factors
        )

    def predict_batch(
        self,
        shipments: List[ShipmentFeatures],
        max_pairs: int = 1000
    ) -> List[PoolingPrediction]:
        """Predict pooling probabilities for all pairs in a batch"""
        self.model.eval()
        n = len(shipments)

        if n < 2:
            return []

        with torch.no_grad():
            # Build node features
            node_features = torch.stack([s.to_tensor() for s in shipments])
            node_features = node_features.unsqueeze(0).to(self.device)

            # Build adjacency (start fully connected, will be learned)
            adjacency = torch.ones(1, n, n).to(self.device)

            # Build all pairs and edge features
            pairs = []
            edge_feats = []

            for i in range(n):
                for j in range(i + 1, n):
                    pairs.append([i, j])
                    edge_feats.append(
                        self.compute_edge_features(shipments[i], shipments[j])
                    )

                    if len(pairs) >= max_pairs:
                        break
                if len(pairs) >= max_pairs:
                    break

            if not pairs:
                return []

            node_pairs = torch.tensor([pairs]).to(self.device)
            edge_features = torch.stack(edge_feats).unsqueeze(0).to(self.device)

            # Predict all at once
            probabilities = self.model(
                node_features, adjacency, edge_features, node_pairs
            ).cpu().numpy()[0]

        # Build predictions
        predictions = []
        for idx, (i, j) in enumerate(pairs):
            prob = float(probabilities[idx])

            compatibility = self._compute_compatibility_score(shipments[i], shipments[j])
            savings = self._estimate_savings(shipments[i], shipments[j], prob)

            pred = PoolingPrediction(
                shipment_1_id=str(i),
                shipment_2_id=str(j),
                pooling_probability=prob,
                compatibility_score=compatibility,
                estimated_savings_pct=savings,
                confidence=min(0.95, prob + 0.1) if prob > 0.5 else max(0.05, prob - 0.1),
                factors={}
            )
            predictions.append(pred)

        # Sort by probability descending
        predictions.sort(key=lambda x: x.pooling_probability, reverse=True)

        return predictions

    def _compute_compatibility_score(
        self,
        s1: ShipmentFeatures,
        s2: ShipmentFeatures
    ) -> float:
        """Compute rule-based compatibility score"""
        score = 1.0

        # Equipment match
        if s1.equipment_type != s2.equipment_type:
            score *= 0.0  # Must match
            return score

        # Commodity compatibility
        if s1.commodity_type != s2.commodity_type:
            score *= 0.8  # Slight penalty

        # Capacity fit
        total_feet = s1.linear_feet + s2.linear_feet
        if total_feet > 53:
            score *= 0.0
            return score

        total_weight = s1.weight_lbs + s2.weight_lbs
        if total_weight > 45000:
            score *= 0.0
            return score

        # Utilization bonus
        utilization = total_feet / 53
        if 0.7 <= utilization <= 0.95:
            score *= 1.1  # Bonus for good utilization

        return min(score, 1.0)

    def _estimate_savings(
        self,
        s1: ShipmentFeatures,
        s2: ShipmentFeatures,
        probability: float
    ) -> float:
        """Estimate cost savings from pooling"""
        # Base savings from shared distance
        # Simplified: assume 30% of longer distance is shared
        max_dist = max(s1.distance_miles, s2.distance_miles)
        min_dist = min(s1.distance_miles, s2.distance_miles)

        shared_fraction = min_dist / max_dist if max_dist > 0 else 0
        base_savings = shared_fraction * 30  # Up to 30% savings

        # Adjust by probability
        expected_savings = base_savings * probability

        return min(expected_savings, 40)  # Cap at 40%

    def _explain_factors(
        self,
        s1: ShipmentFeatures,
        s2: ShipmentFeatures
    ) -> dict:
        """Generate human-readable explanation of pooling factors"""
        factors = {}

        # Geographic
        from math import radians, cos, sin, asin, sqrt

        def haversine(lat1, lon1, lat2, lon2):
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            return 2 * 3956 * asin(sqrt(a))

        origin_dist = haversine(s1.origin_lat, s1.origin_lon, s2.origin_lat, s2.origin_lon)
        dest_dist = haversine(s1.dest_lat, s1.dest_lon, s2.dest_lat, s2.dest_lon)

        factors["origin_proximity"] = "excellent" if origin_dist < 25 else "good" if origin_dist < 50 else "fair"
        factors["destination_proximity"] = "excellent" if dest_dist < 25 else "good" if dest_dist < 50 else "fair"

        # Temporal
        pickup_overlap = max(0, min(s1.pickup_window_end, s2.pickup_window_end) -
                           max(s1.pickup_window_start, s2.pickup_window_start))
        factors["time_window_overlap"] = "high" if pickup_overlap > 4 else "medium" if pickup_overlap > 2 else "low"

        # Capacity
        total_feet = s1.linear_feet + s2.linear_feet
        factors["capacity_utilization"] = f"{total_feet / 53 * 100:.0f}%"

        # Equipment
        factors["equipment_match"] = "yes" if s1.equipment_type == s2.equipment_type else "no"

        return factors

    def train(
        self,
        train_loader: torch.utils.data.DataLoader,
        val_loader: torch.utils.data.DataLoader,
        epochs: int = 100,
        learning_rate: float = 0.001
    ):
        """Train the pooling prediction model"""
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.BCELoss()

        best_val_auc = 0

        for epoch in range(epochs):
            self.model.train()
            train_loss = 0

            for batch in train_loader:
                node_features, adjacency, edge_features, node_pairs, labels = batch

                node_features = node_features.to(self.device)
                adjacency = adjacency.to(self.device)
                edge_features = edge_features.to(self.device)
                node_pairs = node_pairs.to(self.device)
                labels = labels.to(self.device)

                optimizer.zero_grad()

                predictions = self.model(node_features, adjacency, edge_features, node_pairs)
                loss = criterion(predictions, labels)

                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            # Validation
            self.model.eval()
            val_predictions = []
            val_labels = []

            with torch.no_grad():
                for batch in val_loader:
                    node_features, adjacency, edge_features, node_pairs, labels = batch

                    node_features = node_features.to(self.device)
                    adjacency = adjacency.to(self.device)
                    edge_features = edge_features.to(self.device)
                    node_pairs = node_pairs.to(self.device)

                    predictions = self.model(node_features, adjacency, edge_features, node_pairs)

                    val_predictions.extend(predictions.cpu().numpy().flatten())
                    val_labels.extend(labels.numpy().flatten())

            # Calculate AUC
            from sklearn.metrics import roc_auc_score
            try:
                val_auc = roc_auc_score(val_labels, val_predictions)
            except:
                val_auc = 0.5

            if val_auc > best_val_auc:
                best_val_auc = val_auc
                self.save_model("best_pooling_model.pt")

            logger.info(
                "pooling_predictor_epoch",
                epoch=epoch,
                train_loss=train_loss / len(train_loader),
                val_auc=val_auc
            )

    def save_model(self, path: str):
        """Save model weights"""
        torch.save(self.model.state_dict(), path)

    def load_model(self, path: str):
        """Load model weights"""
        self.model.load_state_dict(torch.load(path, map_location=self.device))
