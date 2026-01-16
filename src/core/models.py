"""
Core domain models for the Shared Logistics Platform
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class ShipmentStatus(Enum):
    PENDING = "pending"
    QUOTED = "quoted"
    BOOKED = "booked"
    POOLED = "pooled"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ShipmentType(Enum):
    LTL = "ltl"  # Less Than Truckload
    STL = "stl"  # Shared Truckload
    FTL = "ftl"  # Full Truckload
    PARTIAL = "partial"


class CommodityType(Enum):
    GENERAL = "general"
    FOOD_GRADE = "food_grade"
    HAZMAT = "hazmat"
    FRAGILE = "fragile"
    TEMPERATURE_CONTROLLED = "temperature_controlled"
    HIGH_VALUE = "high_value"


class EquipmentType(Enum):
    DRY_VAN = "dry_van"
    REEFER = "reefer"
    FLATBED = "flatbed"
    STEP_DECK = "step_deck"


@dataclass
class Location:
    """Geographic location with address and coordinates"""
    id: UUID = field(default_factory=uuid4)
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = "USA"
    latitude: float = 0.0
    longitude: float = 0.0
    h3_index: Optional[str] = None  # H3 geospatial index

    def distance_to(self, other: "Location") -> float:
        """Calculate haversine distance in miles"""
        from math import radians, cos, sin, asin, sqrt

        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        # Earth radius in miles
        r = 3956
        return c * r


@dataclass
class TimeWindow:
    """Time window for pickup or delivery"""
    earliest: datetime
    latest: datetime

    @property
    def duration_hours(self) -> float:
        return (self.latest - self.earliest).total_seconds() / 3600

    def overlaps(self, other: "TimeWindow") -> bool:
        return self.earliest <= other.latest and other.earliest <= self.latest

    def intersection(self, other: "TimeWindow") -> Optional["TimeWindow"]:
        if not self.overlaps(other):
            return None
        return TimeWindow(
            earliest=max(self.earliest, other.earliest),
            latest=min(self.latest, other.latest)
        )


@dataclass
class Dimensions:
    """Physical dimensions of shipment"""
    length_inches: float = 0.0
    width_inches: float = 0.0
    height_inches: float = 0.0
    weight_lbs: float = 0.0
    linear_feet: float = 0.0
    pallet_count: int = 0
    stackable: bool = True

    @property
    def cubic_feet(self) -> float:
        return (self.length_inches * self.width_inches * self.height_inches) / 1728

    @property
    def density(self) -> float:
        """PCF - Pounds per cubic foot"""
        if self.cubic_feet == 0:
            return 0
        return self.weight_lbs / self.cubic_feet


@dataclass
class Shipment:
    """A shipment to be transported"""
    id: UUID = field(default_factory=uuid4)
    shipper_id: UUID = field(default_factory=uuid4)

    # Locations
    origin: Location = field(default_factory=Location)
    destination: Location = field(default_factory=Location)

    # Time windows
    pickup_window: TimeWindow = field(default_factory=lambda: TimeWindow(
        earliest=datetime.now(),
        latest=datetime.now() + timedelta(hours=4)
    ))
    delivery_window: TimeWindow = field(default_factory=lambda: TimeWindow(
        earliest=datetime.now() + timedelta(hours=24),
        latest=datetime.now() + timedelta(hours=48)
    ))

    # Physical attributes
    dimensions: Dimensions = field(default_factory=Dimensions)
    commodity_type: CommodityType = CommodityType.GENERAL
    equipment_required: EquipmentType = EquipmentType.DRY_VAN

    # Requirements
    requires_liftgate: bool = False
    requires_appointment: bool = False
    requires_inside_delivery: bool = False
    special_instructions: str = ""

    # Status and pricing
    status: ShipmentStatus = ShipmentStatus.PENDING
    shipment_type: ShipmentType = ShipmentType.STL
    quoted_price: float = 0.0
    final_price: float = 0.0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def distance_miles(self) -> float:
        return self.origin.distance_to(self.destination)

    @property
    def time_flexibility_hours(self) -> float:
        """How much flexibility in delivery timing"""
        return (self.delivery_window.latest - self.pickup_window.earliest).total_seconds() / 3600


@dataclass
class Carrier:
    """A carrier/driver with a truck"""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    mc_number: str = ""
    dot_number: str = ""

    # Equipment
    equipment_type: EquipmentType = EquipmentType.DRY_VAN
    trailer_length_feet: float = 53.0
    max_weight_lbs: float = 45000.0

    # Current state
    current_location: Location = field(default_factory=Location)
    available_capacity_linear_feet: float = 53.0
    available_weight_lbs: float = 45000.0

    # Preferences
    preferred_lanes: list[tuple[str, str]] = field(default_factory=list)  # (origin_state, dest_state)
    max_deadhead_miles: float = 100.0
    min_rate_per_mile: float = 2.00

    # Availability
    available_from: datetime = field(default_factory=datetime.now)
    available_until: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))
    hours_of_service_remaining: float = 11.0

    # Performance metrics
    on_time_percentage: float = 98.0
    damage_free_percentage: float = 99.5
    acceptance_rate: float = 85.0

    def can_handle_shipment(self, shipment: Shipment) -> bool:
        """Check if carrier can handle the shipment"""
        if shipment.equipment_required != self.equipment_type:
            return False
        if shipment.dimensions.linear_feet > self.available_capacity_linear_feet:
            return False
        if shipment.dimensions.weight_lbs > self.available_weight_lbs:
            return False
        return True


@dataclass
class RouteStop:
    """A stop on a route"""
    location: Location
    shipment_id: UUID
    stop_type: str  # "pickup" or "delivery"
    scheduled_time: datetime
    time_window: TimeWindow
    service_time_minutes: float = 30.0
    sequence: int = 0


@dataclass
class Route:
    """An optimized route with multiple stops"""
    id: UUID = field(default_factory=uuid4)
    carrier_id: Optional[UUID] = None
    stops: list[RouteStop] = field(default_factory=list)
    shipment_ids: list[UUID] = field(default_factory=list)

    # Metrics
    total_distance_miles: float = 0.0
    total_duration_hours: float = 0.0
    total_revenue: float = 0.0
    total_cost: float = 0.0
    utilization_percent: float = 0.0

    # Status
    status: str = "planned"
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def profit(self) -> float:
        return self.total_revenue - self.total_cost

    @property
    def profit_per_mile(self) -> float:
        if self.total_distance_miles == 0:
            return 0
        return self.profit / self.total_distance_miles

    @property
    def num_shipments(self) -> int:
        return len(self.shipment_ids)


@dataclass
class PoolingOpportunity:
    """A potential pooling match between shipments"""
    id: UUID = field(default_factory=uuid4)
    shipment_ids: list[UUID] = field(default_factory=list)

    # Compatibility scores
    geographic_score: float = 0.0
    temporal_score: float = 0.0
    capacity_score: float = 0.0
    overall_score: float = 0.0

    # Savings
    individual_cost: float = 0.0
    pooled_cost: float = 0.0
    savings_percent: float = 0.0

    # Route info
    optimized_route: Optional[Route] = None

    @property
    def total_savings(self) -> float:
        return self.individual_cost - self.pooled_cost
