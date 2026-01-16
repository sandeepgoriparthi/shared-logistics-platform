"""
Carrier API Routes

Carrier management and matching endpoints.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()
router = APIRouter()

# In-memory storage
carriers_db = {}


class CarrierCreateRequest(BaseModel):
    """Request to create/register a carrier"""
    name: str = Field(..., description="Carrier name")
    email: str = Field(..., description="Contact email")
    phone: Optional[str] = Field(None)
    mc_number: str = Field(..., description="MC number")
    dot_number: str = Field(..., description="DOT number")

    # Equipment
    equipment_type: str = Field("dry_van")
    trailer_count: int = Field(1, ge=1)
    driver_count: int = Field(1, ge=1)
    max_weight_lbs: float = Field(45000)
    trailer_length_feet: float = Field(53)

    # Capabilities
    hazmat_certified: bool = Field(False)
    team_drivers: bool = Field(False)

    # Preferences
    min_rate_per_mile: float = Field(2.00)
    max_deadhead_miles: float = Field(100)
    preferred_lanes: Optional[List[dict]] = Field(None)


class CarrierResponse(BaseModel):
    """Carrier response"""
    id: UUID
    name: str
    email: str
    mc_number: str
    dot_number: str
    equipment_type: str
    trailer_count: int
    driver_count: int

    # Performance
    on_time_percentage: float
    damage_free_percentage: float
    acceptance_rate: float
    total_loads: int
    total_miles: float

    # Location
    current_city: Optional[str]
    current_state: Optional[str]

    # Status
    status: str
    created_at: datetime


class CarrierAvailabilityRequest(BaseModel):
    """Update carrier availability"""
    available: bool = Field(True)
    current_latitude: float
    current_longitude: float
    current_city: str
    current_state: str
    available_from: datetime
    available_until: datetime
    available_capacity_feet: float = Field(53)
    available_weight_lbs: float = Field(45000)


class LoadMatchResponse(BaseModel):
    """Load match for carrier"""
    shipment_id: UUID
    origin_city: str
    origin_state: str
    dest_city: str
    dest_state: str
    distance_miles: float
    pickup_date: datetime
    delivery_date: datetime
    rate: float
    rate_per_mile: float
    linear_feet: float
    weight_lbs: float
    match_score: float


@router.post("", response_model=CarrierResponse)
async def register_carrier(request: CarrierCreateRequest):
    """
    Register a new carrier

    Carriers can sign up to receive load matches and earn revenue.
    """
    # Check for duplicate MC number
    for carrier in carriers_db.values():
        if carrier["mc_number"] == request.mc_number:
            raise HTTPException(status_code=400, detail="MC number already registered")

    carrier_id = uuid4()

    carrier = {
        "id": carrier_id,
        "name": request.name,
        "email": request.email,
        "phone": request.phone,
        "mc_number": request.mc_number,
        "dot_number": request.dot_number,
        "equipment_type": request.equipment_type,
        "trailer_count": request.trailer_count,
        "driver_count": request.driver_count,
        "max_weight_lbs": request.max_weight_lbs,
        "trailer_length_feet": request.trailer_length_feet,
        "hazmat_certified": request.hazmat_certified,
        "team_drivers": request.team_drivers,
        "min_rate_per_mile": request.min_rate_per_mile,
        "max_deadhead_miles": request.max_deadhead_miles,
        "preferred_lanes": request.preferred_lanes or [],
        "on_time_percentage": 95.0,
        "damage_free_percentage": 99.0,
        "acceptance_rate": 80.0,
        "total_loads": 0,
        "total_miles": 0.0,
        "current_city": None,
        "current_state": None,
        "current_latitude": None,
        "current_longitude": None,
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    carriers_db[carrier_id] = carrier

    logger.info(
        "carrier_registered",
        carrier_id=str(carrier_id),
        mc_number=request.mc_number
    )

    return CarrierResponse(
        id=carrier_id,
        name=carrier["name"],
        email=carrier["email"],
        mc_number=carrier["mc_number"],
        dot_number=carrier["dot_number"],
        equipment_type=carrier["equipment_type"],
        trailer_count=carrier["trailer_count"],
        driver_count=carrier["driver_count"],
        on_time_percentage=carrier["on_time_percentage"],
        damage_free_percentage=carrier["damage_free_percentage"],
        acceptance_rate=carrier["acceptance_rate"],
        total_loads=carrier["total_loads"],
        total_miles=carrier["total_miles"],
        current_city=carrier["current_city"],
        current_state=carrier["current_state"],
        status=carrier["status"],
        created_at=carrier["created_at"]
    )


@router.get("", response_model=List[CarrierResponse])
async def list_carriers(
    equipment_type: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    available: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """List carriers with filters"""
    results = []

    for carrier in list(carriers_db.values())[:limit]:
        if equipment_type and carrier["equipment_type"] != equipment_type:
            continue
        if state and carrier.get("current_state") != state:
            continue

        results.append(CarrierResponse(
            id=carrier["id"],
            name=carrier["name"],
            email=carrier["email"],
            mc_number=carrier["mc_number"],
            dot_number=carrier["dot_number"],
            equipment_type=carrier["equipment_type"],
            trailer_count=carrier["trailer_count"],
            driver_count=carrier["driver_count"],
            on_time_percentage=carrier["on_time_percentage"],
            damage_free_percentage=carrier["damage_free_percentage"],
            acceptance_rate=carrier["acceptance_rate"],
            total_loads=carrier["total_loads"],
            total_miles=carrier["total_miles"],
            current_city=carrier.get("current_city"),
            current_state=carrier.get("current_state"),
            status=carrier["status"],
            created_at=carrier["created_at"]
        ))

    return results


@router.get("/{carrier_id}", response_model=CarrierResponse)
async def get_carrier(carrier_id: UUID):
    """Get carrier details"""
    if carrier_id not in carriers_db:
        raise HTTPException(status_code=404, detail="Carrier not found")

    carrier = carriers_db[carrier_id]

    return CarrierResponse(
        id=carrier["id"],
        name=carrier["name"],
        email=carrier["email"],
        mc_number=carrier["mc_number"],
        dot_number=carrier["dot_number"],
        equipment_type=carrier["equipment_type"],
        trailer_count=carrier["trailer_count"],
        driver_count=carrier["driver_count"],
        on_time_percentage=carrier["on_time_percentage"],
        damage_free_percentage=carrier["damage_free_percentage"],
        acceptance_rate=carrier["acceptance_rate"],
        total_loads=carrier["total_loads"],
        total_miles=carrier["total_miles"],
        current_city=carrier.get("current_city"),
        current_state=carrier.get("current_state"),
        status=carrier["status"],
        created_at=carrier["created_at"]
    )


@router.put("/{carrier_id}/availability")
async def update_availability(carrier_id: UUID, request: CarrierAvailabilityRequest):
    """
    Update carrier availability and location

    Carriers should update their availability regularly for optimal matching.
    """
    if carrier_id not in carriers_db:
        raise HTTPException(status_code=404, detail="Carrier not found")

    carrier = carriers_db[carrier_id]

    carrier["current_latitude"] = request.current_latitude
    carrier["current_longitude"] = request.current_longitude
    carrier["current_city"] = request.current_city
    carrier["current_state"] = request.current_state
    carrier["available_from"] = request.available_from
    carrier["available_until"] = request.available_until
    carrier["available_capacity_feet"] = request.available_capacity_feet
    carrier["available_weight_lbs"] = request.available_weight_lbs
    carrier["updated_at"] = datetime.utcnow()

    logger.info(
        "carrier_availability_updated",
        carrier_id=str(carrier_id),
        city=request.current_city,
        state=request.current_state
    )

    return {"message": "Availability updated", "carrier_id": str(carrier_id)}


@router.get("/{carrier_id}/matches", response_model=List[LoadMatchResponse])
async def get_load_matches(
    carrier_id: UUID,
    max_deadhead: Optional[float] = Query(None),
    min_rate: Optional[float] = Query(None),
    limit: int = Query(20, ge=1, le=50)
):
    """
    Get load matches for a carrier

    Returns shipments that match the carrier's preferences and location.
    """
    if carrier_id not in carriers_db:
        raise HTTPException(status_code=404, detail="Carrier not found")

    carrier = carriers_db[carrier_id]

    from .shipments import shipments_db

    matches = []

    for shipment in shipments_db.values():
        if shipment["status"] not in ["booked", "pooled"]:
            continue
        if shipment.get("equipment_type") != carrier["equipment_type"]:
            continue

        # Check capacity
        if shipment["dimensions"]["linear_feet"] > carrier.get("available_capacity_feet", 53):
            continue
        if shipment["dimensions"]["weight_lbs"] > carrier.get("available_weight_lbs", 45000):
            continue

        # Calculate match score
        match_score = 0.5  # Base score

        # Boost for location proximity
        if carrier.get("current_state") == shipment["origin"].get("state"):
            match_score += 0.3

        # Boost for preferred lanes
        lane = (shipment["origin"].get("state"), shipment["destination"].get("state"))
        if carrier.get("preferred_lanes"):
            for pref in carrier["preferred_lanes"]:
                if pref.get("origin") == lane[0] and pref.get("dest") == lane[1]:
                    match_score += 0.2
                    break

        # Calculate rate
        rate = shipment.get("quoted_price", shipment["distance_miles"] * 2.5)
        rate_per_mile = rate / shipment["distance_miles"] if shipment["distance_miles"] > 0 else 0

        if min_rate and rate_per_mile < min_rate:
            continue

        pickup_earliest = shipment["pickup_window"]["earliest"]
        delivery_latest = shipment["delivery_window"]["latest"]

        if isinstance(pickup_earliest, str):
            pickup_earliest = datetime.fromisoformat(pickup_earliest)
        if isinstance(delivery_latest, str):
            delivery_latest = datetime.fromisoformat(delivery_latest)

        matches.append(LoadMatchResponse(
            shipment_id=shipment["id"],
            origin_city=shipment["origin"].get("city", ""),
            origin_state=shipment["origin"].get("state", ""),
            dest_city=shipment["destination"].get("city", ""),
            dest_state=shipment["destination"].get("state", ""),
            distance_miles=shipment["distance_miles"],
            pickup_date=pickup_earliest,
            delivery_date=delivery_latest,
            rate=rate,
            rate_per_mile=rate_per_mile,
            linear_feet=shipment["dimensions"]["linear_feet"],
            weight_lbs=shipment["dimensions"]["weight_lbs"],
            match_score=match_score
        ))

    # Sort by match score
    matches.sort(key=lambda x: x.match_score, reverse=True)

    return matches[:limit]


@router.post("/{carrier_id}/accept/{shipment_id}")
async def accept_load(carrier_id: UUID, shipment_id: UUID):
    """
    Accept a load/shipment

    Carrier commits to picking up and delivering the shipment.
    """
    if carrier_id not in carriers_db:
        raise HTTPException(status_code=404, detail="Carrier not found")

    from .shipments import shipments_db

    if shipment_id not in shipments_db:
        raise HTTPException(status_code=404, detail="Shipment not found")

    carrier = carriers_db[carrier_id]
    shipment = shipments_db[shipment_id]

    if shipment["status"] not in ["booked", "pooled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot accept shipment in status: {shipment['status']}"
        )

    # Assign carrier
    shipment["carrier_id"] = carrier_id
    shipment["status"] = "assigned"
    shipment["updated_at"] = datetime.utcnow()

    # Update carrier stats
    carrier["total_loads"] += 1
    carrier["total_miles"] += shipment["distance_miles"]

    logger.info(
        "load_accepted",
        carrier_id=str(carrier_id),
        shipment_id=str(shipment_id)
    )

    return {
        "message": "Load accepted",
        "carrier_id": str(carrier_id),
        "shipment_id": str(shipment_id),
        "pickup_window": shipment["pickup_window"],
        "delivery_window": shipment["delivery_window"]
    }
