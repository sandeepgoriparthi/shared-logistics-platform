#!/usr/bin/env python3
"""
Shared Logistics Platform - Main Entry Point

A next-generation shared truckload logistics platform that outperforms
FlockFreight through:

1. Advanced Optimization Algorithms
   - Vehicle Routing Problem with Time Windows (VRPTW)
   - Column Generation for large-scale optimization
   - Adaptive Large Neighborhood Search (ALNS)

2. Machine Learning Models
   - Temporal Fusion Transformer for demand forecasting
   - PPO Reinforcement Learning for dynamic pricing
   - Graph Neural Networks for pooling prediction

3. Real-Time Optimization
   - Event-driven re-optimization
   - Rolling horizon planning
   - Continuous route improvement

Usage:
    python main.py api          # Start API server
    python main.py simulate     # Run simulation benchmark
    python main.py optimize     # Run batch optimization
"""
import sys
import argparse
import asyncio


def run_api():
    """Start the FastAPI server"""
    import uvicorn
    from config.settings import get_settings

    settings = get_settings()

    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║         SHARED LOGISTICS PLATFORM - API SERVER                ║
    ║                                                               ║
    ║   Better than FlockFreight with:                             ║
    ║   • AI-Powered Pooling (GNN + ML)                            ║
    ║   • Dynamic Pricing (Reinforcement Learning)                  ║
    ║   • Real-Time Optimization (VRPTW + ALNS)                    ║
    ║   • Demand Forecasting (Temporal Fusion Transformer)          ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )


def run_simulation():
    """Run simulation benchmark"""
    from tests.simulation.simulator import run_benchmark

    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║         SHARED LOGISTICS PLATFORM - SIMULATION                ║
    ║                                                               ║
    ║   Running freight simulation to demonstrate:                  ║
    ║   • Pooling optimization effectiveness                        ║
    ║   • Cost savings vs individual shipments                      ║
    ║   • Truck utilization improvements                            ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    result = run_benchmark()
    return result


def run_optimization_demo():
    """Run optimization demonstration"""
    from src.core.models import Shipment, Carrier, Location, TimeWindow, Dimensions
    from src.core.matching.pooling_engine import PoolingEngine
    from datetime import datetime, timedelta
    import random

    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║         SHARED LOGISTICS PLATFORM - OPTIMIZATION DEMO         ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    # Generate sample shipments
    print("Generating sample shipments...")

    shipments = []
    base_time = datetime.now()

    # LA to Chicago corridor
    for i in range(10):
        shipment = Shipment(
            origin=Location(
                city="Los Angeles",
                state="CA",
                latitude=34.0522 + random.uniform(-0.3, 0.3),
                longitude=-118.2437 + random.uniform(-0.3, 0.3)
            ),
            destination=Location(
                city="Chicago",
                state="IL",
                latitude=41.8781 + random.uniform(-0.3, 0.3),
                longitude=-87.6298 + random.uniform(-0.3, 0.3)
            ),
            pickup_window=TimeWindow(
                earliest=base_time + timedelta(hours=random.randint(0, 24)),
                latest=base_time + timedelta(hours=random.randint(25, 48))
            ),
            delivery_window=TimeWindow(
                earliest=base_time + timedelta(hours=48),
                latest=base_time + timedelta(hours=96)
            ),
            dimensions=Dimensions(
                weight_lbs=random.uniform(5000, 20000),
                linear_feet=random.uniform(8, 24),
                pallet_count=random.randint(2, 12)
            )
        )
        shipments.append(shipment)

    print(f"Generated {len(shipments)} shipments")

    # Generate carriers
    carriers = [
        Carrier(
            name=f"Carrier_{i}",
            mc_number=f"MC{100000+i}",
            dot_number=f"DOT{1000000+i}",
            current_location=Location(
                city="Los Angeles",
                state="CA",
                latitude=34.0522,
                longitude=-118.2437
            )
        )
        for i in range(5)
    ]

    print(f"Generated {len(carriers)} carriers")

    # Run pooling optimization
    print("\nRunning pooling optimization...")

    engine = PoolingEngine()
    result = engine.find_pooling_opportunities(shipments, carriers)

    print(f"""
    ═══════════════════════════════════════════════════════════════
                        OPTIMIZATION RESULTS
    ═══════════════════════════════════════════════════════════════

    Shipments Analyzed:     {len(shipments)}
    Pooling Opportunities:  {len(result.opportunities)}
    Shipments Pooled:       {result.shipments_pooled}
    Pooling Rate:           {result.shipments_pooled / len(shipments) * 100:.1f}%

    Financial Impact:
    ─────────────────
    Total Potential Savings: ${result.total_potential_savings:,.2f}
    Average Savings:         {result.average_savings_percent:.1f}%

    Computation Time:        {result.computation_time_seconds:.3f} seconds

    ═══════════════════════════════════════════════════════════════
    """)

    # Show top opportunities
    if result.opportunities:
        print("Top Pooling Opportunities:")
        print("─" * 60)
        for i, opp in enumerate(result.opportunities[:5], 1):
            print(f"  {i}. {len(opp.shipment_ids)} shipments | "
                  f"Score: {opp.overall_score:.2f} | "
                  f"Savings: {opp.savings_percent:.1f}%")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Shared Logistics Platform - Next-Gen Freight Optimization"
    )
    parser.add_argument(
        "command",
        choices=["api", "simulate", "optimize"],
        help="Command to run"
    )

    args = parser.parse_args()

    if args.command == "api":
        run_api()
    elif args.command == "simulate":
        run_simulation()
    elif args.command == "optimize":
        run_optimization_demo()


if __name__ == "__main__":
    main()
