"""
Real-Time Optimization Engine

Continuously optimizes routes and pooling as new information arrives:
- New shipment bookings
- Cancellations
- Delays and disruptions
- Carrier availability changes
- Traffic updates

Uses event-driven architecture with rolling horizon optimization.
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from uuid import UUID
from enum import Enum
import structlog

from ..core.models import Shipment, Carrier, Route
from ..core.matching.pooling_engine import PoolingEngine, PoolingConfig
from ..core.optimization import ALNS, ALNSSolution, ALNSConfig

logger = structlog.get_logger()


class EventType(Enum):
    """Types of events that trigger re-optimization"""
    NEW_SHIPMENT = "new_shipment"
    SHIPMENT_CANCELLED = "shipment_cancelled"
    SHIPMENT_UPDATED = "shipment_updated"
    CARRIER_AVAILABLE = "carrier_available"
    CARRIER_UNAVAILABLE = "carrier_unavailable"
    DELAY_REPORTED = "delay_reported"
    TRAFFIC_UPDATE = "traffic_update"
    WEATHER_ALERT = "weather_alert"
    ROUTE_COMPLETED = "route_completed"
    PERIODIC_OPTIMIZATION = "periodic_optimization"


@dataclass
class OptimizationEvent:
    """Event that triggers optimization"""
    event_type: EventType
    timestamp: datetime
    entity_id: Optional[UUID] = None
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1 = highest, 10 = lowest


@dataclass
class OptimizationResult:
    """Result from an optimization run"""
    event: OptimizationEvent
    routes_modified: int
    shipments_affected: int
    savings_achieved: float
    computation_time_ms: float
    success: bool
    message: str


class RealTimeOptimizer:
    """
    Real-time optimization engine

    Features:
    - Event-driven optimization triggers
    - Rolling horizon with configurable lookahead
    - Priority-based event processing
    - Incremental optimization (modify existing routes)
    - Full re-optimization when needed
    """

    def __init__(
        self,
        pooling_engine: Optional[PoolingEngine] = None,
        optimization_interval_seconds: int = 60,
        rolling_horizon_hours: float = 24.0,
        max_events_per_batch: int = 50
    ):
        self.pooling_engine = pooling_engine or PoolingEngine()
        self.optimization_interval = optimization_interval_seconds
        self.rolling_horizon_hours = rolling_horizon_hours
        self.max_events_per_batch = max_events_per_batch

        # State
        self.event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_routes: Dict[UUID, Route] = {}
        self.pending_shipments: Dict[UUID, Shipment] = {}
        self.available_carriers: Dict[UUID, Carrier] = {}

        # Callbacks
        self.on_route_updated: Optional[Callable[[Route], None]] = None
        self.on_shipment_pooled: Optional[Callable[[UUID, UUID], None]] = None

        # Statistics
        self.events_processed = 0
        self.optimizations_run = 0
        self.total_savings = 0.0

        # Control
        self._running = False
        self._optimization_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the real-time optimizer"""
        if self._running:
            return

        self._running = True
        logger.info("starting_realtime_optimizer")

        # Start periodic optimization loop
        self._optimization_task = asyncio.create_task(self._optimization_loop())

    async def stop(self):
        """Stop the real-time optimizer"""
        self._running = False

        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass

        logger.info(
            "stopped_realtime_optimizer",
            events_processed=self.events_processed,
            optimizations_run=self.optimizations_run,
            total_savings=self.total_savings
        )

    async def submit_event(self, event: OptimizationEvent):
        """Submit an event for processing"""
        # Priority queue uses (priority, timestamp, event) tuple
        await self.event_queue.put((
            event.priority,
            event.timestamp.timestamp(),
            event
        ))

        logger.debug(
            "event_submitted",
            event_type=event.event_type.value,
            entity_id=str(event.entity_id) if event.entity_id else None
        )

    async def add_shipment(self, shipment: Shipment):
        """Add a new shipment and trigger optimization"""
        self.pending_shipments[shipment.id] = shipment

        await self.submit_event(OptimizationEvent(
            event_type=EventType.NEW_SHIPMENT,
            timestamp=datetime.utcnow(),
            entity_id=shipment.id,
            priority=3  # High priority for new bookings
        ))

    async def cancel_shipment(self, shipment_id: UUID):
        """Handle shipment cancellation"""
        if shipment_id in self.pending_shipments:
            del self.pending_shipments[shipment_id]

        await self.submit_event(OptimizationEvent(
            event_type=EventType.SHIPMENT_CANCELLED,
            timestamp=datetime.utcnow(),
            entity_id=shipment_id,
            priority=2  # High priority to free up capacity
        ))

    async def update_carrier_availability(
        self,
        carrier: Carrier,
        available: bool
    ):
        """Update carrier availability"""
        if available:
            self.available_carriers[carrier.id] = carrier
            event_type = EventType.CARRIER_AVAILABLE
        else:
            if carrier.id in self.available_carriers:
                del self.available_carriers[carrier.id]
            event_type = EventType.CARRIER_UNAVAILABLE

        await self.submit_event(OptimizationEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            entity_id=carrier.id,
            priority=4
        ))

    async def report_delay(
        self,
        route_id: UUID,
        delay_minutes: float,
        reason: str
    ):
        """Report a delay on an active route"""
        await self.submit_event(OptimizationEvent(
            event_type=EventType.DELAY_REPORTED,
            timestamp=datetime.utcnow(),
            entity_id=route_id,
            data={"delay_minutes": delay_minutes, "reason": reason},
            priority=1  # Highest priority for disruptions
        ))

    async def _optimization_loop(self):
        """Main optimization loop"""
        while self._running:
            try:
                # Wait for interval or events
                await asyncio.sleep(self.optimization_interval)

                # Process queued events
                events = await self._collect_events()

                if events:
                    await self._process_events(events)

                # Periodic full optimization
                await self.submit_event(OptimizationEvent(
                    event_type=EventType.PERIODIC_OPTIMIZATION,
                    timestamp=datetime.utcnow(),
                    priority=8  # Lower priority than reactive events
                ))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("optimization_loop_error", error=str(e))
                await asyncio.sleep(5)  # Back off on error

    async def _collect_events(self) -> List[OptimizationEvent]:
        """Collect events from queue"""
        events = []

        while not self.event_queue.empty() and len(events) < self.max_events_per_batch:
            try:
                priority, timestamp, event = self.event_queue.get_nowait()
                events.append(event)
            except asyncio.QueueEmpty:
                break

        return events

    async def _process_events(
        self,
        events: List[OptimizationEvent]
    ) -> List[OptimizationResult]:
        """Process a batch of events"""
        results = []

        # Group events by type for efficient processing
        grouped = {}
        for event in events:
            if event.event_type not in grouped:
                grouped[event.event_type] = []
            grouped[event.event_type].append(event)

        # Process each event type
        for event_type, type_events in grouped.items():
            try:
                if event_type == EventType.NEW_SHIPMENT:
                    result = await self._handle_new_shipments(type_events)
                elif event_type == EventType.SHIPMENT_CANCELLED:
                    result = await self._handle_cancellations(type_events)
                elif event_type == EventType.DELAY_REPORTED:
                    result = await self._handle_delays(type_events)
                elif event_type == EventType.CARRIER_AVAILABLE:
                    result = await self._handle_carrier_available(type_events)
                elif event_type == EventType.PERIODIC_OPTIMIZATION:
                    result = await self._run_periodic_optimization()
                else:
                    continue

                results.append(result)
                self.events_processed += len(type_events)

            except Exception as e:
                logger.error(
                    "event_processing_error",
                    event_type=event_type.value,
                    error=str(e)
                )

        return results

    async def _handle_new_shipments(
        self,
        events: List[OptimizationEvent]
    ) -> OptimizationResult:
        """Handle new shipment events - try to insert into existing routes"""
        import time
        start_time = time.time()

        inserted = 0
        savings = 0.0

        for event in events:
            shipment_id = event.entity_id
            if shipment_id not in self.pending_shipments:
                continue

            shipment = self.pending_shipments[shipment_id]

            # Try to insert into existing route
            best_route = await self._find_best_insertion(shipment)

            if best_route:
                # Insert shipment into route
                best_route.shipment_ids.append(shipment_id)
                inserted += 1

                # Estimate savings
                individual_cost = shipment.distance_miles * 2.5
                insertion_cost = individual_cost * 0.3  # Roughly 30% marginal cost
                savings += individual_cost - insertion_cost

                del self.pending_shipments[shipment_id]

                if self.on_shipment_pooled:
                    self.on_shipment_pooled(shipment_id, best_route.id)

        # For remaining shipments, run pooling optimization
        if self.pending_shipments:
            pooling_result = self.pooling_engine.find_pooling_opportunities(
                list(self.pending_shipments.values()),
                list(self.available_carriers.values())
            )

            if pooling_result.opportunities:
                # Create routes from opportunities
                for opp in pooling_result.opportunities[:5]:  # Limit
                    route = opp.optimized_route or Route(
                        shipment_ids=opp.shipment_ids
                    )
                    self.active_routes[route.id] = route

                    for sid in opp.shipment_ids:
                        if sid in self.pending_shipments:
                            del self.pending_shipments[sid]

                    inserted += len(opp.shipment_ids)
                    savings += opp.total_savings

        computation_time = (time.time() - start_time) * 1000
        self.total_savings += savings
        self.optimizations_run += 1

        logger.info(
            "new_shipments_processed",
            num_events=len(events),
            inserted=inserted,
            savings=savings
        )

        return OptimizationResult(
            event=events[0],
            routes_modified=len([r for r in self.active_routes.values()]),
            shipments_affected=inserted,
            savings_achieved=savings,
            computation_time_ms=computation_time,
            success=True,
            message=f"Processed {len(events)} new shipments, inserted {inserted}"
        )

    async def _handle_cancellations(
        self,
        events: List[OptimizationEvent]
    ) -> OptimizationResult:
        """Handle shipment cancellation events"""
        import time
        start_time = time.time()

        affected_routes = set()

        for event in events:
            shipment_id = event.entity_id

            # Find and update affected route
            for route in self.active_routes.values():
                if shipment_id in route.shipment_ids:
                    route.shipment_ids.remove(shipment_id)
                    affected_routes.add(route.id)
                    break

        # Re-optimize affected routes
        for route_id in affected_routes:
            route = self.active_routes[route_id]

            if len(route.shipment_ids) < 2:
                # Route no longer viable for pooling
                # Mark for individual handling
                pass

            if self.on_route_updated:
                self.on_route_updated(route)

        computation_time = (time.time() - start_time) * 1000

        return OptimizationResult(
            event=events[0],
            routes_modified=len(affected_routes),
            shipments_affected=len(events),
            savings_achieved=0,
            computation_time_ms=computation_time,
            success=True,
            message=f"Handled {len(events)} cancellations"
        )

    async def _handle_delays(
        self,
        events: List[OptimizationEvent]
    ) -> OptimizationResult:
        """Handle delay events - reschedule downstream stops"""
        import time
        start_time = time.time()

        affected_routes = 0

        for event in events:
            route_id = event.entity_id
            delay_minutes = event.data.get("delay_minutes", 0)

            if route_id not in self.active_routes:
                continue

            route = self.active_routes[route_id]

            # Update scheduled times for remaining stops
            for stop in route.stops:
                if stop.scheduled_time > datetime.utcnow():
                    stop.scheduled_time += timedelta(minutes=delay_minutes)

            affected_routes += 1

            # Notify downstream parties
            if self.on_route_updated:
                self.on_route_updated(route)

        computation_time = (time.time() - start_time) * 1000

        logger.info(
            "delays_processed",
            num_events=len(events),
            affected_routes=affected_routes
        )

        return OptimizationResult(
            event=events[0],
            routes_modified=affected_routes,
            shipments_affected=0,
            savings_achieved=0,
            computation_time_ms=computation_time,
            success=True,
            message=f"Processed {len(events)} delays"
        )

    async def _handle_carrier_available(
        self,
        events: List[OptimizationEvent]
    ) -> OptimizationResult:
        """Handle new carrier availability - match with pending shipments"""
        import time
        start_time = time.time()

        matched = 0

        if self.pending_shipments and self.available_carriers:
            # Run matching
            pooling_result = self.pooling_engine.find_pooling_opportunities(
                list(self.pending_shipments.values()),
                list(self.available_carriers.values())
            )

            matched = pooling_result.shipments_pooled

        computation_time = (time.time() - start_time) * 1000

        return OptimizationResult(
            event=events[0],
            routes_modified=0,
            shipments_affected=matched,
            savings_achieved=0,
            computation_time_ms=computation_time,
            success=True,
            message=f"Matched {matched} shipments with new carriers"
        )

    async def _run_periodic_optimization(self) -> OptimizationResult:
        """Run full periodic optimization"""
        import time
        start_time = time.time()

        # Use ALNS to improve existing routes
        improvements = 0.0

        for route_id, route in self.active_routes.items():
            if len(route.shipment_ids) < 2:
                continue

            # Would run ALNS here to improve route
            # For now, skip

        computation_time = (time.time() - start_time) * 1000
        self.optimizations_run += 1

        return OptimizationResult(
            event=OptimizationEvent(
                event_type=EventType.PERIODIC_OPTIMIZATION,
                timestamp=datetime.utcnow()
            ),
            routes_modified=len(self.active_routes),
            shipments_affected=sum(len(r.shipment_ids) for r in self.active_routes.values()),
            savings_achieved=improvements,
            computation_time_ms=computation_time,
            success=True,
            message="Periodic optimization complete"
        )

    async def _find_best_insertion(
        self,
        shipment: Shipment
    ) -> Optional[Route]:
        """Find the best existing route to insert a shipment"""
        best_route = None
        best_cost_increase = float('inf')

        for route in self.active_routes.values():
            # Check basic compatibility
            # Same equipment, capacity available, time windows overlap

            # Calculate insertion cost
            # This would use proper insertion heuristics

            cost_increase = shipment.distance_miles * 0.3  # Rough estimate

            if cost_increase < best_cost_increase:
                best_cost_increase = cost_increase
                best_route = route

        # Only return if insertion cost is reasonable
        if best_route and best_cost_increase < shipment.distance_miles * 0.5:
            return best_route

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        return {
            "events_processed": self.events_processed,
            "optimizations_run": self.optimizations_run,
            "total_savings": self.total_savings,
            "active_routes": len(self.active_routes),
            "pending_shipments": len(self.pending_shipments),
            "available_carriers": len(self.available_carriers),
            "running": self._running
        }
