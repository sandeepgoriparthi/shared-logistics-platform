"""
Database Entity Models

SQLAlchemy models for the shared logistics platform.
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Index, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from .base import Base


# Enums
class ShipmentStatusEnum(str):
    PENDING = "pending"
    QUOTED = "quoted"
    BOOKED = "booked"
    POOLED = "pooled"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class EquipmentTypeEnum(str):
    DRY_VAN = "dry_van"
    REEFER = "reefer"
    FLATBED = "flatbed"
    STEP_DECK = "step_deck"


# ============= SHIPPER =============

class Shipper(Base):
    """Shipper entity - companies that need to ship goods"""
    __tablename__ = "shippers"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    zip_code: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(50), default="USA")

    # Business info
    mc_number: Mapped[Optional[str]] = mapped_column(String(50))
    dot_number: Mapped[Optional[str]] = mapped_column(String(50))
    credit_limit: Mapped[float] = mapped_column(Float, default=50000.0)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30)

    # Metrics
    total_shipments: Mapped[int] = mapped_column(Integer, default=0)
    total_spend: Mapped[float] = mapped_column(Float, default=0.0)
    pooling_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shipments: Mapped[List["Shipment"]] = relationship("Shipment", back_populates="shipper")

    __table_args__ = (
        Index("ix_shippers_email", "email"),
        Index("ix_shippers_company", "company_name"),
    )


# ============= CARRIER =============

class Carrier(Base):
    """Carrier entity - trucking companies and owner-operators"""
    __tablename__ = "carriers"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50))

    # Compliance
    mc_number: Mapped[str] = mapped_column(String(50), nullable=False)
    dot_number: Mapped[str] = mapped_column(String(50), nullable=False)
    insurance_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime)
    authority_status: Mapped[str] = mapped_column(String(50), default="active")

    # Equipment
    equipment_type: Mapped[str] = mapped_column(String(50), default=EquipmentTypeEnum.DRY_VAN)
    trailer_count: Mapped[int] = mapped_column(Integer, default=1)
    driver_count: Mapped[int] = mapped_column(Integer, default=1)

    # Capabilities
    max_weight_lbs: Mapped[float] = mapped_column(Float, default=45000.0)
    trailer_length_feet: Mapped[float] = mapped_column(Float, default=53.0)
    hazmat_certified: Mapped[bool] = mapped_column(Boolean, default=False)
    team_drivers: Mapped[bool] = mapped_column(Boolean, default=False)

    # Preferences
    preferred_lanes: Mapped[Optional[dict]] = mapped_column(JSON)  # JSON of lane preferences
    min_rate_per_mile: Mapped[float] = mapped_column(Float, default=2.00)
    max_deadhead_miles: Mapped[float] = mapped_column(Float, default=100.0)

    # Performance
    on_time_percentage: Mapped[float] = mapped_column(Float, default=95.0)
    damage_free_percentage: Mapped[float] = mapped_column(Float, default=99.0)
    acceptance_rate: Mapped[float] = mapped_column(Float, default=80.0)
    total_loads: Mapped[int] = mapped_column(Integer, default=0)
    total_miles: Mapped[float] = mapped_column(Float, default=0.0)

    # Location (current)
    current_latitude: Mapped[Optional[float]] = mapped_column(Float)
    current_longitude: Mapped[Optional[float]] = mapped_column(Float)
    current_city: Mapped[Optional[str]] = mapped_column(String(100))
    current_state: Mapped[Optional[str]] = mapped_column(String(50))
    location_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    routes: Mapped[List["Route"]] = relationship("Route", back_populates="carrier")

    __table_args__ = (
        Index("ix_carriers_mc_number", "mc_number"),
        Index("ix_carriers_location", "current_state", "current_city"),
        Index("ix_carriers_equipment", "equipment_type"),
    )


# ============= SHIPMENT =============

class Shipment(Base):
    """Shipment entity - individual freight shipments"""
    __tablename__ = "shipments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    shipper_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shippers.id"), nullable=False)
    reference_number: Mapped[str] = mapped_column(String(100), unique=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default=ShipmentStatusEnum.PENDING)

    # Origin
    origin_address: Mapped[str] = mapped_column(String(500), nullable=False)
    origin_city: Mapped[str] = mapped_column(String(100), nullable=False)
    origin_state: Mapped[str] = mapped_column(String(50), nullable=False)
    origin_zip: Mapped[str] = mapped_column(String(20), nullable=False)
    origin_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    origin_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    origin_h3_index: Mapped[Optional[str]] = mapped_column(String(20))

    # Destination
    dest_address: Mapped[str] = mapped_column(String(500), nullable=False)
    dest_city: Mapped[str] = mapped_column(String(100), nullable=False)
    dest_state: Mapped[str] = mapped_column(String(50), nullable=False)
    dest_zip: Mapped[str] = mapped_column(String(20), nullable=False)
    dest_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    dest_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    dest_h3_index: Mapped[Optional[str]] = mapped_column(String(20))

    # Time windows
    pickup_earliest: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pickup_latest: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    delivery_earliest: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    delivery_latest: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Physical attributes
    weight_lbs: Mapped[float] = mapped_column(Float, nullable=False)
    linear_feet: Mapped[float] = mapped_column(Float, nullable=False)
    pallet_count: Mapped[int] = mapped_column(Integer, default=0)
    piece_count: Mapped[int] = mapped_column(Integer, default=1)
    stackable: Mapped[bool] = mapped_column(Boolean, default=True)
    hazmat: Mapped[bool] = mapped_column(Boolean, default=False)

    # Requirements
    equipment_type: Mapped[str] = mapped_column(String(50), default=EquipmentTypeEnum.DRY_VAN)
    commodity_type: Mapped[str] = mapped_column(String(100), default="general")
    commodity_description: Mapped[Optional[str]] = mapped_column(Text)
    requires_liftgate: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_appointment: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_inside_delivery: Mapped[bool] = mapped_column(Boolean, default=False)
    temperature_min: Mapped[Optional[float]] = mapped_column(Float)
    temperature_max: Mapped[Optional[float]] = mapped_column(Float)

    # Pricing
    distance_miles: Mapped[float] = mapped_column(Float, nullable=False)
    quoted_price: Mapped[Optional[float]] = mapped_column(Float)
    final_price: Mapped[Optional[float]] = mapped_column(Float)
    market_rate: Mapped[Optional[float]] = mapped_column(Float)
    savings_percent: Mapped[Optional[float]] = mapped_column(Float)

    # Pooling
    pooled: Mapped[bool] = mapped_column(Boolean, default=False)
    pooling_probability: Mapped[Optional[float]] = mapped_column(Float)
    route_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("routes.id"))

    # Timestamps
    quoted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    booked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    picked_up_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shipper: Mapped["Shipper"] = relationship("Shipper", back_populates="shipments")
    route: Mapped[Optional["Route"]] = relationship("Route", back_populates="shipments")

    __table_args__ = (
        Index("ix_shipments_status", "status"),
        Index("ix_shipments_origin", "origin_state", "origin_city"),
        Index("ix_shipments_dest", "dest_state", "dest_city"),
        Index("ix_shipments_pickup", "pickup_earliest", "pickup_latest"),
        Index("ix_shipments_h3_origin", "origin_h3_index"),
        Index("ix_shipments_h3_dest", "dest_h3_index"),
        Index("ix_shipments_pooling", "pooled", "pooling_probability"),
    )


# ============= ROUTE =============

class Route(Base):
    """Route entity - optimized multi-stop routes"""
    __tablename__ = "routes"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    carrier_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("carriers.id"))

    # Status
    status: Mapped[str] = mapped_column(String(50), default="planned")

    # Metrics
    total_distance_miles: Mapped[float] = mapped_column(Float, default=0.0)
    total_duration_hours: Mapped[float] = mapped_column(Float, default=0.0)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    utilization_percent: Mapped[float] = mapped_column(Float, default=0.0)
    num_shipments: Mapped[int] = mapped_column(Integer, default=0)

    # Route details
    stops: Mapped[Optional[dict]] = mapped_column(JSON)  # JSON array of stops

    # Optimization
    optimization_score: Mapped[Optional[float]] = mapped_column(Float)
    carbon_saved_kg: Mapped[Optional[float]] = mapped_column(Float)

    # Timestamps
    planned_start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    planned_end: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actual_start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actual_end: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    carrier: Mapped[Optional["Carrier"]] = relationship("Carrier", back_populates="routes")
    shipments: Mapped[List["Shipment"]] = relationship("Shipment", back_populates="route")

    __table_args__ = (
        Index("ix_routes_status", "status"),
        Index("ix_routes_carrier", "carrier_id"),
        Index("ix_routes_dates", "planned_start", "planned_end"),
    )


# ============= QUOTE =============

class Quote(Base):
    """Quote entity - price quotes for shipments"""
    __tablename__ = "quotes"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    shipment_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False)

    # Pricing
    base_rate: Mapped[float] = mapped_column(Float, nullable=False)
    fuel_surcharge: Mapped[float] = mapped_column(Float, default=0.0)
    accessorial_charges: Mapped[float] = mapped_column(Float, default=0.0)
    pooling_discount: Mapped[float] = mapped_column(Float, default=0.0)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    rate_per_mile: Mapped[float] = mapped_column(Float, nullable=False)

    # ML predictions
    pooling_probability: Mapped[float] = mapped_column(Float, default=0.0)
    demand_score: Mapped[Optional[float]] = mapped_column(Float)
    dynamic_adjustment: Mapped[float] = mapped_column(Float, default=0.0)

    # Comparison
    market_rate: Mapped[Optional[float]] = mapped_column(Float)
    competitor_low: Mapped[Optional[float]] = mapped_column(Float)
    competitor_high: Mapped[Optional[float]] = mapped_column(Float)
    savings_vs_market: Mapped[Optional[float]] = mapped_column(Float)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="active")
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_quotes_shipment", "shipment_id"),
        Index("ix_quotes_status", "status", "valid_until"),
    )


# ============= POOLING MATCH =============

class PoolingMatch(Base):
    """Pooling match entity - potential pooling combinations"""
    __tablename__ = "pooling_matches"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Shipments involved
    shipment_ids: Mapped[list] = mapped_column(JSON, nullable=False)  # Array of UUIDs

    # Scores
    geographic_score: Mapped[float] = mapped_column(Float, nullable=False)
    temporal_score: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    ml_probability: Mapped[float] = mapped_column(Float, nullable=False)

    # Economics
    individual_cost_total: Mapped[float] = mapped_column(Float, nullable=False)
    pooled_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_savings: Mapped[float] = mapped_column(Float, nullable=False)
    savings_percent: Mapped[float] = mapped_column(Float, nullable=False)

    # Route info
    route_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("routes.id"))
    total_distance: Mapped[float] = mapped_column(Float, nullable=False)
    total_duration: Mapped[float] = mapped_column(Float, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="proposed")
    executed: Mapped[bool] = mapped_column(Boolean, default=False)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_pooling_score", "overall_score"),
        Index("ix_pooling_status", "status", "expires_at"),
    )
