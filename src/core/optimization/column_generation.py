"""
Column Generation Algorithm for Large-Scale Shared Truckload Optimization

Column Generation decomposes the problem into:
- Master Problem: Select the best subset of routes (set covering)
- Subproblem: Generate new promising routes (shortest path with resource constraints)

This allows solving problems with millions of potential routes efficiently.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
import heapq
import structlog

from ..models import Shipment, Carrier, Route, Location

logger = structlog.get_logger()


@dataclass
class Column:
    """A column represents a feasible route"""
    id: int
    shipment_indices: list[int]
    cost: float
    distance: float
    duration: float
    utilization: float
    reduced_cost: float = 0.0

    @property
    def num_shipments(self) -> int:
        return len(self.shipment_indices)


@dataclass
class MasterProblemSolution:
    """Solution from master problem"""
    selected_columns: list[int]
    dual_values: np.ndarray
    objective_value: float


@dataclass
class ColumnGenerationResult:
    """Final result from column generation"""
    selected_routes: list[Route]
    total_cost: float
    total_distance: float
    unassigned_shipments: list[int]
    iterations: int
    gap: float


class SetCoveringMasterProblem:
    """
    Master Problem: Set Covering/Partitioning formulation

    Minimize sum(c_k * y_k) for all routes k
    Subject to:
        sum(a_ik * y_k) >= 1 for all shipments i  (each shipment covered)
        y_k in {0, 1}

    We solve LP relaxation and use dual values to price new columns.
    """

    def __init__(self, num_shipments: int):
        self.num_shipments = num_shipments
        self.columns: list[Column] = []
        self.A: list[list[int]] = []  # Coefficient matrix
        self.costs: list[float] = []

    def add_column(self, column: Column):
        """Add a new column (route) to the master problem"""
        self.columns.append(column)
        self.costs.append(column.cost)

        # Build coefficient row
        coeffs = [0] * self.num_shipments
        for idx in column.shipment_indices:
            if idx < self.num_shipments:
                coeffs[idx] = 1
        self.A.append(coeffs)

    def solve_lp_relaxation(self) -> MasterProblemSolution:
        """
        Solve LP relaxation using revised simplex method

        For production, use scipy.optimize.linprog or PuLP/Gurobi
        Here we implement a simplified version for demonstration
        """
        if not self.columns:
            return MasterProblemSolution(
                selected_columns=[],
                dual_values=np.zeros(self.num_shipments),
                objective_value=float('inf')
            )

        num_columns = len(self.columns)

        # Convert to numpy arrays
        A = np.array(self.A).T  # Transpose: shipments x columns
        c = np.array(self.costs)

        # Simple heuristic LP solution using greedy approach
        # In production, use proper LP solver
        selected = []
        covered = np.zeros(self.num_shipments, dtype=bool)
        dual_values = np.zeros(self.num_shipments)
        total_cost = 0

        # Greedy selection based on cost per uncovered shipment
        remaining_columns = list(range(num_columns))

        while not all(covered) and remaining_columns:
            best_col = None
            best_ratio = float('inf')

            for col_idx in remaining_columns:
                col = self.columns[col_idx]
                # Count how many new shipments this column covers
                new_coverage = sum(
                    1 for i in col.shipment_indices
                    if i < self.num_shipments and not covered[i]
                )
                if new_coverage > 0:
                    ratio = col.cost / new_coverage
                    if ratio < best_ratio:
                        best_ratio = ratio
                        best_col = col_idx

            if best_col is not None:
                selected.append(best_col)
                col = self.columns[best_col]
                total_cost += col.cost

                # Update coverage and estimate dual values
                for i in col.shipment_indices:
                    if i < self.num_shipments and not covered[i]:
                        covered[i] = True
                        dual_values[i] = col.cost / col.num_shipments

                remaining_columns.remove(best_col)
            else:
                break

        return MasterProblemSolution(
            selected_columns=selected,
            dual_values=dual_values,
            objective_value=total_cost
        )

    def solve_ip(self, selected_columns: list[int]) -> list[int]:
        """
        Solve Integer Program using the LP solution as starting point

        For large instances, use branch-and-bound or branch-and-price
        """
        # For now, return LP solution (greedy is already integral)
        return selected_columns


class ShortestPathSubproblem:
    """
    Subproblem: Shortest Path with Resource Constraints (SPPRC)

    Finds routes with negative reduced cost to add to master problem.

    Resources:
    - Time (duration constraint)
    - Capacity (weight, linear feet)
    - Node visits (pickup before delivery)
    """

    def __init__(
        self,
        shipments: list[Shipment],
        carriers: list[Carrier],
        max_stops: int = 8,
        max_duration_hours: float = 14.0,
        max_distance_miles: float = 800.0
    ):
        self.shipments = shipments
        self.carriers = carriers
        self.max_stops = max_stops
        self.max_duration_hours = max_duration_hours
        self.max_distance_miles = max_distance_miles

        # Build distance matrix
        self._build_graph()

    def _build_graph(self):
        """Build graph for shortest path computation"""
        n = len(self.shipments)
        self.distances = np.zeros((2*n + 1, 2*n + 1))  # depot + pickup/delivery pairs

        # Node 0 is depot (use first carrier location or centroid)
        if self.carriers:
            depot = self.carriers[0].current_location
        else:
            depot = Location(latitude=39.8283, longitude=-98.5795)  # US centroid

        locations = [depot]
        for s in self.shipments:
            locations.append(s.origin)
            locations.append(s.destination)

        for i in range(len(locations)):
            for j in range(len(locations)):
                if i != j:
                    self.distances[i][j] = locations[i].distance_to(locations[j])

    def solve(self, dual_values: np.ndarray, cost_per_mile: float = 2.5) -> Optional[Column]:
        """
        Find route with minimum reduced cost using label-setting algorithm

        Reduced cost = route_cost - sum(dual_i for shipments in route)
        """
        n = len(self.shipments)
        if n == 0:
            return None

        # Label: (cost, reduced_cost, visited_shipments, current_node, capacity_used, time_used)
        # Use A* style search with reduced cost as heuristic

        best_column = None
        best_reduced_cost = 0  # Only want negative reduced cost

        # Try building routes greedily with different starting shipments
        for start_shipment in range(n):
            route = self._build_route_from_shipment(
                start_shipment, dual_values, cost_per_mile
            )
            if route and route.reduced_cost < best_reduced_cost:
                best_reduced_cost = route.reduced_cost
                best_column = route

        return best_column

    def _build_route_from_shipment(
        self,
        start_idx: int,
        dual_values: np.ndarray,
        cost_per_mile: float
    ) -> Optional[Column]:
        """Build a feasible route starting from a shipment"""
        n = len(self.shipments)

        visited_shipments = [start_idx]
        route_distance = 0.0
        capacity_used = self.shipments[start_idx].dimensions.linear_feet

        # Start at depot, go to pickup, then delivery
        current_node = 0  # depot
        pickup_node = 1 + 2 * start_idx
        delivery_node = 2 + 2 * start_idx

        route_distance += self.distances[current_node][pickup_node]
        route_distance += self.distances[pickup_node][delivery_node]
        current_node = delivery_node

        # Try to add more shipments
        remaining = [i for i in range(n) if i != start_idx]

        while remaining and len(visited_shipments) < self.max_stops // 2:
            best_next = None
            best_insertion_cost = float('inf')

            for idx in remaining:
                shipment = self.shipments[idx]

                # Check capacity
                new_capacity = capacity_used + shipment.dimensions.linear_feet
                if self.carriers and new_capacity > self.carriers[0].trailer_length_feet:
                    continue

                # Calculate insertion cost
                pickup_node_new = 1 + 2 * idx
                delivery_node_new = 2 + 2 * idx

                insertion_distance = (
                    self.distances[current_node][pickup_node_new] +
                    self.distances[pickup_node_new][delivery_node_new]
                )

                # Check distance constraint
                if route_distance + insertion_distance > self.max_distance_miles:
                    continue

                # Evaluate based on distance per unit dual value
                if dual_values[idx] > 0:
                    ratio = insertion_distance / dual_values[idx]
                    if ratio < best_insertion_cost:
                        best_insertion_cost = ratio
                        best_next = idx

            if best_next is not None:
                visited_shipments.append(best_next)
                pickup_node_new = 1 + 2 * best_next
                delivery_node_new = 2 + 2 * best_next

                route_distance += self.distances[current_node][pickup_node_new]
                route_distance += self.distances[pickup_node_new][delivery_node_new]
                current_node = delivery_node_new

                capacity_used += self.shipments[best_next].dimensions.linear_feet
                remaining.remove(best_next)
            else:
                break

        # Return to depot
        route_distance += self.distances[current_node][0]

        # Calculate costs
        route_cost = route_distance * cost_per_mile
        dual_sum = sum(dual_values[i] for i in visited_shipments)
        reduced_cost = route_cost - dual_sum

        # Calculate utilization
        utilization = 0.0
        if self.carriers:
            utilization = capacity_used / self.carriers[0].trailer_length_feet * 100

        return Column(
            id=hash(tuple(visited_shipments)),
            shipment_indices=visited_shipments,
            cost=route_cost,
            distance=route_distance,
            duration=route_distance / 50,  # Assume 50 mph
            utilization=utilization,
            reduced_cost=reduced_cost
        )


class ColumnGenerationSolver:
    """
    Main Column Generation Algorithm

    1. Initialize with simple feasible routes (one shipment per route)
    2. Solve master problem LP relaxation
    3. Get dual values
    4. Solve subproblem to find negative reduced cost columns
    5. If found, add to master and repeat from step 2
    6. When no negative reduced cost columns, solve IP for final solution
    """

    def __init__(
        self,
        max_iterations: int = 100,
        gap_tolerance: float = 0.001,
        time_limit_seconds: int = 60
    ):
        self.max_iterations = max_iterations
        self.gap_tolerance = gap_tolerance
        self.time_limit_seconds = time_limit_seconds

    def solve(
        self,
        shipments: list[Shipment],
        carriers: list[Carrier]
    ) -> ColumnGenerationResult:
        """Run column generation algorithm"""
        import time
        start_time = time.time()

        logger.info(
            "starting_column_generation",
            num_shipments=len(shipments),
            num_carriers=len(carriers)
        )

        n = len(shipments)
        if n == 0:
            return ColumnGenerationResult(
                selected_routes=[],
                total_cost=0,
                total_distance=0,
                unassigned_shipments=[],
                iterations=0,
                gap=0
            )

        # Initialize master problem
        master = SetCoveringMasterProblem(n)

        # Initialize with single-shipment routes
        for i, shipment in enumerate(shipments):
            distance = shipment.distance_miles * 2 + 50  # Round trip + deadhead
            cost = distance * 2.5

            initial_column = Column(
                id=i,
                shipment_indices=[i],
                cost=cost,
                distance=distance,
                duration=distance / 50,
                utilization=shipment.dimensions.linear_feet / 53 * 100
            )
            master.add_column(initial_column)

        # Initialize subproblem
        subproblem = ShortestPathSubproblem(shipments, carriers)

        # Column generation iterations
        iteration = 0
        lower_bound = 0
        upper_bound = float('inf')

        while iteration < self.max_iterations:
            if time.time() - start_time > self.time_limit_seconds:
                logger.warning("column_generation_time_limit_reached")
                break

            # Solve master LP
            master_solution = master.solve_lp_relaxation()
            lower_bound = master_solution.objective_value

            if master_solution.selected_columns:
                upper_bound = min(upper_bound, master_solution.objective_value)

            # Solve subproblem with dual values
            new_column = subproblem.solve(master_solution.dual_values)

            # Check for negative reduced cost
            if new_column is None or new_column.reduced_cost >= -self.gap_tolerance:
                logger.info(
                    "column_generation_converged",
                    iteration=iteration,
                    final_cost=master_solution.objective_value
                )
                break

            # Add new column to master
            master.add_column(new_column)
            iteration += 1

            logger.debug(
                "column_generation_iteration",
                iteration=iteration,
                num_columns=len(master.columns),
                reduced_cost=new_column.reduced_cost
            )

        # Solve final IP
        final_solution = master.solve_lp_relaxation()
        selected_indices = master.solve_ip(final_solution.selected_columns)

        # Build result routes
        routes = []
        covered_shipments = set()

        for col_idx in selected_indices:
            col = master.columns[col_idx]
            route = Route(
                shipment_ids=[shipments[i].id for i in col.shipment_indices],
                total_distance_miles=col.distance,
                total_duration_hours=col.duration,
                utilization_percent=col.utilization,
                total_cost=col.cost,
                status="planned"
            )
            routes.append(route)
            covered_shipments.update(col.shipment_indices)

        unassigned = [i for i in range(n) if i not in covered_shipments]

        gap = (upper_bound - lower_bound) / upper_bound if upper_bound > 0 else 0

        logger.info(
            "column_generation_complete",
            num_routes=len(routes),
            total_cost=final_solution.objective_value,
            iterations=iteration,
            gap=gap
        )

        return ColumnGenerationResult(
            selected_routes=routes,
            total_cost=final_solution.objective_value,
            total_distance=sum(r.total_distance_miles for r in routes),
            unassigned_shipments=unassigned,
            iterations=iteration,
            gap=gap
        )
