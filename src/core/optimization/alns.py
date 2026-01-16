"""
Adaptive Large Neighborhood Search (ALNS) Metaheuristic

ALNS is a powerful metaheuristic that:
1. Uses multiple destroy operators to remove parts of the solution
2. Uses multiple repair operators to rebuild
3. Adaptively selects operators based on their historical performance
4. Accepts worse solutions with simulated annealing probability

This provides significant solution improvement over initial heuristics.
"""
import random
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Callable, Optional
from abc import ABC, abstractmethod
from copy import deepcopy
from uuid import UUID
import structlog

from ..models import Shipment, Carrier, Route, RouteStop

logger = structlog.get_logger()


@dataclass
class ALNSSolution:
    """Solution representation for ALNS"""
    routes: list[Route]
    unassigned: list[int]  # Indices of unassigned shipments
    shipments: list[Shipment]
    total_cost: float = 0.0
    total_distance: float = 0.0

    def copy(self) -> "ALNSSolution":
        return ALNSSolution(
            routes=deepcopy(self.routes),
            unassigned=self.unassigned.copy(),
            shipments=self.shipments,  # Reference, don't copy
            total_cost=self.total_cost,
            total_distance=self.total_distance
        )

    def calculate_cost(self, cost_per_mile: float = 2.5, penalty_per_unassigned: float = 1000):
        """Calculate total solution cost"""
        route_cost = sum(r.total_distance_miles * cost_per_mile for r in self.routes)
        penalty = len(self.unassigned) * penalty_per_unassigned
        self.total_cost = route_cost + penalty
        self.total_distance = sum(r.total_distance_miles for r in self.routes)
        return self.total_cost


# ============= DESTROY OPERATORS =============

class DestroyOperator(ABC):
    """Base class for destroy operators"""

    @abstractmethod
    def __call__(
        self,
        solution: ALNSSolution,
        num_to_remove: int,
        random_state: random.Random
    ) -> tuple[ALNSSolution, list[int]]:
        """Remove shipments from solution, return modified solution and removed indices"""
        pass


class RandomDestroy(DestroyOperator):
    """Randomly remove shipments from routes"""

    def __call__(
        self,
        solution: ALNSSolution,
        num_to_remove: int,
        random_state: random.Random
    ) -> tuple[ALNSSolution, list[int]]:
        sol = solution.copy()
        removed = []

        # Get all assigned shipment indices
        assigned = []
        for route in sol.routes:
            for sid in route.shipment_ids:
                for i, s in enumerate(sol.shipments):
                    if s.id == sid and i not in assigned:
                        assigned.append(i)

        # Randomly select to remove
        num_to_remove = min(num_to_remove, len(assigned))
        to_remove = random_state.sample(assigned, num_to_remove)

        for idx in to_remove:
            shipment_id = sol.shipments[idx].id
            for route in sol.routes:
                if shipment_id in route.shipment_ids:
                    route.shipment_ids.remove(shipment_id)
                    route.stops = [s for s in route.stops if s.shipment_id != shipment_id]
                    break
            removed.append(idx)
            sol.unassigned.append(idx)

        # Remove empty routes
        sol.routes = [r for r in sol.routes if r.shipment_ids]

        return sol, removed


class WorstCostDestroy(DestroyOperator):
    """Remove shipments that contribute most to cost"""

    def __call__(
        self,
        solution: ALNSSolution,
        num_to_remove: int,
        random_state: random.Random
    ) -> tuple[ALNSSolution, list[int]]:
        sol = solution.copy()

        # Calculate marginal cost for each shipment
        marginal_costs = []
        for route in sol.routes:
            for sid in route.shipment_ids:
                for i, s in enumerate(sol.shipments):
                    if s.id == sid:
                        # Estimate marginal cost as distance * rate / num_shipments
                        marginal = route.total_distance_miles * 2.5 / len(route.shipment_ids)
                        marginal_costs.append((i, marginal))
                        break

        # Sort by cost (highest first)
        marginal_costs.sort(key=lambda x: x[1], reverse=True)

        # Remove highest cost shipments
        removed = []
        num_to_remove = min(num_to_remove, len(marginal_costs))

        for idx, _ in marginal_costs[:num_to_remove]:
            if idx in sol.unassigned:
                continue
            shipment_id = sol.shipments[idx].id
            for route in sol.routes:
                if shipment_id in route.shipment_ids:
                    route.shipment_ids.remove(shipment_id)
                    route.stops = [s for s in route.stops if s.shipment_id != shipment_id]
                    break
            removed.append(idx)
            sol.unassigned.append(idx)

        sol.routes = [r for r in sol.routes if r.shipment_ids]
        return sol, removed


