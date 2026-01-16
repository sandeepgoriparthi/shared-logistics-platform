"""
Configuration settings for the Shared Logistics Platform
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "SharedLogisticsPlatform"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/logistics_db"
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group: str = "logistics-platform"

    # Optimization Parameters
    optimization_time_limit_seconds: int = 30
    optimization_max_iterations: int = 10000
    max_shipments_per_truck: int = 4
    max_route_duration_hours: float = 14.0
    max_route_distance_miles: float = 800.0

    # Pooling Parameters
    pooling_time_window_hours: float = 4.0
    pooling_distance_threshold_miles: float = 50.0
    min_pooling_savings_percent: float = 10.0

    # Pricing
    base_rate_per_mile: float = 2.50
    fuel_surcharge_percent: float = 15.0
    pooling_discount_percent: float = 25.0

    # ML Model Paths
    demand_model_path: str = "models/demand_forecaster.pt"
    pricing_model_path: str = "models/dynamic_pricing.pt"
    pooling_model_path: str = "models/pooling_predictor.pt"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: list[str] = ["*"]

    # External APIs
    google_maps_api_key: Optional[str] = None
    weather_api_key: Optional[str] = None

    # Mapping Services (Free - MapLibre + OSM)
    map_style_url: str = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
    nominatim_url: str = "https://nominatim.openstreetmap.org"
    osrm_url: str = "https://router.project-osrm.org"

    # Additional Settings
    api_debug: bool = False
    max_detour_percent: float = 15.0
    min_margin_percent: float = 10.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
