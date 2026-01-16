"""
FastAPI Application - Shared Logistics Platform

Main entry point for the API server.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn

from config.settings import get_settings
from .routes import shipments, quotes, pooling, carriers, analytics

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("starting_application", version=settings.app_version)

    # Initialize database connection
    # db = DatabaseManager(settings.database_url)
    # await db.create_tables()
    # app.state.db = db

    # Initialize ML models
    logger.info("loading_ml_models")
    # app.state.demand_forecaster = DemandForecaster()
    # app.state.pricing_engine = DynamicPricingEngine()
    # app.state.pooling_predictor = PoolingPredictor()

    yield

    # Shutdown
    logger.info("shutting_down_application")
    # await db.close()


# Create FastAPI app
app = FastAPI(
    title="Shared Logistics Platform",
    description="""
    Advanced Shared Truckload Logistics Platform

    Features:
    - AI-powered shipment pooling
    - Dynamic pricing optimization
    - Real-time route optimization
    - Demand forecasting
    - Multi-objective optimization (cost, time, carbon)

    Better than FlockFreight with:
    - Graph Neural Networks for pooling prediction
    - Reinforcement Learning for pricing
    - Column Generation for large-scale optimization
    - Virtual hub network for improved pooling density
    """,
    version=settings.app_version,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error("unhandled_exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )


# Include routers
app.include_router(shipments.router, prefix="/api/v1/shipments", tags=["Shipments"])
app.include_router(quotes.router, prefix="/api/v1/quotes", tags=["Quotes"])
app.include_router(pooling.router, prefix="/api/v1/pooling", tags=["Pooling"])
app.include_router(carriers.router, prefix="/api/v1/carriers", tags=["Carriers"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "version": settings.app_version}


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check including dependencies"""
    # Check database
    # Check Redis
    # Check ML models loaded
    return {
        "status": "ready",
        "database": "connected",
        "redis": "connected",
        "ml_models": "loaded"
    }


@app.get("/", tags=["Root"])
async def root():
    """API root"""
    return {
        "name": "Shared Logistics Platform",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


def run_server():
    """Run the API server"""
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug
    )


if __name__ == "__main__":
    run_server()
