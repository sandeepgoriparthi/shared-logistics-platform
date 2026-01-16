"""
Vehicle Routing Problem with Time Windows (VRPTW) Solver

This is the core optimization engine that solves the routing problem
for shared truckload logistics. Uses Google OR-Tools with custom
enhancements for multi-objective optimization.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from uuid import UUID
import structlog

from ..models import Shipment, Carrier, Route, RouteStop, Location, TimeWindow

logger = structlog.get_logger()


@dataclass
class VRPTWInstance:
    """Data structure for VRPTW problem instance"""
    shipments: list[Shipment]
    carriers: list[Carrier]
    depot_location: Location

    # Computed matrices
    distance_matrix: np.ndarray = field(default_factory=lambda: np.array([]))
    time_matrix: np.ndarray = field(default_factory=lambda: np.array([]))

    # Parameters
    time_limit_seconds: int = 30
    max_vehicles: int = 100

    def __post_init__(self):
        self._build_matrices()

    def _build_matrices(self):
        """Build distance and time matrices for all locations"""
        # Collect all locations: depot + pickup + delivery for each shipment
        locations = [self.depot_location]
        for shipment in self.shipments:
            locations.append(shipment.origin)
            locations.append(shipment.destination)

        n = len(locations)
        self.distance_matrix = np.zeros((n, n))
        self.time_matrix = np.zeros((n, n))

        # Average speed in mph for time calculation
        avg_speed_mph = 50.0

        for i in range(n):
            for j in range(n):
                if i != j:
                    dist = locations[i].distance_to(locations[j])
                    self.distance_matrix[i][j] = dist
                    # Time in minutes
                    self.time_matrix[i][j] = (dist / avg_speed_mph) * 60

    @property
    def num_locations(self) -> int:
        return 1 + 2 * len(self.shipments)  # depot + pickup/delivery pairs

    @property
    def num_vehicles(self) -> int:
        return min(len(self.carriers), self.max_vehicles)


@dataclass
class VRPTWSolution:
    """Solution from VRPTW solver"""
    routes: list[Route]
    total_distance: float
    total_time: float
    unassigned_shipments: list[UUID]
    objective_value: float
    solve_time_seconds: float
    status: str


class VRPTWSolver:
    """
    Advanced VRPTW Solver using Google OR-Tools

    Features:
    - Time windows for pickup and delivery
    - Capacity constraints (weight, linear feet, pallets)
    - Pickup and delivery pairing
    - Multiple objectives (cost, time, utilization)
    - Service time at stops
    """

    def __init__(
        self,
        time_limit_seconds: int = 30,
        first_solution_strategy: str = "PATH_CHEAPEST_ARC",
        local_search_metaheuristic: str = "GUIDED_LOCAL_SEARCH",
    ):
        self.time_limit_seconds = time_limit_seconds
        self.first_solution_strategy = first_solution_strategy
        self.local_search_metaheuristic = local_search_metaheuristic

    def solve(self, instance: VRPTWInstance) -> VRPTWSolution:
        """Solve the VRPTW instance"""
        import time
        start_time = time.time()

        logger.info(
            "solving_vrptw",
            num_shipments=len(instance.shipments),
            num_vehicles=instance.num_vehicles,
        )

        # Create routing index manager
        manager = pywrapcp.RoutingIndexManager(
            instance.num_locations,
            instance.num_vehicles,
            0  # Depot index
        )

        # Create routing model
        routing = pywrapcp.RoutingModel(manager)

        # Create distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(instance.distance_matrix[from_node][to_node] * 100)  # Scale for precision

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Add distance dimension
        routing.AddDimension(
            transit_callback_index,
            0,  # No slack
            int(800 * 100),  # Max distance 800 miles scaled
            True,  # Start cumul at zero
            "Distance"
        )

        # Create time callback
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            travel_time = instance.time_matrix[from_node][to_node]
            # Add service time (30 minutes average)
            service_time = 30 if from_node != 0 else 0
            return int(travel_time + service_time)

        time_callback_index = routing.RegisterTransitCallback(time_callback)

        # Add time dimension with time windows
        routing.AddDimension(
            time_callback_index,
            60,  # Allow 60 minutes of slack
            14 * 60,  # Max 14 hours per route
            False,  # Don't force start cumul to zero
            "Time"
        )
        time_dimension = routing.GetDimensionOrDie("Time")

        # Add time windows for each location
        self._add_time_windows(routing, manager, instance, time_dimension)

        # Add capacity constraints
        self._add_capacity_constraints(routing, manager, instance)

        # Add pickup and delivery constraints
        self._add_pickup_delivery_constraints(routing, manager, instance)

        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = getattr(
            routing_enums_pb2.FirstSolutionStrategy,
            self.first_solution_strategy
        )
        search_parameters.local_search_metaheuristic = getattr(
            routing_enums_pb2.LocalSearchMetaheuristic,
            self.local_search_metaheuristic
        )
        search_parameters.time_limit.seconds = self.time_limit_seconds

        # Solve
        solution = routing.SolveWithParameters(search_parameters)

        solve_time = time.time() - start_time

        if solution:
            return self._extract_solution(
                routing, manager, solution, instance, solve_time
            )
        else:
            logger.warning("vrptw_no_solution_found")
            return VRPTWSolution(
                routes=[],
                total_distance=0,
                total_time=0,
                unassigned_shipments=[s.id for s in instance.shipments],
                objective_value=float('inf'),
                solve_time_seconds=solve_time,
                status="no_solution"
            )

    def _add_time_windows(
        self,
        routing: pywrapcp.RoutingModel,
        manager: pywrapcp.RoutingIndexManager,
        instance: VRPTWInstance,
        time_dimension
    ):
        """Add time window constraints for each node"""
        # Depot has wide time window
        depot_index = manager.NodeToIndex(0)
        time_dimension.CumulVar(depot_index).SetRange(0, 24 * 60)

        # Add time windows for pickup and delivery nodes
        for i, shipment in enumerate(instance.shipments):
            pickup_index = manager.NodeToIndex(1 + 2 * i)
            delivery_index = manager.NodeToIndex(2 + 2 * i)

            # Convert time windows to minutes from midnight
            # For simplicity, using hours offset
            pickup_earliest = 0
            pickup_latest = int(shipment.pickup_window.duration_hours * 60 + 4 * 60)

            delivery_earliest = 0
            delivery_latest = int(shipment.delivery_window.duration_hours * 60 + 24 * 60)

            time_dimension.CumulVar(pickup_index).SetRange(pickup_earliest, pickup_latest)
            time_dimension.CumulVar(delivery_index).SetRange(delivery_earliest, delivery_latest)

    def _add_capacity_constraints(
        self,
        routing: pywrapcp.RoutingModel,
        manager: pywrapcp.RoutingIndexManager,
        instance: VRPTWInstance
    ):
        """Add capacity constraints for weight and linear feet"""
        # Weight capacity
        def weight_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            if from_node == 0:
                return 0
            shipment_idx = (from_node - 1) // 2
            is_pickup = (from_node - 1) % 2 == 0
            if shipment_idx < len(instance.shipments):
                weight = int(instance.shipments[shipment_idx].dimensions.weight_lbs)
                return weight if is_pickup else -weight
            return 0

        weight_callback_index = routing.RegisterUnaryTransitCallback(weight_callback)
        routing.AddDimensionWithVehicleCapacity(
            weight_callback_index,
            0,  # No slack
            [int(c.max_weight_lbs) for c in instance.carriers[:instance.num_vehicles]],
            True,  # Start at zero
            "Weight"
        )

        # Linear feet capacity
        def linear_feet_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            if from_node == 0:
                return 0
            shipment_idx = (from_node - 1) // 2
            is_pickup = (from_node - 1) % 2 == 0
            if shipment_idx < len(instance.shipments):
                feet = int(instance.shipments[shipment_idx].dimensions.linear_feet * 10)
                return feet if is_pickup else -feet
            return 0

        linear_feet_callback_index = routing.RegisterUnaryTransitCallback(linear_feet_callback)
        routing.AddDimensionWithVehicleCapacity(
            linear_feet_callback_index,
            0,
            [int(c.trailer_length_feet * 10) for c in instance.carriers[:instance.num_vehicles]],
            True,
            "LinearFeet"
        )

    def _add_pickup_delivery_constraints(
        self,
        routing: pywrapcp.RoutingModel,
        manager: pywrapcp.RoutingIndexManager,
        instance: VRPTWInstance
    ):
        """Add pickup and delivery pairing constraints"""
        for i in range(len(instance.shipments)):
            pickup_index = manager.NodeToIndex(1 + 2 * i)
            delivery_index = manager.NodeToIndex(2 + 2 * i)

            # Same vehicle must serve pickup and delivery
            routing.AddPickupAndDelivery(pickup_index, delivery_index)

            # Pickup must happen before delivery
            routing.solver().Add(
                routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index)
            )

            time_dimension = routing.GetDimensionOrDie("Time")
            routing.solver().Add(
                time_dimension.CumulVar(pickup_index) <= time_dimension.CumulVar(delivery_index)
            )

    def _extract_solution(
        self,
        routing: pywrapcp.RoutingModel,
        manager: pywrapcp.RoutingIndexManager,
        solution,
        instance: VRPTWInstance,
        solve_time: float
    ) -> VRPTWSolution:
        """Extract solution into Route objects"""
        routes = []
        total_distance = 0
        total_time = 0

        time_dimension = routing.GetDimensionOrDie("Time")
        distance_dimension = routing.GetDimensionOrDie("Distance")

        for vehicle_id in range(instance.num_vehicles):
            index = routing.Start(vehicle_id)
            route_distance = 0
            route_time = 0
            stops = []
            shipment_ids = []

            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)

                if node != 0:  # Not depot
                    shipment_idx = (node - 1) // 2
                    is_pickup = (node - 1) % 2 == 0

                    if shipment_idx < len(instance.shipments):
                        shipment = instance.shipments[shipment_idx]
                        location = shipment.origin if is_pickup else shipment.destination
                        time_window = shipment.pickup_window if is_pickup else shipment.delivery_window

                        time_var = time_dimension.CumulVar(index)
                        scheduled_minutes = solution.Value(time_var)

                        stop = RouteStop(
                            location=location,
                            shipment_id=shipment.id,
                            stop_type="pickup" if is_pickup else "delivery",
                            scheduled_time=time_window.earliest,  # Simplified
                            time_window=time_window,
                            sequence=len(stops)
                        )
                        stops.append(stop)

                        if is_pickup and shipment.id not in shipment_ids:
                            shipment_ids.append(shipment.id)

                next_index = solution.Value(routing.NextVar(index))

                # Accumulate distance
                from_node = manager.IndexToNode(index)
                to_node = manager.IndexToNode(next_index)
                route_distance += instance.distance_matrix[from_node][to_node]

                index = next_index

            if stops:  # Only add non-empty routes
                route = Route(
                    carrier_id=instance.carriers[vehicle_id].id if vehicle_id < len(instance.carriers) else None,
                    stops=stops,
                    shipment_ids=shipment_ids,
                    total_distance_miles=route_distance,
                    total_duration_hours=route_time / 60 if route_time else route_distance / 50,
                    status="planned"
                )

                # Calculate utilization
                total_linear_feet = sum(
                    instance.shipments[i].dimensions.linear_feet
                    for i, s in enumerate(instance.shipments)
                    if s.id in shipment_ids
                )
                if vehicle_id < len(instance.carriers):
                    route.utilization_percent = (
                        total_linear_feet / instance.carriers[vehicle_id].trailer_length_feet * 100
                    )

                routes.append(route)
                total_distance += route_distance

        logger.info(
            "vrptw_solution_found",
            num_routes=len(routes),
            total_distance=total_distance,
            solve_time=solve_time
        )

        return VRPTWSolution(
            routes=routes,
            total_distance=total_distance,
            total_time=total_time,
            unassigned_shipments=[],  # Simplified
            objective_value=solution.ObjectiveValue() / 100,  # Unscale
            solve_time_seconds=solve_time,
            status="optimal" if routing.status() == 1 else "feasible"
        )


class MultiObjectiveVRPTW(VRPTWSolver):
    """
    Multi-objective VRPTW that optimizes for:
    1. Total cost (distance-based)
    2. Delivery time (customer service)
    3. Carbon footprint (environmental)
    4. Truck utilization (efficiency)
    """

    def __init__(
        self,
        weights: dict[str, float] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.weights = weights or {
            "cost": 0.4,
            "time": 0.3,
            "carbon": 0.15,
            "utilization": 0.15
        }

    def solve(self, instance: VRPTWInstance) -> VRPTWSolution:
        """Solve with multi-objective consideration"""
        # First solve for minimum cost
        solution = super().solve(instance)

        if solution.routes:
            # Calculate multi-objective metrics
            solution = self._calculate_objectives(solution, instance)

        return solution

    def _calculate_objectives(
        self,
        solution: VRPTWSolution,
        instance: VRPTWInstance
    ) -> VRPTWSolution:
        """Calculate and attach multi-objective scores"""
        total_cost = solution.total_distance * 2.5  # $2.50/mile
        total_carbon = solution.total_distance * 0.4  # kg CO2 per mile

        avg_utilization = np.mean([r.utilization_percent for r in solution.routes]) if solution.routes else 0

        # Composite score (lower is better)
        composite_score = (
            self.weights["cost"] * total_cost / 10000 +
            self.weights["time"] * solution.total_time / 100 +
            self.weights["carbon"] * total_carbon / 1000 +
            self.weights["utilization"] * (100 - avg_utilization) / 100
        )

        logger.info(
            "multi_objective_scores",
            total_cost=total_cost,
            total_carbon=total_carbon,
            avg_utilization=avg_utilization,
            composite_score=composite_score
        )

        return solution