class RelatedDestroy(DestroyOperator):
    """Remove geographically related shipments (cluster removal)"""

    def __init__(self, shipments: list[Shipment]):
        self.shipments = shipments
        self._build_relatedness_matrix()

    def _build_relatedness_matrix(self):
        """Build matrix of shipment relatedness based on geography"""
        n = len(self.shipments)
        self.relatedness = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    # Relatedness based on origin-origin and dest-dest distance
                    origin_dist = self.shipments[i].origin.distance_to(self.shipments[j].origin)
                    dest_dist = self.shipments[i].destination.distance_to(self.shipments[j].destination)
                    # Inverse distance as relatedness
                    self.relatedness[i][j] = 1 / (1 + origin_dist + dest_dist)

    def __call__(
        self,
        solution: ALNSSolution,
        num_to_remove: int,
        random_state: random.Random
    ) -> tuple[ALNSSolution, list[int]]:
        sol = solution.copy()

        # Get assigned shipments
        assigned = []
        for route in sol.routes:
            for sid in route.shipment_ids:
                for i, s in enumerate(sol.shipments):
                    if s.id == sid and i not in assigned:
                        assigned.append(i)

        if not assigned:
            return sol, []

        # Start with random shipment
        seed = random_state.choice(assigned)
        removed = [seed]

        # Add related shipments
        while len(removed) < num_to_remove and len(removed) < len(assigned):
            # Find most related unremoved shipment
            best_idx = None
            best_relatedness = -1

            for idx in assigned:
                if idx in removed:
                    continue
                # Sum of relatedness to all removed
                rel = sum(self.relatedness[idx][r] for r in removed)
                if rel > best_relatedness:
                    best_relatedness = rel
                    best_idx = idx

            if best_idx is not None:
                removed.append(best_idx)
            else:
                break

        # Actually remove from solution
        for idx in removed:
            shipment_id = sol.shipments[idx].id
            for route in sol.routes:
                if shipment_id in route.shipment_ids:
                    route.shipment_ids.remove(shipment_id)
                    route.stops = [s for s in route.stops if s.shipment_id != shipment_id]
                    break
            if idx not in sol.unassigned:
                sol.unassigned.append(idx)

        sol.routes = [r for r in sol.routes if r.shipment_ids]
        return sol, removed


# ============= REPAIR OPERATORS =============

class RepairOperator(ABC):
    """Base class for repair operators"""

    @abstractmethod
    def __call__(
        self,
        solution: ALNSSolution,
        random_state: random.Random
    ) -> ALNSSolution:
        """Reinsert unassigned shipments"""
        pass


class GreedyRepair(RepairOperator):
    """Insert shipments at lowest cost position"""

    def __init__(self, carriers: list[Carrier]):
        self.carriers = carriers

    def __call__(
        self,
        solution: ALNSSolution,
        random_state: random.Random
    ) -> ALNSSolution:
        sol = solution.copy()

        while sol.unassigned:
            idx = sol.unassigned[0]
            shipment = sol.shipments[idx]

            best_route_idx = None
            best_cost_increase = float('inf')

            # Try inserting into existing routes
            for route_idx, route in enumerate(sol.routes):
                # Check capacity
                current_feet = sum(
                    sol.shipments[i].dimensions.linear_feet
                    for i, s in enumerate(sol.shipments)
                    if s.id in route.shipment_ids
                )
                if current_feet + shipment.dimensions.linear_feet > 53:
                    continue

                # Estimate cost increase
                # Simplified: just check distance to nearest stop
                if route.stops:
                    min_dist = min(
                        shipment.origin.distance_to(stop.location) +
                        shipment.destination.distance_to(stop.location)
                        for stop in route.stops
                    )
                else:
                    min_dist = shipment.distance_miles

                cost_increase = min_dist * 2.5

                if cost_increase < best_cost_increase:
                    best_cost_increase = cost_increase
                    best_route_idx = route_idx

            if best_route_idx is not None:
                # Insert into existing route
                sol.routes[best_route_idx].shipment_ids.append(shipment.id)
                sol.routes[best_route_idx].total_distance_miles += best_cost_increase / 2.5
            else:
                # Create new route
                new_route = Route(
                    carrier_id=self.carriers[0].id if self.carriers else None,
                    shipment_ids=[shipment.id],
                    total_distance_miles=shipment.distance_miles * 2 + 50,
                    status="planned"
                )
                sol.routes.append(new_route)

            sol.unassigned.remove(idx)

        return sol


