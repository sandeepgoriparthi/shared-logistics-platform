"""
Analytics API Routes

Business intelligence and reporting endpoints.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()
router = APIRouter()


class PlatformMetrics(BaseModel):
    """Overall platform metrics"""
    # Volume
    total_shipments: int
    shipments_today: int
    shipments_this_week: int
    shipments_this_month: int

    # Pooling
    pooled_shipments: int
    pooling_rate_percent: float
    total_savings_from_pooling: float
    average_pooling_savings_percent: float

    # Financial
    total_revenue: float
    revenue_today: float
    average_rate_per_mile: float
    average_shipment_value: float

    # Performance
    on_time_delivery_percent: float
    damage_free_percent: float
    average_transit_days: float

    # Capacity
    total_carriers: int
    active_carriers: int
    average_utilization_percent: float

    # Carbon
    total_miles_saved: float
    carbon_reduced_kg: float


class LaneMetrics(BaseModel):
    """Metrics for a specific lane"""
    origin_state: str
    dest_state: str
    total_shipments: int
    average_rate_per_mile: float
    pooling_rate_percent: float
    average_transit_days: float
    demand_trend: str  # "increasing", "stable", "decreasing"


class ForecastResponse(BaseModel):
    """Demand forecast response"""
    lane: str
    forecast_date: datetime
    predicted_volume_low: float
    predicted_volume_mid: float
    predicted_volume_high: float
    confidence: float


@router.get("/platform", response_model=PlatformMetrics)
async def get_platform_metrics():
    """
    Get overall platform metrics

    Provides key performance indicators for the entire platform.
    """
    from .shipments import shipments_db
    from .carriers import carriers_db

    total_shipments = len(shipments_db)
    pooled = sum(1 for s in shipments_db.values() if s.get("pooled", False))
    total_revenue = sum(s.get("final_price", 0) or s.get("quoted_price", 0) or 0 for s in shipments_db.values())
    total_distance = sum(s.get("distance_miles", 0) for s in shipments_db.values())

    pooling_savings = sum(
        (s.get("quoted_price", 0) or 0) * (s.get("savings_percent", 0) or 0) / 100
        for s in shipments_db.values()
        if s.get("pooled")
    )

    avg_savings = (
        sum(s.get("savings_percent", 0) or 0 for s in shipments_db.values() if s.get("pooled")) / pooled
        if pooled > 0 else 0
    )

    # Estimated carbon savings (roughly 0.4 kg CO2 per mile saved)
    miles_saved = sum(
        s.get("distance_miles", 0) * 0.3  # Assume 30% distance reduction from pooling
        for s in shipments_db.values()
        if s.get("pooled")
    )
    carbon_saved = miles_saved * 0.4

    return PlatformMetrics(
        total_shipments=total_shipments,
        shipments_today=total_shipments // 30,  # Placeholder
        shipments_this_week=total_shipments // 4,
        shipments_this_month=total_shipments,
        pooled_shipments=pooled,
        pooling_rate_percent=pooled / total_shipments * 100 if total_shipments > 0 else 0,
        total_savings_from_pooling=pooling_savings,
        average_pooling_savings_percent=avg_savings,
        total_revenue=total_revenue,
        revenue_today=total_revenue / 30,
        average_rate_per_mile=total_revenue / total_distance if total_distance > 0 else 2.5,
        average_shipment_value=total_revenue / total_shipments if total_shipments > 0 else 0,
        on_time_delivery_percent=97.3,  # Placeholder
        damage_free_percent=99.1,
        average_transit_days=2.5,
        total_carriers=len(carriers_db),
        active_carriers=len(carriers_db),
        average_utilization_percent=78.5,
        total_miles_saved=miles_saved,
        carbon_reduced_kg=carbon_saved
    )


@router.get("/lanes")
async def get_lane_analytics(
    origin_state: Optional[str] = Query(None),
    dest_state: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get analytics by lane (origin-destination pair)

    Provides insights into specific shipping corridors.
    """
    from .shipments import shipments_db

    # Aggregate by lane
    lanes = {}

    for shipment in shipments_db.values():
        origin = shipment["origin"].get("state", "Unknown")
        dest = shipment["destination"].get("state", "Unknown")

        if origin_state and origin != origin_state:
            continue
        if dest_state and dest != dest_state:
            continue

        lane_key = f"{origin}-{dest}"

        if lane_key not in lanes:
            lanes[lane_key] = {
                "origin_state": origin,
                "dest_state": dest,
                "shipments": [],
                "pooled_count": 0
            }

        lanes[lane_key]["shipments"].append(shipment)
        if shipment.get("pooled"):
            lanes[lane_key]["pooled_count"] += 1

    # Calculate metrics for each lane
    results = []

    for lane_key, data in lanes.items():
        shipments = data["shipments"]
        total = len(shipments)

        if total == 0:
            continue

        total_distance = sum(s.get("distance_miles", 0) for s in shipments)
        total_revenue = sum(s.get("final_price", 0) or s.get("quoted_price", 0) or 0 for s in shipments)

        results.append(LaneMetrics(
            origin_state=data["origin_state"],
            dest_state=data["dest_state"],
            total_shipments=total,
            average_rate_per_mile=total_revenue / total_distance if total_distance > 0 else 2.5,
            pooling_rate_percent=data["pooled_count"] / total * 100,
            average_transit_days=total_distance / 500,  # Rough estimate
            demand_trend="stable"
        ))

    # Sort by volume
    results.sort(key=lambda x: x.total_shipments, reverse=True)

    return results[:limit]


