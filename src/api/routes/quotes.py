"""
Quote API Routes

Dynamic pricing and quote generation endpoints.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, Query
import structlog

from ..schemas.shipment import QuoteRequest, QuoteResponse

logger = structlog.get_logger()
router = APIRouter()

# In-memory storage for demo
quotes_db = {}

# Reference to shipments (in production, use proper dependency injection)
from .shipments import shipments_db


@router.post("", response_model=QuoteResponse)
async def create_quote(request: QuoteRequest):
    """
    Generate a price quote for a shipment

    Uses dynamic pricing with:
    - ML-based demand forecasting
    - Pooling probability estimation
    - Real-time market rate analysis
    - Capacity utilization optimization
    """
    # Get shipment
    if request.shipment_id:
        if request.shipment_id not in shipments_db:
            raise HTTPException(status_code=404, detail="Shipment not found")
        shipment = shipments_db[request.shipment_id]
        shipment_id = request.shipment_id
    else:
        # Create new shipment from request
        raise HTTPException(
            status_code=400,
            detail="Creating shipment in quote not implemented. Create shipment first."
        )

    distance = shipment["distance_miles"]
    weight = shipment["dimensions"]["weight_lbs"]
    linear_feet = shipment["dimensions"]["linear_feet"]

    # Dynamic pricing calculation
    # Base rate varies by market conditions (simplified)
    base_rate_per_mile = 2.50

    # Adjust for demand (ML prediction placeholder)
    demand_multiplier = 1.0 + (0.1 if distance > 500 else -0.05)

    # Adjust for capacity utilization
    utilization = linear_feet / 53
    utilization_multiplier = 1.0 if utilization > 0.5 else 1.1  # Premium for low utilization

    # Calculate base rate
    adjusted_rate = base_rate_per_mile * demand_multiplier * utilization_multiplier
    base_cost = distance * adjusted_rate

    # Fuel surcharge (typically 15-20% of base)
    fuel_surcharge = base_cost * 0.15

    # Accessorials
    accessorial_charges = 0.0
    if shipment.get("requires_liftgate"):
        accessorial_charges += 75.0
    if shipment.get("requires_appointment"):
        accessorial_charges += 50.0
    if shipment.get("requires_inside_delivery"):
        accessorial_charges += 100.0

    # Pooling discount
    pooling_probability = shipment.get("pooling_probability", 0.5)
    pooling_discount = 0.0

    if pooling_probability > 0.6:
        # High probability of pooling - offer discount
        pooling_discount = base_cost * 0.20 * pooling_probability
    elif pooling_probability > 0.3:
        pooling_discount = base_cost * 0.10 * pooling_probability

    # Total price
    total_price = base_cost + fuel_surcharge + accessorial_charges - pooling_discount
    rate_per_mile = total_price / distance if distance > 0 else 0

    # Market comparison (placeholder - would use real market data)
    market_rate = distance * 2.80  # Competitor average
    savings_vs_market = ((market_rate - total_price) / market_rate) * 100 if market_rate > 0 else 0

    # Create quote
    quote_id = uuid4()
    quote = {
        "id": quote_id,
        "shipment_id": shipment_id,
        "base_rate": base_cost,
        "fuel_surcharge": fuel_surcharge,
        "accessorial_charges": accessorial_charges,
        "pooling_discount": pooling_discount,
        "total_price": total_price,
        "rate_per_mile": rate_per_mile,
        "pooling_probability": pooling_probability,
        "demand_score": demand_multiplier,
        "dynamic_adjustment": (demand_multiplier - 1) * 100,
        "market_rate": market_rate,
        "competitor_low": market_rate * 0.9,
        "competitor_high": market_rate * 1.2,
        "savings_vs_market": savings_vs_market,
        "status": "active",
        "valid_until": datetime.utcnow() + timedelta(hours=24),
        "accepted": False,
        "created_at": datetime.utcnow()
    }

    quotes_db[quote_id] = quote

    # Update shipment with quote
    shipment["quoted_price"] = total_price
    shipment["status"] = "quoted"
    shipment["savings_percent"] = savings_vs_market
    shipment["updated_at"] = datetime.utcnow()

    logger.info(
        "quote_created",
        quote_id=str(quote_id),
        shipment_id=str(shipment_id),
        total_price=total_price,
        pooling_probability=pooling_probability,
        savings=savings_vs_market
    )

    return QuoteResponse(
        id=quote_id,
        shipment_id=shipment_id,
        base_rate=base_cost,
        fuel_surcharge=fuel_surcharge,
        accessorial_charges=accessorial_charges,
        pooling_discount=pooling_discount,
        total_price=total_price,
        rate_per_mile=rate_per_mile,
        market_rate=market_rate,
        savings_vs_market=savings_vs_market,
        pooling_probability=pooling_probability,
        estimated_pooling_savings=pooling_discount * 1.5 if pooling_probability > 0.7 else None,
        valid_until=quote["valid_until"],
        status="active"
    )


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: UUID):
    """Get quote details"""
    if quote_id not in quotes_db:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote = quotes_db[quote_id]

    # Check if expired
    if datetime.utcnow() > quote["valid_until"]:
        quote["status"] = "expired"

    return QuoteResponse(
        id=quote["id"],
        shipment_id=quote["shipment_id"],
        base_rate=quote["base_rate"],
        fuel_surcharge=quote["fuel_surcharge"],
        accessorial_charges=quote["accessorial_charges"],
        pooling_discount=quote["pooling_discount"],
        total_price=quote["total_price"],
        rate_per_mile=quote["rate_per_mile"],
        market_rate=quote["market_rate"],
        savings_vs_market=quote["savings_vs_market"],
        pooling_probability=quote["pooling_probability"],
        estimated_pooling_savings=quote["pooling_discount"] * 1.5 if quote["pooling_probability"] > 0.7 else None,
        valid_until=quote["valid_until"],
        status=quote["status"]
    )


@router.post("/{quote_id}/accept")
async def accept_quote(quote_id: UUID):
    """
    Accept a quote and proceed to booking

    This locks in the price and initiates the booking process.
    """
    if quote_id not in quotes_db:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote = quotes_db[quote_id]

    # Check validity
    if datetime.utcnow() > quote["valid_until"]:
        raise HTTPException(status_code=400, detail="Quote has expired")

    if quote["accepted"]:
        raise HTTPException(status_code=400, detail="Quote already accepted")

    # Accept quote
    quote["accepted"] = True
    quote["accepted_at"] = datetime.utcnow()
    quote["status"] = "accepted"

    logger.info(
        "quote_accepted",
        quote_id=str(quote_id),
        shipment_id=str(quote["shipment_id"]),
        price=quote["total_price"]
    )

    return {
        "message": "Quote accepted",
        "quote_id": str(quote_id),
        "shipment_id": str(quote["shipment_id"]),
        "next_step": f"/api/v1/shipments/{quote['shipment_id']}/book"
    }


@router.get("", response_model=List[QuoteResponse])
async def list_quotes(
    shipment_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """List quotes with optional filters"""
    results = []

    for quote in list(quotes_db.values())[:limit]:
        if shipment_id and quote["shipment_id"] != shipment_id:
            continue
        if status and quote["status"] != status:
            continue

        # Check if expired
        if datetime.utcnow() > quote["valid_until"] and quote["status"] == "active":
            quote["status"] = "expired"

        results.append(QuoteResponse(
            id=quote["id"],
            shipment_id=quote["shipment_id"],
            base_rate=quote["base_rate"],
            fuel_surcharge=quote["fuel_surcharge"],
            accessorial_charges=quote["accessorial_charges"],
            pooling_discount=quote["pooling_discount"],
            total_price=quote["total_price"],
            rate_per_mile=quote["rate_per_mile"],
            market_rate=quote["market_rate"],
            savings_vs_market=quote["savings_vs_market"],
            pooling_probability=quote["pooling_probability"],
            estimated_pooling_savings=quote["pooling_discount"] * 1.5 if quote["pooling_probability"] > 0.7 else None,
            valid_until=quote["valid_until"],
            status=quote["status"]
        ))

    return results


@router.post("/bulk")
async def bulk_quote(shipment_ids: List[UUID]):
    """
    Generate quotes for multiple shipments at once

    Useful for batch pricing and comparison.
    """
    results = []

    for shipment_id in shipment_ids:
        try:
            request = QuoteRequest(shipment_id=shipment_id)
            quote = await create_quote(request)
            results.append({"shipment_id": str(shipment_id), "quote": quote})
        except HTTPException as e:
            results.append({"shipment_id": str(shipment_id), "error": e.detail})

    return {"quotes": results, "total": len(results)}