class RegretRepair(RepairOperator):
    """
    Regret-2 insertion: Insert shipment with highest regret first

    Regret = (cost of 2nd best insertion) - (cost of best insertion)
    High regret means we should insert this shipment now or pay later
    """

    def __init__(self, carriers: list[Carrier]):
        self.carriers = carriers

    def __call__(
        self,
        solution: ALNSSolution,
        random_state: random.Random
    ) -> ALNSSolution:
        sol = solution.copy()

        while sol.unassigned:
            best_shipment_idx = None
            best_shipment_insertion = None
            highest_regret = -float('inf')

            for idx in sol.unassigned:
                shipment = sol.shipments[idx]

                # Find insertion costs for all routes
                insertion_costs = []

                for route_idx, route in enumerate(sol.routes):
                    current_feet = sum(
                        sol.shipments[i].dimensions.linear_feet
                        for i, s in enumerate(sol.shipments)
                        if s.id in route.shipment_ids
                    )
                    if current_feet + shipment.dimensions.linear_feet > 53:
                        continue

                    if route.stops:
                        min_dist = min(
                            shipment.origin.distance_to(stop.location) +
                            shipment.destination.distance_to(stop.location)
                            for stop in route.stops
                        )
                    else:
                        min_dist = shipment.distance_miles

                    cost = min_dist * 2.5
                    insertion_costs.append((route_idx, cost))

                # Add option for new route
                new_route_cost = (shipment.distance_miles * 2 + 50) * 2.5
                insertion_costs.append((-1, new_route_cost))

                if len(insertion_costs) >= 2:
                    insertion_costs.sort(key=lambda x: x[1])
                    regret = insertion_costs[1][1] - insertion_costs[0][1]
                else:
                    regret = 0

                if regret > highest_regret:
                    highest_regret = regret
                    best_shipment_idx = idx
                    best_shipment_insertion = insertion_costs[0]

            if best_shipment_idx is not None:
                shipment = sol.shipments[best_shipment_idx]
                route_idx, _ = best_shipment_insertion

                if route_idx >= 0:
                    sol.routes[route_idx].shipment_ids.append(shipment.id)
                else:
                    new_route = Route(
                        carrier_id=self.carriers[0].id if self.carriers else None,
                        shipment_ids=[shipment.id],
                        total_distance_miles=shipment.distance_miles * 2 + 50,
                        status="planned"
                    )
                    sol.routes.append(new_route)

                sol.unassigned.remove(best_shipment_idx)
            else:
                break

        return sol


# ============= ALNS ALGORITHM =============

@dataclass
class ALNSConfig:
    """Configuration for ALNS"""
    max_iterations: int = 10000
    max_iterations_no_improvement: int = 1000
    segment_size: int = 100  # Iterations per segment for weight update
    min_removal_pct: float = 0.1
    max_removal_pct: float = 0.4
    reaction_factor: float = 0.1  # Weight update speed

    # Simulated annealing
    initial_temperature: float = 100.0
    cooling_rate: float = 0.9995
    min_temperature: float = 0.01

    # Acceptance scores
    score_best: float = 33.0
    score_better: float = 9.0
    score_accepted: float = 13.0


