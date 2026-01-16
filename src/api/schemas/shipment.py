"""
API Schemas for Shipments
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class LocationSchema(BaseModel):
    """Location details"""
    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State code (e.g., CA, TX)")
    zip_code: str = Field(..., description="ZIP code")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")


class TimeWindowSchema(BaseModel):
    """Time window for pickup/delivery"""
    earliest: datetime = Field(..., description="Earliest time")
    latest: datetime = Field(..., description="Latest time")

    @field_validator("latest")
    @classmethod
    def latest_after_earliest(cls, v, info):
        if "earliest" in info.data and v < info.data["earliest"]:
            raise ValueError("Latest time must be after earliest time")
        return v


class DimensionsSchema(BaseModel):
    """Physical dimensions of shipment"""
    weight_lbs: float = Field(..., ge=1, le=45000, description="Weight in pounds")
    linear_feet: float = Field(..., ge=1, le=53, description="Linear feet")
    pallet_count: int = Field(0, ge=0, le=26, description="Number of pallets")
    piece_count: int = Field(1, ge=1, description="Number of pieces")
    stackable: bool = Field(True, description="Whether freight is stackable")


class ShipmentCreateRequest(BaseModel):
    """Request to create a new shipment"""
    # Locations
    origin: LocationSchema
    destination: LocationSchema

    # Time windows
    pickup_window: TimeWindowSchema
    delivery_window: TimeWindowSchema

    # Physical attributes
    dimensions: DimensionsSchema

    # Requirements
    equipment_type: str = Field("dry_van", description="Equipment type required")
    commodity_type: str = Field("general", description="Type of commodity")
    commodity_description: Optional[str] = Field(None, description="Description of goods")
    requires_liftgate: bool = Field(False)
    requires_appointment: bool = Field(False)
    requires_inside_delivery: bool = Field(False)
    hazmat: bool = Field(False, description="Hazardous materials")
    temperature_min: Optional[float] = Field(None, description="Minimum temperature (F)")
    temperature_max: Optional[float] = Field(None, description="Maximum temperature (F)")

    # Optional
    reference_number: Optional[str] = Field(None, description="Customer reference number")
    special_instructions: Optional[str] = Field(None)


class ShipmentResponse(BaseModel):
    """Shipment response"""
    id: UUID
    reference_number: str
    status: str

    # Locations
    origin: LocationSchema
    destination: LocationSchema

    # Time windows
    pickup_window: TimeWindowSchema
    delivery_window: TimeWindowSchema

    # Dimensions
    dimensions: DimensionsSchema

    # Pricing
    distance_miles: float
    quoted_price: Optional[float]
    final_price: Optional[float]
    savings_percent: Optional[float]

    # Pooling
    pooled: bool
    pooling_probability: Optional[float]

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuoteRequest(BaseModel):
    """Request for a price quote"""
    shipment_id: Optional[UUID] = Field(None, description="Existing shipment ID")
    shipment: Optional[ShipmentCreateRequest] = Field(None, description="New shipment details")

    @field_validator("shipment")
    @classmethod
    def shipment_or_id_required(cls, v, info):
        if v is None and info.data.get("shipment_id") is None:
            raise ValueError("Either shipment_id or shipment details required")
        return v


class QuoteResponse(BaseModel):
    """Price quote response"""
    id: UUID
    shipment_id: UUID

    # Pricing breakdown
    base_rate: float = Field(..., description="Base rate")
    fuel_surcharge: float = Field(..., description="Fuel surcharge")
    accessorial_charges: float = Field(0, description="Additional charges")
    pooling_discount: float = Field(0, description="Discount from pooling")
    total_price: float = Field(..., description="Total price")
    rate_per_mile: float = Field(..., description="Rate per mile")

    # Comparisons
    market_rate: Optional[float] = Field(None, description="Current market rate")
    savings_vs_market: Optional[float] = Field(None, description="Savings vs market (%)")

    # Pooling info
    pooling_probability: float = Field(..., description="Probability of pooling (0-1)")
    estimated_pooling_savings: Optional[float] = Field(None, description="Additional savings if pooled")

    # Validity
    valid_until: datetime
    status: str

    class Config:
        from_attributes = True


class BookingRequest(BaseModel):
    """Request to book a shipment"""
    quote_id: UUID = Field(..., description="Quote ID to accept")
    payment_method: str = Field("invoice", description="Payment method")
    po_number: Optional[str] = Field(None, description="Purchase order number")
    special_instructions: Optional[str] = Field(None)


class BookingResponse(BaseModel):
    """Booking confirmation response"""
    shipment_id: UUID
    booking_number: str
    status: str
    total_price: float
    pickup_window: TimeWindowSchema
    delivery_window: TimeWindowSchema
    estimated_delivery: datetime
    tracking_url: str

    class Config:
        from_attributes = True


class TrackingResponse(BaseModel):
    """Shipment tracking response"""
    shipment_id: UUID
    status: str
    current_location: Optional[LocationSchema]
    last_update: datetime

    # Timeline
    events: List[dict]  # List of tracking events

    # ETA
    estimated_pickup: Optional[datetime]
    estimated_delivery: Optional[datetime]
    actual_pickup: Optional[datetime]
    actual_delivery: Optional[datetime]

    # Route info
    route_id: Optional[UUID]
    carrier_name: Optional[str]
    driver_name: Optional[str]
    driver_phone: Optional[str]

    class Config:
        from_attributes = True