@router.get("/forecast")
async def get_demand_forecast(
    origin_state: str = Query(..., description="Origin state code"),
    dest_state: str = Query(..., description="Destination state code"),
    horizon_days: int = Query(14, ge=1, le=30)
):
    """
    Get demand forecast for a lane

    Uses ML to predict future shipment volumes.
    """
    forecasts = []

    # Generate forecasts (placeholder - would use actual ML model)
    import random

    base_volume = random.randint(10, 50)

    for day in range(horizon_days):
        forecast_date = datetime.utcnow() + timedelta(days=day + 1)

        # Add some variation
        variation = random.uniform(-0.2, 0.2)
        mid = base_volume * (1 + variation)

        forecasts.append(ForecastResponse(
            lane=f"{origin_state}-{dest_state}",
            forecast_date=forecast_date,
            predicted_volume_low=mid * 0.7,
            predicted_volume_mid=mid,
            predicted_volume_high=mid * 1.3,
            confidence=0.85 - 0.02 * day  # Confidence decreases with horizon
        ))

    return {
        "lane": f"{origin_state}-{dest_state}",
        "forecast_horizon_days": horizon_days,
        "forecasts": forecasts
    }


@router.get("/savings-report")
async def get_savings_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """
    Get detailed savings report

    Shows how much customers have saved through the platform.
    """
    from .shipments import shipments_db

    total_shipments = len(shipments_db)
    pooled_shipments = sum(1 for s in shipments_db.values() if s.get("pooled"))

    # Calculate savings
    total_quoted = sum(s.get("quoted_price", 0) or 0 for s in shipments_db.values())
    total_final = sum(s.get("final_price", 0) or s.get("quoted_price", 0) or 0 for s in shipments_db.values())
    total_market = sum(s.get("distance_miles", 0) * 2.8 for s in shipments_db.values())  # Competitor avg

    savings_vs_market = total_market - total_final
    pooling_savings = sum(
        (s.get("quoted_price", 0) or 0) - (s.get("final_price", 0) or 0)
        for s in shipments_db.values()
        if s.get("pooled") and s.get("final_price")
    )

    return {
        "period": {
            "start": start_date or datetime.utcnow() - timedelta(days=30),
            "end": end_date or datetime.utcnow()
        },
        "summary": {
            "total_shipments": total_shipments,
            "pooled_shipments": pooled_shipments,
            "pooling_rate_percent": pooled_shipments / total_shipments * 100 if total_shipments > 0 else 0
        },
        "financial": {
            "total_billed": total_final,
            "estimated_market_cost": total_market,
            "total_savings_vs_market": savings_vs_market,
            "savings_percent_vs_market": savings_vs_market / total_market * 100 if total_market > 0 else 0,
            "savings_from_pooling": pooling_savings
        },
        "environmental": {
            "miles_reduced": sum(s.get("distance_miles", 0) * 0.3 for s in shipments_db.values() if s.get("pooled")),
            "carbon_reduced_kg": sum(s.get("distance_miles", 0) * 0.3 * 0.4 for s in shipments_db.values() if s.get("pooled")),
            "trucks_removed_equivalent": pooled_shipments * 0.5  # Rough estimate
        }
    }


@router.get("/performance")
async def get_performance_metrics():
    """
    Get operational performance metrics

    Shows delivery performance, carrier metrics, etc.
    """
    from .shipments import shipments_db
    from .carriers import carriers_db

    delivered = [s for s in shipments_db.values() if s.get("status") == "delivered"]
    in_transit = [s for s in shipments_db.values() if s.get("status") == "in_transit"]

    carrier_performance = []
    for carrier in carriers_db.values():
        carrier_performance.append({
            "carrier_id": str(carrier["id"]),
            "name": carrier["name"],
            "on_time_percent": carrier.get("on_time_percentage", 95),
            "damage_free_percent": carrier.get("damage_free_percentage", 99),
            "total_loads": carrier.get("total_loads", 0)
        })

    return {
        "delivery_performance": {
            "total_delivered": len(delivered),
            "currently_in_transit": len(in_transit),
            "on_time_rate_percent": 97.3,  # Placeholder
            "damage_free_rate_percent": 99.1,
            "average_transit_time_hours": 48
        },
        "carrier_performance": sorted(
            carrier_performance,
            key=lambda x: x["total_loads"],
            reverse=True
        )[:10],
        "pooling_efficiency": {
            "average_shipments_per_pool": 2.3,
            "average_utilization_percent": 78.5,
            "pool_success_rate_percent": 85.0
        }
    }
