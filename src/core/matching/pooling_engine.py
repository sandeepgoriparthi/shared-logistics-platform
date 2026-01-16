"""
Pooling Engine

Core engine for finding and executing shipment pooling opportunities.
Combines ML predictions with optimization algorithms.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import structlog

from ..models import Shipment, Carrier, Route, PoolingOpportunity
from ..optimization import VRPTWSolver, VRPTWInstance, ALNS, ALNSSolution, ALNSConfig
from ..optimization import ColumnGenerationSolver

logger = structlog.get_logger()


@dataclass
class PoolingConfig:
    """Configuration for pooling engine"""
    # Matching thresholds
    max_origin_distance_miles: float = 50.0
    max_dest_distance_miles: float = 50.0
    min_time_overlap_hours: float = 2.0
    max_shipments_per_pool: int = 4

    # Capacity constraints
    max_total_weight_lbs: float = 45000.0
    max_total_linear_feet: float = 53.0
    target_utilization_min: float = 0.7
    target_utilization_max: float = 0.95

    # Savings thresholds
    min_savings_percent: float = 10.0
    min_pooling_probability: float = 0.5

    # Optimization
    use_ml_predictions: bool = True
    use_advanced_optimization: bool = True
    optimization_time_limit: int = 30


@dataclass
class PoolingResult:
    """Result from pooling optimization"""
    opportunities: List[PoolingOpportunity]
    total_potential_savings: float
    average_savings_percent: float
    shipments_pooled: int
    shipments_unpooled: int
    computation_time_seconds: float


class PoolingEngine:
    """
    Main pooling engine that finds optimal shipment combinations

    Pipeline:
    1. Filter eligible shipments
    2. Build compatibility graph
    3. Use ML to predict pooling probability
    4. Find optimal pooling combinations
    5. Optimize routes for each pool
    """

    def __init__(
        self,
        config: PoolingConfig = None,
        pooling_predictor = None,
        demand_forecaster = None
    ):
        self.config = config or PoolingConfig()
        self.pooling_predictor = pooling_predictor
        self.demand_forecaster = demand_forecaster

        # Initialize optimizers
        self.vrptw_solver = VRPTWSolver(
            time_limit_seconds=self.config.optimization_time_limit
        )
        self.column_gen_solver = ColumnGenerationSolver(
            max_iterations=100,
            time_limit_seconds=self.config.optimization_time_limit
        )

    def find_pooling_opportunities(
        self,
        shipments: List[Shipment],
        carriers: List[Carrier]
    ) -> PoolingResult:
        """
        Find all pooling opportunities for a set of shipments

        Returns ranked list of potential pools with estimated savings.
        """
        import time
        start_time = time.time()

        logger.info(
            "finding_pooling_opportunities",
            num_shipments=len(shipments),
            num_carriers=len(carriers)
        )

        if len(shipments) < 2:
            return PoolingResult(
                opportunities=[],
                total_potential_savings=0,
                average_savings_percent=0,
                shipments_pooled=0,
                shipments_unpooled=len(shipments),
                computation_time_seconds=time.time() - start_time
            )

        # Step 1: Build compatibility graph
        compatibility_matrix = self._build_compatibility_matrix(shipments)

        # Step 2: Find candidate pools using graph clustering
        candidate_pools = self._find_candidate_pools(shipments, compatibility_matrix)

        # Step 3: Evaluate and optimize each pool
        opportunities = []

        for pool_indices in candidate_pools:
            pool_shipments = [shipments[i] for i in pool_indices]

            # Check constraints
            if not self._check_pool_constraints(pool_shipments):
                continue

            # Predict pooling probability with ML
            if self.config.use_ml_predictions and self.pooling_predictor:
                probability = self._predict_pooling_probability(pool_shipments)
            else:
                probability = self._estimate_pooling_probability(pool_shipments)

            if probability < self.config.min_pooling_probability:
                continue

            # Calculate savings
            individual_cost = self._calculate_individual_cost(pool_shipments)
            pooled_cost, optimized_route = self._calculate_pooled_cost(
                pool_shipments, carriers
            )

            savings = individual_cost - pooled_cost
            savings_percent = (savings / individual_cost) * 100 if individual_cost > 0 else 0

            if savings_percent < self.config.min_savings_percent:
                continue

            # Create opportunity
            opportunity = PoolingOpportunity(
                shipment_ids=[s.id for s in pool_shipments],
                geographic_score=self._calculate_geographic_score(pool_shipments),
                temporal_score=self._calculate_temporal_score(pool_shipments),
                capacity_score=self._calculate_capacity_score(pool_shipments),
                overall_score=probability,
                individual_cost=individual_cost,
                pooled_cost=pooled_cost,
                savings_percent=savings_percent,
                optimized_route=optimized_route
            )

            opportunities.append(opportunity)

        # Sort by savings
        opportunities.sort(key=lambda x: x.savings_percent, reverse=True)

        # Calculate summary
        total_savings = sum(o.total_savings for o in opportunities)
        avg_savings = (
            sum(o.savings_percent for o in opportunities) / len(opportunities)
            if opportunities else 0
        )
        pooled_shipment_ids = set()
        for o in opportunities:
            pooled_shipment_ids.update(o.shipment_ids)

        computation_time = time.time() - start_time

        logger.info(
            "pooling_opportunities_found",
            num_opportunities=len(opportunities),
            total_savings=total_savings,
            avg_savings_percent=avg_savings,
            computation_time=computation_time
        )

        return PoolingResult(
            opportunities=opportunities,
            total_potential_savings=total_savings,
            average_savings_percent=avg_savings,
            shipments_pooled=len(pooled_shipment_ids),
            shipments_unpooled=len(shipments) - len(pooled_shipment_ids),
            computation_time_seconds=computation_time
        )

    def _build_compatibility_matrix(
        self,
        shipments: List[Shipment]
    ) -> np.ndarray:
        """Build pairwise compatibility matrix"""
        n = len(shipments)
        matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                s1, s2 = shipments[i], shipments[j]

                # Check equipment compatibility
                if s1.equipment_required != s2.equipment_required:
                    continue

                # Check geographic compatibility
                origin_dist = s1.origin.distance_to(s2.origin)
                dest_dist = s1.destination.distance_to(s2.destination)

                if origin_dist > self.config.max_origin_distance_miles:
                    continue
                if dest_dist > self.config.max_dest_distance_miles:
                    continue

                # Check time window overlap
                pickup_overlap = s1.pickup_window.intersection(s2.pickup_window)
                if pickup_overlap is None or pickup_overlap.duration_hours < self.config.min_time_overlap_hours:
                    continue

                # Check capacity
                total_feet = s1.dimensions.linear_feet + s2.dimensions.linear_feet
                total_weight = s1.dimensions.weight_lbs + s2.dimensions.weight_lbs

                if total_feet > self.config.max_total_linear_feet:
                    continue
                if total_weight > self.config.max_total_weight_lbs:
                    continue

                # Calculate compatibility score
                geo_score = 1 - (origin_dist + dest_dist) / (2 * self.config.max_origin_distance_miles)
                time_score = pickup_overlap.duration_hours / max(
                    s1.pickup_window.duration_hours,
                    s2.pickup_window.duration_hours
                )

                utilization = total_feet / self.config.max_total_linear_feet
                if self.config.target_utilization_min <= utilization <= self.config.target_utilization_max:
                    cap_score = 1.0
                else:
                    cap_score = 0.5

                compatibility = 0.4 * geo_score + 0.3 * time_score + 0.3 * cap_score

                matrix[i, j] = compatibility
                matrix[j, i] = compatibility

        return matrix

    def _find_candidate_pools(
        self,
        shipments: List[Shipment],
        compatibility_matrix: np.ndarray
    ) -> List[List[int]]:
        """Find candidate pools using greedy clustering"""
        n = len(shipments)
        pools = []
        used = set()

        # Sort shipments by number of compatible partners (descending)
        compatibility_counts = [
            (i, np.sum(compatibility_matrix[i] > 0))
            for i in range(n)
        ]
        compatibility_counts.sort(key=lambda x: x[1], reverse=True)

        for seed_idx, _ in compatibility_counts:
            if seed_idx in used:
                continue

            pool = [seed_idx]
            used.add(seed_idx)

            # Find compatible shipments to add
            candidates = [
                (j, compatibility_matrix[seed_idx, j])
                for j in range(n)
                if j not in used and compatibility_matrix[seed_idx, j] > 0
            ]
            candidates.sort(key=lambda x: x[1], reverse=True)

            for candidate_idx, _ in candidates:
                if len(pool) >= self.config.max_shipments_per_pool:
                    break

                # Check compatibility with all current pool members
                all_compatible = all(
                    compatibility_matrix[candidate_idx, member] > 0
                    for member in pool
                )

                if all_compatible:
                    # Check combined constraints
                    pool_shipments = [shipments[i] for i in pool + [candidate_idx]]
                    if self._check_pool_constraints(pool_shipments):
                        pool.append(candidate_idx)
                        used.add(candidate_idx)

            if len(pool) >= 2:
                pools.append(pool)

        return pools

    def _check_pool_constraints(self, pool_shipments: List[Shipment]) -> bool:
        """Check if pool satisfies all constraints"""
        # Capacity
        total_feet = sum(s.dimensions.linear_feet for s in pool_shipments)
        total_weight = sum(s.dimensions.weight_lbs for s in pool_shipments)

        if total_feet > self.config.max_total_linear_feet:
            return False
        if total_weight > self.config.max_total_weight_lbs:
            return False

        # Equipment
        equipment_types = set(s.equipment_required for s in pool_shipments)
        if len(equipment_types) > 1:
            return False

        return True

    def _predict_pooling_probability(
        self,
        pool_shipments: List[Shipment]
    ) -> float:
        """Use ML model to predict pooling probability"""
        if self.pooling_predictor is None:
            return self._estimate_pooling_probability(pool_shipments)

        # Would call actual ML model here
        # For now, use heuristic
        return self._estimate_pooling_probability(pool_shipments)

    def _estimate_pooling_probability(
        self,
        pool_shipments: List[Shipment]
    ) -> float:
        """Heuristic estimation of pooling probability"""
        geo_score = self._calculate_geographic_score(pool_shipments)
        time_score = self._calculate_temporal_score(pool_shipments)
        cap_score = self._calculate_capacity_score(pool_shipments)

        return 0.4 * geo_score + 0.3 * time_score + 0.3 * cap_score

    def _calculate_geographic_score(
        self,
        pool_shipments: List[Shipment]
    ) -> float:
        """Calculate geographic compatibility score"""
        if len(pool_shipments) < 2:
            return 1.0

        origin_distances = []
        dest_distances = []

        for i, s1 in enumerate(pool_shipments):
            for s2 in pool_shipments[i+1:]:
                origin_distances.append(s1.origin.distance_to(s2.origin))
                dest_distances.append(s1.destination.distance_to(s2.destination))

        avg_origin = np.mean(origin_distances)
        avg_dest = np.mean(dest_distances)

        score = 1 - (avg_origin + avg_dest) / (2 * self.config.max_origin_distance_miles)
        return max(0, min(1, score))

    def _calculate_temporal_score(
        self,
        pool_shipments: List[Shipment]
    ) -> float:
        """Calculate time window compatibility score"""
        if len(pool_shipments) < 2:
            return 1.0

        # Find common pickup window
        common_earliest = max(s.pickup_window.earliest for s in pool_shipments)
        common_latest = min(s.pickup_window.latest for s in pool_shipments)

        if common_earliest >= common_latest:
            return 0.0

        common_duration = (common_latest - common_earliest).total_seconds() / 3600
        max_duration = max(s.pickup_window.duration_hours for s in pool_shipments)

        return common_duration / max_duration if max_duration > 0 else 0

    def _calculate_capacity_score(
        self,
        pool_shipments: List[Shipment]
    ) -> float:
        """Calculate capacity utilization score"""
        total_feet = sum(s.dimensions.linear_feet for s in pool_shipments)
        utilization = total_feet / self.config.max_total_linear_feet

        if self.config.target_utilization_min <= utilization <= self.config.target_utilization_max:
            return 1.0
        elif utilization > self.config.target_utilization_max:
            return 0.5
        else:
            return utilization / self.config.target_utilization_min

    def _calculate_individual_cost(
        self,
        pool_shipments: List[Shipment]
    ) -> float:
        """Calculate cost if shipments were shipped individually"""
        cost_per_mile = 2.50
        return sum(
            s.distance_miles * cost_per_mile + 50  # Plus deadhead
            for s in pool_shipments
        )

    def _calculate_pooled_cost(
        self,
        pool_shipments: List[Shipment],
        carriers: List[Carrier]
    ) -> Tuple[float, Optional[Route]]:
        """Calculate cost if shipments were pooled"""
        if self.config.use_advanced_optimization and len(pool_shipments) > 2:
            # Use VRPTW solver for optimal route
            instance = VRPTWInstance(
                shipments=pool_shipments,
                carriers=carriers[:10],  # Limit carriers
                depot_location=pool_shipments[0].origin
            )
            solution = self.vrptw_solver.solve(instance)

            if solution.routes:
                route = solution.routes[0]
                return route.total_distance_miles * 2.50, route

        # Simple estimation
        # Pooled route is roughly 70% of sum of individual distances
        total_individual_distance = sum(s.distance_miles for s in pool_shipments)
        pooled_distance = total_individual_distance * 0.7

        return pooled_distance * 2.50 + 50, None