class ALNS:
    """
    Adaptive Large Neighborhood Search

    Main improvement algorithm for shared truckload routing
    """

    def __init__(
        self,
        shipments: list[Shipment],
        carriers: list[Carrier],
        config: ALNSConfig = None
    ):
        self.shipments = shipments
        self.carriers = carriers
        self.config = config or ALNSConfig()
        self.random = random.Random(42)

        # Initialize operators
        self.destroy_operators: list[DestroyOperator] = [
            RandomDestroy(),
            WorstCostDestroy(),
            RelatedDestroy(shipments)
        ]

        self.repair_operators: list[RepairOperator] = [
            GreedyRepair(carriers),
            RegretRepair(carriers)
        ]

        # Operator weights (adaptive)
        self.destroy_weights = [1.0] * len(self.destroy_operators)
        self.repair_weights = [1.0] * len(self.repair_operators)

        # Scores accumulated during segment
        self.destroy_scores = [0.0] * len(self.destroy_operators)
        self.repair_scores = [0.0] * len(self.repair_operators)
        self.destroy_uses = [0] * len(self.destroy_operators)
        self.repair_uses = [0] * len(self.repair_operators)

    def solve(self, initial_solution: ALNSSolution) -> ALNSSolution:
        """Run ALNS to improve initial solution"""
        logger.info(
            "starting_alns",
            max_iterations=self.config.max_iterations,
            num_shipments=len(self.shipments)
        )

        current = initial_solution.copy()
        current.calculate_cost()

        best = current.copy()
        best_cost = current.total_cost

        temperature = self.config.initial_temperature
        iterations_no_improvement = 0

        for iteration in range(self.config.max_iterations):
            # Select operators
            destroy_idx = self._select_operator(self.destroy_weights)
            repair_idx = self._select_operator(self.repair_weights)

            # Determine number of shipments to remove
            n_assigned = len(self.shipments) - len(current.unassigned)
            min_remove = max(1, int(n_assigned * self.config.min_removal_pct))
            max_remove = max(1, int(n_assigned * self.config.max_removal_pct))
            num_to_remove = self.random.randint(min_remove, max_remove)

            # Apply destroy and repair
            destroyed, removed = self.destroy_operators[destroy_idx](
                current, num_to_remove, self.random
            )
            candidate = self.repair_operators[repair_idx](destroyed, self.random)
            candidate.calculate_cost()

            # Determine acceptance
            self.destroy_uses[destroy_idx] += 1
            self.repair_uses[repair_idx] += 1

            if candidate.total_cost < best_cost:
                # New global best
                best = candidate.copy()
                best_cost = candidate.total_cost
                current = candidate
                iterations_no_improvement = 0

                self.destroy_scores[destroy_idx] += self.config.score_best
                self.repair_scores[repair_idx] += self.config.score_best

                logger.debug(
                    "alns_new_best",
                    iteration=iteration,
                    cost=best_cost
                )

            elif candidate.total_cost < current.total_cost:
                # Better than current
                current = candidate
                self.destroy_scores[destroy_idx] += self.config.score_better
                self.repair_scores[repair_idx] += self.config.score_better

            elif self._accept_worse(candidate.total_cost, current.total_cost, temperature):
                # Accept worse with SA probability
                current = candidate
                self.destroy_scores[destroy_idx] += self.config.score_accepted
                self.repair_scores[repair_idx] += self.config.score_accepted

            else:
                iterations_no_improvement += 1

            # Update temperature
            temperature = max(
                self.config.min_temperature,
                temperature * self.config.cooling_rate
            )

            # Update weights at end of segment
            if (iteration + 1) % self.config.segment_size == 0:
                self._update_weights()

            # Early termination
            if iterations_no_improvement >= self.config.max_iterations_no_improvement:
                logger.info(
                    "alns_early_termination",
                    iteration=iteration,
                    reason="no_improvement"
                )
                break

        logger.info(
            "alns_complete",
            final_cost=best_cost,
            initial_cost=initial_solution.total_cost,
            improvement_pct=(initial_solution.total_cost - best_cost) / initial_solution.total_cost * 100
        )

        return best

    def _select_operator(self, weights: list[float]) -> int:
        """Roulette wheel selection based on weights"""
        total = sum(weights)
        r = self.random.random() * total
        cumulative = 0
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                return i
        return len(weights) - 1

    def _accept_worse(self, candidate_cost: float, current_cost: float, temperature: float) -> bool:
        """Simulated annealing acceptance criterion"""
        if temperature <= 0:
            return False
        delta = candidate_cost - current_cost
        probability = math.exp(-delta / temperature)
        return self.random.random() < probability

    def _update_weights(self):
        """Update operator weights based on performance"""
        for i in range(len(self.destroy_operators)):
            if self.destroy_uses[i] > 0:
                score = self.destroy_scores[i] / self.destroy_uses[i]
                self.destroy_weights[i] = (
                    self.destroy_weights[i] * (1 - self.config.reaction_factor) +
                    score * self.config.reaction_factor
                )
            self.destroy_scores[i] = 0
            self.destroy_uses[i] = 0

        for i in range(len(self.repair_operators)):
            if self.repair_uses[i] > 0:
                score = self.repair_scores[i] / self.repair_uses[i]
                self.repair_weights[i] = (
                    self.repair_weights[i] * (1 - self.config.reaction_factor) +
                    score * self.config.reaction_factor
                )
            self.repair_scores[i] = 0
            self.repair_uses[i] = 0

        logger.debug(
            "alns_weights_updated",
            destroy_weights=self.destroy_weights,
            repair_weights=self.repair_weights
        )
