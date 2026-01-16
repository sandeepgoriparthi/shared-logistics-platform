"""
Shipment API Routes
"""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, Query, Depends
import structlog

from ..schemas.shipment import (
    ShipmentCreateRequest,
    ShipmentResponse,
    BookingRequest,
    BookingResponse,
    TrackingResponse,
    LocationSchema,
    TimeWindowSchema,
    DimensionsSchema
)

logger = structlog.get_logger()
router = APIRouter()


# In-memory storage for demo (replace with database in production)
shipments_db = {}


def calculate_distance(origin: LocationSchema, destination: LocationSchema) -> float:
    """Calculate haversine distance between two points"""
    from math import radians, cos, sin, asin, sqrt

    if origin.latitude is None or destination.latitude is None:
        return 500.0  # Default distance

    lat1, lon1 = radians(origin.latitude), radians(origin.longitude)
    lat2, lon2 = radians(destination.latitude), radians(destination.longitude)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    return c * 3956  # Earth radius in miles


@router.post("", response_model=ShipmentResponse)
async def create_shipment(request: ShipmentCreateRequest):
    """
    Create a new shipment

    This endpoint creates a shipment and automatically:
    - Calculates distance and estimated cost
    - Predicts pooling probability using ML
    - Finds potential pooling matches
    """
    shipment_id = uuid4()
    reference_number = f"SLP-{datetime.now().strftime('%Y%m%d')}-{str(shipment_id)[:8].upper()}"

    # Calculate distance
    distance = calculate_distance(request.origin, request.destination)

    # Create shipment record
    shipment = {
        "id": shipment_id,
        "reference_number": reference_number,
        "status": "pending",
        "origin": request.origin.model_dump(),
        "destination": request.destination.model_dump(),
        "pickup_window": request.pickup_window.model_dump(),
        "delivery_window": request.delivery_window.model_dump(),
        "dimensions": request.dimensions.model_dump(),
        "equipment_type": request.equipment_type,
        "commodity_type": request.commodity_type,
        "distance_miles": distance,
        "quoted_price": None,
        "final_price": None,
        "savings_percent": None,
        "pooled": False,
        "pooling_probability": 0.65,  # ML prediction placeholder
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    shipments_db[shipment_id] = shipment

    logger.info(
        "shipment_created",
        shipment_id=str(shipment_id),
        distance=distance,
        pooling_probability=0.65
    )

    return ShipmentResponse(
        id=shipment_id,
        reference_number=reference_number,
        status="pending",
        origin=LocationSchema(**shipment["origin"]),
        destination=LocationSchema(**shipment["destination"]),
        pickup_window=TimeWindowSchema(**shipment["pickup_window"]),
        delivery_window=TimeWindowSchema(**shipment["delivery_window"]),
        dimensions=DimensionsSchema(**shipment["dimensions"]),
        distance_miles=distance,
        quoted_price=None,
        final_price=None,
        savings_percent=None,
        pooled=False,
        pooling_probability=0.65,
        created_at=shipment["created_at"],
        updated_at=shipment["updated_at"]
    )


@router.get("", response_model=List[ShipmentResponse])
async def list_shipments(
    status: Optional[str] = Query(None, description="Filter by status"),
    origin_state: Optional[str] = Query(None, description="Filter by origin state"),
    dest_state: Optional[str] = Query(None, description="Filter by destination state"),
    pooled: Optional[bool] = Query(None, description="Filter by pooling status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List shipments with optional filters
    """
    results = []

    for shipment in list(shipments_db.values())[offset:offset+limit]:
        if status and shipment["status"] != status:
            continue
        if origin_state and shipment["origin"].get("state") != origin_state:
            continue
        if dest_state and shipment["destination"].get("state") != dest_state:
            continue
        if pooled is not None and shipment["pooled"] != pooled:
            continue

        results.append(ShipmentResponse(
            id=shipment["id"],
            reference_number=shipment["reference_number"],
            status=shipment["status"],
            origin=LocationSchema(**shipment["origin"]),
            destination=LocationSchema(**shipment["destination"]),
            pickup_window=TimeWindowSchema(**shipment["pickup_window"]),
            delivery_window=TimeWindowSchema(**shipment["delivery_window"]),
            dimensions=DimensionsSchema(**shipment["dimensions"]),
            distance_miles=shipment["distance_miles"],
            quoted_price=shipment["quoted_price"],
            final_price=shipment["final_price"],
            savings_percent=shipment["savings_percent"],
            pooled=shipment["pooled"],
            pooling_probability=shipment["pooling_probability"],
            created_at=shipment["created_at"],
            updated_at=shipment["updated_at"]
        ))

    return results


@router.get("/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(shipment_id: UUID):
    """Get shipment details by ID"""
    if shipment_id not in shipments_db:
        raise HTTPException(status_code=404, detail="Shipment not found")

    shipment = shipments_db[shipment_id]

    return ShipmentResponse(
        id=shipment["id"],
        reference_number=shipment["reference_number"],
        status=shipment["status"],
        origin=LocationSchema(**shipment["origin"]),
        destination=LocationSchema(**shipment["destination"]),
        pickup_window=TimeWindowSchema(**shipment["pickup_window"]),
        delivery_window=TimeWindowSchema(**shipment["delivery_window"]),
        dimensions=DimensionsSchema(**shipment["dimensions"]),
        distance_miles=shipment["distance_miles"],
        quoted_price=shipment["quoted_price"],
        final_price=shipment["final_price"],
        savings_percent=shipment["savings_percent"],
        pooled=shipment["pooled"],
        pooling_probability=shipment["pooling_probability"],
        created_at=shipment["created_at"],
        updated_at=shipment["updated_at"]
    )


@router.post("/{shipment_id}/book", response_model=BookingResponse)
async def book_shipment(shipment_id: UUID, request: BookingRequest):
    """
    Book a shipment after accepting a quote

    This confirms the shipment and assigns it to the optimization queue
    for carrier matching and route building.
    """
    if shipment_id not in shipments_db:
        raise HTTPException(status_code=404, detail="Shipment not found")

    shipment = shipments_db[shipment_id]

    if shipment["status"] != "quoted":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot book shipment in status: {shipment['status']}"
        )

    # Update shipment status
    shipment["status"] = "booked"
    shipment["final_price"] = shipment["quoted_price"]
    shipment["updated_at"] = datetime.utcnow()

    booking_number = f"BK-{str(shipment_id)[:8].upper()}"

    logger.info(
        "shipment_booked",
        shipment_id=str(shipment_id),
        booking_number=booking_number,
        price=shipment["final_price"]
    )

    return BookingResponse(
        shipment_id=shipment_id,
        booking_number=booking_number,
        status="booked",
        total_price=shipment["final_price"],
        pickup_window=TimeWindowSchema(**shipment["pickup_window"]),
        delivery_window=TimeWindowSchema(**shipment["delivery_window"]),
        estimated_delivery=datetime.fromisoformat(shipment["delivery_window"]["latest"].isoformat() if isinstance(shipment["delivery_window"]["latest"], datetime) else shipment["delivery_window"]["latest"]),
        tracking_url=f"/api/v1/shipments/{shipment_id}/tracking"
    )


@router.get("/{shipment_id}/tracking", response_model=TrackingResponse)
async def get_tracking(shipment_id: UUID):
    """
    Get real-time tracking information for a shipment
    """
    if shipment_id not in shipments_db:
        raise HTTPException(status_code=404, detail="Shipment not found")

    shipment = shipments_db[shipment_id]

    # Build tracking events timeline
    events = [
        {
            "timestamp": shipment["created_at"].isoformat(),
            "event": "Shipment created",
            "location": shipment["origin"].get("city", "")
        },
    ]

    if shipment["status"] in ["quoted", "booked", "pooled", "in_transit", "delivered"]:
        events.append({
            "timestamp": shipment["updated_at"].isoformat(),
            "event": f"Status updated to {shipment['status']}",
            "location": None
        })

    return TrackingResponse(
        shipment_id=shipment_id,
        status=shipment["status"],
        current_location=None,
        last_update=shipment["updated_at"],
        events=events,
        estimated_pickup=datetime.fromisoformat(shipment["pickup_window"]["earliest"].isoformat() if isinstance(shipment["pickup_window"]["earliest"], datetime) else shipment["pickup_window"]["earliest"]),
        estimated_delivery=datetime.fromisoformat(shipment["delivery_window"]["latest"].isoformat() if isinstance(shipment["delivery_window"]["latest"], datetime) else shipment["delivery_window"]["latest"]),
        actual_pickup=None,
        actual_delivery=None,
        route_id=None,
        carrier_name=None,
        driver_name=None,
        driver_phone=None
    )


@router.delete("/{shipment_id}")
async def cancel_shipment(shipment_id: UUID):
    """
    Cancel a shipment

    Only pending or quoted shipments can be cancelled.
    Booked shipments require contacting support.
    """
    if shipment_id not in shipments_db:
        raise HTTPException(status_code=404, detail="Shipment not found")

    shipment = shipments_db[shipment_id]

    if shipment["status"] not in ["pending", "quoted"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel shipment in status: {shipment['status']}"
        )

    shipment["status"] = "cancelled"
    shipment["updated_at"] = datetime.utcnow()

    logger.info("shipment_cancelled", shipment_id=str(shipment_id))

    return {"message": "Shipment cancelled successfully", "shipment_id": str(shipment_id)}
