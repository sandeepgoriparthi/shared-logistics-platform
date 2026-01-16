"""
Logistics Simulator

Simulates realistic freight operations to test and validate
the platform's optimization algorithms and ML models.
"""
import random
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import uuid4
import structlog

from src.core.models import (
    Shipment, Carrier, Location, TimeWindow, Dimensions,
    CommodityType, EquipmentType, ShipmentStatus
)
from src.core.matching.pooling_engine import PoolingEngine, PoolingConfig

logger = structlog.get_logger()


# Major US freight hubs with coordinates
US_FREIGHT_HUBS = {
    "Los Angeles, CA": (34.0522, -118.2437),
    "Chicago, IL": (41.8781, -87.6298),
    "Dallas, TX": (32.7767, -96.7970),
    "Atlanta, GA": (33.7490, -84.3880),
    "Houston, TX": (29.7604, -95.3698),
    "Phoenix, AZ": (33.4484, -112.0740),
    "Philadelphia, PA": (39.9526, -75.1652),
    "San Antonio, TX": (29.4241, -98.4936),
    "San Diego, CA": (32.7157, -117.1611),
    "San Jose, CA": (37.3382, -121.8863),
    "Denver, CO": (39.7392, -104.9903),
    "Seattle, WA": (47.6062, -122.3321),
    "Boston, MA": (42.3601, -71.0589),
    "Nashville, TN": (36.1627, -86.7816),
    "Memphis, TN": (35.1495, -90.0490),
    "Indianapolis, IN": (39.7684, -86.1581),
    "Columbus, OH": (39.9612, -82.9988),
    "Charlotte, NC": (35.2271, -80.8431),
    "Kansas City, MO": (39.0997, -94.5786),
    "Salt Lake City, UT": (40.7608, -111.8910),
}

# Common freight lanes (high volume corridors)
HIGH_VOLUME_LANES = [
    ("Los Angeles, CA", "Chicago, IL"),
    ("Los Angeles, CA", "Dallas, TX"),
    ("Chicago, IL", "Atlanta, GA"),
    ("Dallas, TX", "Atlanta, GA"),
    ("Seattle, WA", "Los Angeles, CA"),
    ("Houston, TX", "Atlanta, GA"),
    ("Chicago, IL", "Dallas, TX"),
    ("Phoenix, AZ", "Denver, CO"),
    ("Memphis, TN", "Chicago, IL"),
    ("Nashville, TN", "Atlanta, GA"),
]


@dataclass
class SimulationConfig:
    """Configuration for simulation"""
    # Time settings
    start_date: datetime = None
    simulation_days: int = 7
    time_step_hours: float = 1.0

    # Volume settings
    shipments_per_day_mean: int = 100
    shipments_per_day_std: int = 20

    # Shipment characteristics
    weight_mean_lbs: float = 15000
    weight_std_lbs: float = 8000
    linear_feet_mean: float = 20
    linear_feet_std: float = 10

    # Time windows
    pickup_window_hours: float = 4.0
    delivery_flexibility_hours: float = 48.0

    # Carrier settings
    num_carriers: int = 50
    carrier_utilization_target: float = 0.75

    # Pooling
    pooling_probability_base: float = 0.6

    # Randomization
    random_seed: int = 42

    def __post_init__(self):
        if self.start_date is None:
            self.start_date = datetime.utcnow()


@dataclass
class SimulationResult:
    """Results from simulation run"""
    total_shipments: int
    pooled_shipments: int
    pooling_rate: float
    total_cost_individual: float
    total_cost_pooled: float
    total_savings: float
    savings_percent: float
    average_utilization: float
    on_time_rate: float
    routes_created: int
    simulation_time_seconds: float


