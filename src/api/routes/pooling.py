"""
Pooling API Routes

Shipment pooling and matching endpoints.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()
router = APIRouter()

# In-memory storage
pooling_matches_db = {}

from .shipments import shipments_db


class PoolingMatchResponse(BaseModel):
    """Pooling match response"""
    id: UUID
    shipment_ids: List[UUID]
    num_shipments: int

    # Scores
    geographic_score: float
    temporal_score: float
    capacity_score: float
    overall_score: float
    ml_probability: float

    # Savings
    individual_cost_total: float
    pooled_cost: float
    total_savings: float
    savings_percent: float

    # Route info
    total_distance_miles: float
    total_duration_hours: float
    estimated_utilization: float

    # Status
    status: str
    expires_at: datetime


class OptimizePoolingRequest(BaseModel):
    """Request to optimize pooling for shipments"""
    shipment_ids: Optional[List[UUID]] = Field(None, description="Specific shipments to pool")
    origin_state: Optional[str] = Field(None, description="Filter by origin state")
    dest_state: Optional[str] = Field(None, description="Filter by destination state")
    max_shipments_per_pool: int = Field(4, ge=2, le=6)
    min_savings_percent: float = Field(10.0, ge=0, le=50)


class ExecutePoolingRequest(BaseModel):
    """Request to execute a pooling match"""
    match_id: UUID
    confirm: bool = Field(True)


def calculate_pooling_score(shipments: list) -> dict:
    """Calculate pooling scores for a set of shipments"""
    if len(shipments) < 2:
        return {"overall_score": 0}

    # Geographic score - based on origin/dest proximity
    geo_scores = []
    for i, s1 in enumerate(shipments):
        for s2 in shipments[i+1:]:
            # Simple distance-based score
            origin_dist = abs(
                (s1["origin"].get("latitude", 0) - s2["origin"].get("latitude", 0)) +
                (s1["origin"].get("longitude", 0) - s2["origin"].get("longitude", 0))
            ) * 50  # Rough miles
            dest_dist = abs(
                (s1["destination"].get("latitude", 0) - s2["destination"].get("latitude", 0)) +
                (s1["destination"].get("longitude", 0) - s2["destination"].get("longitude", 0))
            ) * 50

            geo_score = max(0, 1 - (origin_dist + dest_dist) / 200)
            geo_scores.append(geo_score)

    geographic_score = sum(geo_scores) / len(geo_scores) if geo_scores else 0

    # Temporal score - based on time window overlap
    temporal_scores = []
    for i, s1 in enumerate(shipments):
        for s2 in shipments[i+1:]:
            # Check pickup window overlap
            p1_start = s1["pickup_window"]["earliest"]
            p1_end = s1["pickup_window"]["latest"]
            p2_start = s2["pickup_window"]["earliest"]
            p2_end = s2["pickup_window"]["latest"]

            if isinstance(p1_start, str):
                p1_start = datetime.fromisoformat(p1_start)
            if isinstance(p1_end, str):
                p1_end = datetime.fromisoformat(p1_end)
            if isinstance(p2_start, str):
                p2_start = datetime.fromisoformat(p2_start)
            if isinstance(p2_end, str):
                p2_end = datetime.fromisoformat(p2_end)

            overlap = max(0, min(p1_end, p2_end).timestamp() - max(p1_start, p2_start).timestamp())
            max_overlap = max((p1_end - p1_start).total_seconds(), (p2_end - p2_start).total_seconds())

            temp_score = overlap / max_overlap if max_overlap > 0 else 0
            temporal_scores.append(temp_score)

    temporal_score = sum(temporal_scores) / len(temporal_scores) if temporal_scores else 0

    # Capacity score - based on utilization
    total_linear_feet = sum(s["dimensions"]["linear_feet"] for s in shipments)
    total_weight = sum(s["dimensions"]["weight_lbs"] for s in shipments)

    feet_util = min(total_linear_feet / 53, 1)
    weight_util = min(total_weight / 45000, 1)

    # Ideal utilization is 70-95%
    if 0.7 <= feet_util <= 0.95:
        capacity_score = 1.0
    elif feet_util > 0.95:
        capacity_score = 0.5  # Too full, risk of overflow
    else:
        capacity_score = feet_util / 0.7

    # Overall score
    overall_score = (
        0.4 * geographic_score +
        0.3 * temporal_score +
        0.3 * capacity_score
    )

    return {
        "geographic_score": geographic_score,
        "temporal_score": temporal_score,
        "capacity_score": capacity_score,
        "overall_score": overall_score,
        "ml_probability": overall_score * 0.9,  # Placeholder for ML prediction
        "utilization": feet_util
    }


@router.post("/optimize", response_model=List[PoolingMatchResponse])
async def optimize_pooling(request: OptimizePoolingRequest):
    """
    Find optimal pooling opportunities

    Uses ML and optimization algorithms to identify shipments
    that can be efficiently pooled together.
    """
    # Get eligible shipments
    eligible = []

    for shipment_id, shipment in shipments_db.items():
        if shipment["status"] not in ["pending", "quoted", "booked"]:
            continue
        if shipment["pooled"]:
            continue
        if request.shipment_ids and shipment_id not in request.shipment_ids:
            continue
        if request.origin_state and shipment["origin"].get("state") != request.origin_state:
            continue
        if request.dest_state and shipment["destination"].get("state") != request.dest_state:
            continue

        eligible.append(shipment)

    if len(eligible) < 2:
        return []

    # Find pooling matches
    # In production, this would use the ML pooling predictor and optimization
    matches = []

    # Simple greedy matching for demo
    used = set()

    for i, s1 in enumerate(eligible):
        if s1["id"] in used:
            continue

        pool = [s1]
        used.add(s1["id"])

        for s2 in eligible[i+1:]:
            if s2["id"] in used:
                continue
            if len(pool) >= request.max_shipments_per_pool:
                break

            # Check basic compatibility
            if s1.get("equipment_type") != s2.get("equipment_type"):
                continue

            # Check capacity
            current_feet = sum(p["dimensions"]["linear_feet"] for p in pool)
            if current_feet + s2["dimensions"]["linear_feet"] > 53:
                continue

            current_weight = sum(p["dimensions"]["weight_lbs"] for p in pool)
            if current_weight + s2["dimensions"]["weight_lbs"] > 45000:
                continue

            pool.append(s2)
            used.add(s2["id"])

        if len(pool) >= 2:
            # Calculate scores
            scores = calculate_pooling_score(pool)

            # Calculate savings
            individual_cost = sum(p["distance_miles"] * 2.5 for p in pool)
            # Pooled cost is roughly 60-80% of individual
            pooled_cost = individual_cost * (1 - scores["overall_score"] * 0.4)
            savings = individual_cost - pooled_cost
            savings_percent = (savings / individual_cost) * 100 if individual_cost > 0 else 0

            if savings_percent >= request.min_savings_percent:
                match_id = uuid4()

                match = {
                    "id": match_id,
                    "shipment_ids": [p["id"] for p in pool],
                    "num_shipments": len(pool),
                    **scores,
                    "individual_cost_total": individual_cost,
                    "pooled_cost": pooled_cost,
                    "total_savings": savings,
                    "savings_percent": savings_percent,
                    "total_distance_miles": sum(p["distance_miles"] for p in pool) * 0.7,  # Reduced due to sharing
                    "total_duration_hours": sum(p["distance_miles"] for p in pool) * 0.7 / 50,
                    "estimated_utilization": scores["utilization"],
                    "status": "proposed",
                    "expires_at": datetime.utcnow() + timedelta(hours=4),
                    "created_at": datetime.utcnow()
                }

                pooling_matches_db[match_id] = match
                matches.append(PoolingMatchResponse(**match))

    # Sort by savings
    matches.sort(key=lambda x: x.savings_percent, reverse=True)

    logger.info(
        "pooling_optimization_complete",
        eligible_shipments=len(eligible),
        matches_found=len(matches),
        total_potential_savings=sum(m.total_savings for m in matches)
    )

    return matches


@router.get("/matches", response_model=List[PoolingMatchResponse])
async def list_pooling_matches(
    status: Optional[str] = Query(None),
    min_savings: Optional[float] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """List all pooling matches"""
    results = []

    for match in list(pooling_matches_db.values())[:limit]:
        if status and match["status"] != status:
            continue
        if min_savings and match["savings_percent"] < min_savings:
            continue

        # Check expiry
        if datetime.utcnow() > match["expires_at"] and match["status"] == "proposed":
            match["status"] = "expired"

        results.append(PoolingMatchResponse(**match))

    return sorted(results, key=lambda x: x.savings_percent, reverse=True)


@router.get("/matches/{match_id}", response_model=PoolingMatchResponse)
async def get_pooling_match(match_id: UUID):
    """Get pooling match details"""
    if match_id not in pooling_matches_db:
        raise HTTPException(status_code=404, detail="Pooling match not found")

    match = pooling_matches_db[match_id]

    # Check expiry
    if datetime.utcnow() > match["expires_at"] and match["status"] == "proposed":
        match["status"] = "expired"

    return PoolingMatchResponse(**match)


@router.post("/matches/{match_id}/execute")
async def execute_pooling(match_id: UUID, request: ExecutePoolingRequest):
    """
    Execute a pooling match

    This locks in the pooling arrangement and updates all involved shipments.
    """
    if match_id not in pooling_matches_db:
        raise HTTPException(status_code=404, detail="Pooling match not found")

    match = pooling_matches_db[match_id]

    if match["status"] != "proposed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot execute match in status: {match['status']}"
        )

    if datetime.utcnow() > match["expires_at"]:
        match["status"] = "expired"
        raise HTTPException(status_code=400, detail="Match has expired")

    if not request.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")

    # Execute pooling
    match["status"] = "executed"
    match["executed_at"] = datetime.utcnow()

    # Update shipments
    for shipment_id in match["shipment_ids"]:
        if shipment_id in shipments_db:
            shipment = shipments_db[shipment_id]
            shipment["pooled"] = True
            shipment["status"] = "pooled"

            # Apply savings
            original_price = shipment.get("quoted_price", 0)
            savings_ratio = match["savings_percent"] / 100
            shipment["final_price"] = original_price * (1 - savings_ratio)
            shipment["savings_percent"] = match["savings_percent"]
            shipment["updated_at"] = datetime.utcnow()

    logger.info(
        "pooling_executed",
        match_id=str(match_id),
        num_shipments=match["num_shipments"],
        total_savings=match["total_savings"]
    )

    return {
        "message": "Pooling executed successfully",
        "match_id": str(match_id),
        "shipments_pooled": match["num_shipments"],
        "total_savings": match["total_savings"],
        "savings_percent": match["savings_percent"]
    }


@router.get("/stats")
async def get_pooling_stats():
    """Get pooling statistics"""
    total_matches = len(pooling_matches_db)
    executed = sum(1 for m in pooling_matches_db.values() if m["status"] == "executed")
    total_savings = sum(
        m["total_savings"] for m in pooling_matches_db.values()
        if m["status"] == "executed"
    )
    avg_savings_percent = (
        sum(m["savings_percent"] for m in pooling_matches_db.values() if m["status"] == "executed") / executed
        if executed > 0 else 0
    )

    return {
        "total_matches_found": total_matches,
        "matches_executed": executed,
        "total_savings_dollars": total_savings,
        "average_savings_percent": avg_savings_percent,
        "pooling_success_rate": executed / total_matches * 100 if total_matches > 0 else 0
    }