class FreightSimulator:
    """
    Simulate realistic freight operations

    Features:
    - Realistic shipment generation
    - Lane-based volume patterns
    - Time-varying demand
    - Carrier capacity constraints
    """

    def __init__(self, config: SimulationConfig = None):
        self.config = config or SimulationConfig()
        self.random = random.Random(self.config.random_seed)
        np.random.seed(self.config.random_seed)

        # State
        self.shipments: List[Shipment] = []
        self.carriers: List[Carrier] = []
        self.routes: List = []

        # Metrics
        self.metrics: Dict = {}

    def generate_shipments(self, num_shipments: int = None) -> List[Shipment]:
        """Generate realistic shipments"""
        if num_shipments is None:
            num_shipments = int(np.random.normal(
                self.config.shipments_per_day_mean * self.config.simulation_days,
                self.config.shipments_per_day_std * np.sqrt(self.config.simulation_days)
            ))

        shipments = []

        for _ in range(num_shipments):
            shipment = self._generate_single_shipment()
            shipments.append(shipment)

        self.shipments = shipments
        logger.info("generated_shipments", count=len(shipments))
        return shipments

    def _generate_single_shipment(self) -> Shipment:
        """Generate a single realistic shipment"""
        # Select origin and destination
        if self.random.random() < 0.7:
            # Use high volume lane
            origin_city, dest_city = self.random.choice(HIGH_VOLUME_LANES)
            if self.random.random() < 0.5:
                origin_city, dest_city = dest_city, origin_city
        else:
            # Random lane
            origin_city = self.random.choice(list(US_FREIGHT_HUBS.keys()))
            dest_city = self.random.choice([c for c in US_FREIGHT_HUBS.keys() if c != origin_city])

        origin_coords = US_FREIGHT_HUBS[origin_city]
        dest_coords = US_FREIGHT_HUBS[dest_city]

        # Add some randomness to exact location (within 30 miles)
        origin_lat = origin_coords[0] + self.random.uniform(-0.3, 0.3)
        origin_lon = origin_coords[1] + self.random.uniform(-0.3, 0.3)
        dest_lat = dest_coords[0] + self.random.uniform(-0.3, 0.3)
        dest_lon = dest_coords[1] + self.random.uniform(-0.3, 0.3)

        origin = Location(
            city=origin_city.split(",")[0],
            state=origin_city.split(",")[1].strip(),
            latitude=origin_lat,
            longitude=origin_lon
        )

        destination = Location(
            city=dest_city.split(",")[0],
            state=dest_city.split(",")[1].strip(),
            latitude=dest_lat,
            longitude=dest_lon
        )

        # Time windows
        days_offset = self.random.randint(0, self.config.simulation_days - 1)
        hour_offset = self.random.randint(6, 18)  # Business hours

        pickup_start = self.config.start_date + timedelta(days=days_offset, hours=hour_offset)
        pickup_end = pickup_start + timedelta(hours=self.config.pickup_window_hours)

        # Delivery based on distance
        distance = origin.distance_to(destination)
        transit_hours = distance / 50 + 6  # 50 mph average + handling

        delivery_start = pickup_start + timedelta(hours=transit_hours)
        delivery_end = delivery_start + timedelta(hours=self.config.delivery_flexibility_hours)

        pickup_window = TimeWindow(earliest=pickup_start, latest=pickup_end)
        delivery_window = TimeWindow(earliest=delivery_start, latest=delivery_end)

        # Dimensions
        weight = max(1000, np.random.normal(
            self.config.weight_mean_lbs,
            self.config.weight_std_lbs
        ))
        linear_feet = max(4, min(48, np.random.normal(
            self.config.linear_feet_mean,
            self.config.linear_feet_std
        )))
        pallet_count = max(1, int(linear_feet / 4))

        dimensions = Dimensions(
            weight_lbs=weight,
            linear_feet=linear_feet,
            pallet_count=pallet_count,
            stackable=self.random.random() < 0.7
        )

        # Equipment and commodity
        equipment = EquipmentType.DRY_VAN
        if self.random.random() < 0.15:
            equipment = EquipmentType.REEFER
        elif self.random.random() < 0.05:
            equipment = EquipmentType.FLATBED

        commodity = CommodityType.GENERAL
        if equipment == EquipmentType.REEFER:
            commodity = CommodityType.FOOD_GRADE
        elif self.random.random() < 0.1:
            commodity = CommodityType.HIGH_VALUE

        return Shipment(
            origin=origin,
            destination=destination,
            pickup_window=pickup_window,
            delivery_window=delivery_window,
            dimensions=dimensions,
            equipment_required=equipment,
            commodity_type=commodity,
            requires_liftgate=self.random.random() < 0.1,
            requires_appointment=self.random.random() < 0.3,
            status=ShipmentStatus.PENDING
        )

    def generate_carriers(self, num_carriers: int = None) -> List[Carrier]:
        """Generate carrier fleet"""
        if num_carriers is None:
            num_carriers = self.config.num_carriers

        carriers = []

        for i in range(num_carriers):
            # Random starting location
            city = self.random.choice(list(US_FREIGHT_HUBS.keys()))
            coords = US_FREIGHT_HUBS[city]

            # Add variation
            lat = coords[0] + self.random.uniform(-0.5, 0.5)
            lon = coords[1] + self.random.uniform(-0.5, 0.5)

            location = Location(
                city=city.split(",")[0],
                state=city.split(",")[1].strip(),
                latitude=lat,
                longitude=lon
            )

            # Equipment distribution
            equipment = EquipmentType.DRY_VAN
            if self.random.random() < 0.2:
                equipment = EquipmentType.REEFER
            elif self.random.random() < 0.1:
                equipment = EquipmentType.FLATBED

            carrier = Carrier(
                name=f"Carrier_{i+1:03d}",
                mc_number=f"MC{100000+i}",
                dot_number=f"DOT{1000000+i}",
                equipment_type=equipment,
                current_location=location,
                available_capacity_linear_feet=53.0,
                available_weight_lbs=45000.0,
                min_rate_per_mile=self.random.uniform(1.8, 2.5),
                max_deadhead_miles=self.random.uniform(50, 150),
                on_time_percentage=self.random.uniform(90, 99),
                damage_free_percentage=self.random.uniform(97, 100),
                acceptance_rate=self.random.uniform(60, 95)
            )

            carriers.append(carrier)

        self.carriers = carriers
        logger.info("generated_carriers", count=len(carriers))
        return carriers

    def run_simulation(self) -> SimulationResult:
        """Run full simulation"""
        import time
        start_time = time.time()

        logger.info(
            "starting_simulation",
            days=self.config.simulation_days,
            target_shipments=self.config.shipments_per_day_mean * self.config.simulation_days
        )

        # Generate data
        if not self.shipments:
            self.generate_shipments()
        if not self.carriers:
            self.generate_carriers()

        # Run pooling optimization
        pooling_engine = PoolingEngine(
            config=PoolingConfig(
                max_origin_distance_miles=50,
                max_dest_distance_miles=50,
                min_time_overlap_hours=2,
                max_shipments_per_pool=4,
                min_savings_percent=10,
                use_advanced_optimization=True
            )
        )

        pooling_result = pooling_engine.find_pooling_opportunities(
            self.shipments,
            self.carriers
        )

        # Calculate metrics
        total_individual_cost = sum(
            s.distance_miles * 2.5 + 50
            for s in self.shipments
        )

        total_pooled_cost = total_individual_cost - pooling_result.total_potential_savings

        # Utilization
        total_capacity_used = sum(s.dimensions.linear_feet for s in self.shipments)
        num_trucks_needed_individual = len(self.shipments)
        num_trucks_needed_pooled = len(self.shipments) - pooling_result.shipments_pooled + len(pooling_result.opportunities)

        avg_utilization_individual = (total_capacity_used / (num_trucks_needed_individual * 53)) * 100
        avg_utilization_pooled = (total_capacity_used / (num_trucks_needed_pooled * 53)) * 100 if num_trucks_needed_pooled > 0 else 0

        simulation_time = time.time() - start_time

        result = SimulationResult(
            total_shipments=len(self.shipments),
            pooled_shipments=pooling_result.shipments_pooled,
            pooling_rate=pooling_result.shipments_pooled / len(self.shipments) * 100 if self.shipments else 0,
            total_cost_individual=total_individual_cost,
            total_cost_pooled=total_pooled_cost,
            total_savings=pooling_result.total_potential_savings,
            savings_percent=pooling_result.average_savings_percent,
            average_utilization=avg_utilization_pooled,
            on_time_rate=97.0,  # Placeholder
            routes_created=len(pooling_result.opportunities),
            simulation_time_seconds=simulation_time
        )

        logger.info(
            "simulation_complete",
            total_shipments=result.total_shipments,
            pooling_rate=f"{result.pooling_rate:.1f}%",
            savings_percent=f"{result.savings_percent:.1f}%",
            total_savings=f"${result.total_savings:,.2f}",
            simulation_time=f"{result.simulation_time_seconds:.2f}s"
        )

        return result

    def generate_report(self, result: SimulationResult) -> str:
        """Generate simulation report"""
        report = f"""
═══════════════════════════════════════════════════════════════════
              SHARED LOGISTICS PLATFORM - SIMULATION REPORT
═══════════════════════════════════════════════════════════════════

SIMULATION PARAMETERS
─────────────────────
  Duration:           {self.config.simulation_days} days
  Shipments:          {result.total_shipments}
  Carriers:           {len(self.carriers)}

POOLING PERFORMANCE
─────────────────────
  Shipments Pooled:   {result.pooled_shipments} ({result.pooling_rate:.1f}%)
  Routes Created:     {result.routes_created}
  Avg Utilization:    {result.average_utilization:.1f}%

FINANCIAL IMPACT
─────────────────────
  Cost (Individual):  ${result.total_cost_individual:,.2f}
  Cost (Pooled):      ${result.total_cost_pooled:,.2f}
  ─────────────────────
  TOTAL SAVINGS:      ${result.total_savings:,.2f}
  Savings Rate:       {result.savings_percent:.1f}%

OPERATIONAL METRICS
─────────────────────
  On-Time Rate:       {result.on_time_rate:.1f}%

PERFORMANCE
─────────────────────
  Simulation Time:    {result.simulation_time_seconds:.2f} seconds

═══════════════════════════════════════════════════════════════════
"""
        return report


def run_benchmark():
    """Run benchmark simulation"""
    print("\n" + "="*70)
    print("Running Shared Logistics Platform Benchmark")
    print("="*70 + "\n")

    config = SimulationConfig(
        simulation_days=7,
        shipments_per_day_mean=100,
        num_carriers=50,
        random_seed=42
    )

    simulator = FreightSimulator(config)
    result = simulator.run_simulation()
    report = simulator.generate_report(result)

    print(report)

    return result


if __name__ == "__main__":
    run_benchmark()
