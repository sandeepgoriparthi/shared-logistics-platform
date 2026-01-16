"""
MapLibre Mapping Service

Provides mapping, geocoding, and routing functionality using open-source tools:
- MapLibre GL JS for map rendering
- Nominatim (OpenStreetMap) for geocoding
- OSRM (Open Source Routing Machine) for routing
- Valhalla for advanced routing (optional)

No Google Maps API required - completely free and open source!
"""
import httpx
import asyncio
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from functools import lru_cache
import structlog
import json
from math import radians, cos, sin, asin, sqrt

logger = structlog.get_logger()


@dataclass
class GeocodingResult:
    """Result from geocoding operation"""
    address: str
    city: str
    state: str
    country: str
    zip_code: str
    latitude: float
    longitude: float
    confidence: float
    place_id: str
    raw_response: Dict[str, Any]


@dataclass
class RouteResult:
    """Result from routing operation"""
    distance_meters: float
    distance_miles: float
    duration_seconds: float
    duration_hours: float
    geometry: List[Tuple[float, float]]  # List of (lat, lon) points
    instructions: List[Dict[str, Any]]
    toll_cost_estimate: float
    fuel_cost_estimate: float


@dataclass
class DistanceMatrixResult:
    """Result from distance matrix calculation"""
    origins: List[Tuple[float, float]]
    destinations: List[Tuple[float, float]]
    distances: List[List[float]]  # meters
    durations: List[List[float]]  # seconds


class NominatimGeocoder:
    """
    OpenStreetMap Nominatim Geocoder

    Free geocoding service with no API key required.
    Rate limit: 1 request/second for public API
    For production: Self-host Nominatim for unlimited requests
    """

    def __init__(
        self,
        base_url: str = "https://nominatim.openstreetmap.org",
        user_agent: str = "SharedLogisticsPlatform/1.0"
    ):
        self.base_url = base_url
        self.user_agent = user_agent
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": user_agent}
        )

    async def geocode(
        self,
        address: str,
        country_codes: List[str] = None
    ) -> Optional[GeocodingResult]:
        """
        Convert address to coordinates

        Args:
            address: Full or partial address string
            country_codes: List of ISO 3166-1 alpha-2 codes to restrict search

        Returns:
            GeocodingResult or None if not found
        """
        params = {
            "q": address,
            "format": "json",
            "addressdetails": 1,
            "limit": 1
        }

        if country_codes:
            params["countrycodes"] = ",".join(country_codes)

        try:
            response = await self.client.get(
                f"{self.base_url}/search",
                params=params
            )
            response.raise_for_status()
            results = response.json()

            if not results:
                logger.warning("geocoding_no_results", address=address)
                return None

            result = results[0]
            addr = result.get("address", {})

            return GeocodingResult(
                address=result.get("display_name", ""),
                city=addr.get("city") or addr.get("town") or addr.get("village", ""),
                state=addr.get("state", ""),
                country=addr.get("country", ""),
                zip_code=addr.get("postcode", ""),
                latitude=float(result["lat"]),
                longitude=float(result["lon"]),
                confidence=float(result.get("importance", 0.5)),
                place_id=result.get("place_id", ""),
                raw_response=result
            )

        except httpx.HTTPError as e:
            logger.error("geocoding_error", address=address, error=str(e))
            return None

    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[GeocodingResult]:
        """
        Convert coordinates to address

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            GeocodingResult or None if not found
        """
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json",
            "addressdetails": 1
        }

        try:
            response = await self.client.get(
                f"{self.base_url}/reverse",
                params=params
            )
            response.raise_for_status()
            result = response.json()

            addr = result.get("address", {})

            return GeocodingResult(
                address=result.get("display_name", ""),
                city=addr.get("city") or addr.get("town") or addr.get("village", ""),
                state=addr.get("state", ""),
                country=addr.get("country", ""),
                zip_code=addr.get("postcode", ""),
                latitude=latitude,
                longitude=longitude,
                confidence=1.0,
                place_id=result.get("place_id", ""),
                raw_response=result
            )

        except httpx.HTTPError as e:
            logger.error("reverse_geocoding_error", lat=latitude, lon=longitude, error=str(e))
            return None

    async def batch_geocode(
        self,
        addresses: List[str],
        delay_seconds: float = 1.0
    ) -> List[Optional[GeocodingResult]]:
        """
        Geocode multiple addresses with rate limiting

        Args:
            addresses: List of address strings
            delay_seconds: Delay between requests (for public API rate limiting)

        Returns:
            List of GeocodingResults (None for failed lookups)
        """
        results = []

        for address in addresses:
            result = await self.geocode(address)
            results.append(result)
            await asyncio.sleep(delay_seconds)

        return results

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class OSRMRouter:
    """
    Open Source Routing Machine (OSRM) Router

    Free routing service for vehicle routing.
    Public demo server available, or self-host for production.
    """

    def __init__(
        self,
        base_url: str = "https://router.project-osrm.org",
        profile: str = "driving"  # driving, cycling, walking
    ):
        self.base_url = base_url
        self.profile = profile
        self.client = httpx.AsyncClient(timeout=60.0)

        # Cost estimates
        self.fuel_price_per_gallon = 3.50
        self.mpg = 6.5  # Truck MPG
        self.toll_rate_per_mile = 0.15  # Average estimate

    async def get_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        waypoints: List[Tuple[float, float]] = None
    ) -> Optional[RouteResult]:
        """
        Get route between two points

        Args:
            origin: (latitude, longitude) tuple
            destination: (latitude, longitude) tuple
            waypoints: Optional list of intermediate points

        Returns:
            RouteResult or None if routing fails
        """
        # Build coordinates string (OSRM uses lon,lat format)
        coords = [f"{origin[1]},{origin[0]}"]

        if waypoints:
            for wp in waypoints:
                coords.append(f"{wp[1]},{wp[0]}")

        coords.append(f"{destination[1]},{destination[0]}")
        coords_str = ";".join(coords)

        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
            "annotations": "true"
        }

        try:
            response = await self.client.get(
                f"{self.base_url}/route/v1/{self.profile}/{coords_str}",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "Ok":
                logger.warning("routing_failed", code=data.get("code"))
                return None

            route = data["routes"][0]
            distance_meters = route["distance"]
            duration_seconds = route["duration"]

            # Extract geometry
            geometry = [
                (coord[1], coord[0])  # Convert to (lat, lon)
                for coord in route["geometry"]["coordinates"]
            ]

            # Extract turn-by-turn instructions
            instructions = []
            for leg in route["legs"]:
                for step in leg["steps"]:
                    instructions.append({
                        "instruction": step["maneuver"].get("instruction", ""),
                        "type": step["maneuver"]["type"],
                        "distance": step["distance"],
                        "duration": step["duration"],
                        "name": step.get("name", "")
                    })

            # Calculate costs
            distance_miles = distance_meters / 1609.34
            fuel_gallons = distance_miles / self.mpg
            fuel_cost = fuel_gallons * self.fuel_price_per_gallon
            toll_cost = distance_miles * self.toll_rate_per_mile

            return RouteResult(
                distance_meters=distance_meters,
                distance_miles=distance_miles,
                duration_seconds=duration_seconds,
                duration_hours=duration_seconds / 3600,
                geometry=geometry,
                instructions=instructions,
                toll_cost_estimate=toll_cost,
                fuel_cost_estimate=fuel_cost
            )

        except httpx.HTTPError as e:
            logger.error("routing_error", error=str(e))
            return None

    async def get_distance_matrix(
        self,
        origins: List[Tuple[float, float]],
        destinations: List[Tuple[float, float]]
    ) -> Optional[DistanceMatrixResult]:
        """
        Calculate distance matrix between multiple origins and destinations

        Args:
            origins: List of (latitude, longitude) tuples
            destinations: List of (latitude, longitude) tuples

        Returns:
            DistanceMatrixResult or None if calculation fails
        """
        # Combine all points
        all_points = origins + destinations
        coords_str = ";".join(f"{p[1]},{p[0]}" for p in all_points)

        # Source indices (origins)
        sources = ";".join(str(i) for i in range(len(origins)))

        # Destination indices
        dest_start = len(origins)
        destinations_param = ";".join(str(i) for i in range(dest_start, len(all_points)))

        params = {
            "sources": sources,
            "destinations": destinations_param,
            "annotations": "distance,duration"
        }

        try:
            response = await self.client.get(
                f"{self.base_url}/table/v1/{self.profile}/{coords_str}",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "Ok":
                logger.warning("distance_matrix_failed", code=data.get("code"))
                return None

            return DistanceMatrixResult(
                origins=origins,
                destinations=destinations,
                distances=data["distances"],
                durations=data["durations"]
            )

        except httpx.HTTPError as e:
            logger.error("distance_matrix_error", error=str(e))
            return None

    async def optimize_route(
        self,
        locations: List[Tuple[float, float]],
        start_index: int = 0,
        end_index: int = None,
        roundtrip: bool = True
    ) -> Optional[List[int]]:
        """
        Optimize visit order for multiple locations (TSP)

        Args:
            locations: List of (latitude, longitude) tuples
            start_index: Index of starting location
            end_index: Index of ending location (None = same as start)
            roundtrip: Whether to return to start

        Returns:
            Optimized order of location indices
        """
        coords_str = ";".join(f"{p[1]},{p[0]}" for p in locations)

        params = {
            "source": "first" if start_index == 0 else str(start_index),
            "roundtrip": str(roundtrip).lower()
        }

        if end_index is not None:
            params["destination"] = "last" if end_index == len(locations) - 1 else str(end_index)

        try:
            response = await self.client.get(
                f"{self.base_url}/trip/v1/{self.profile}/{coords_str}",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "Ok":
                return None

            # Extract waypoint order
            waypoints = data.get("waypoints", [])
            order = [wp["waypoint_index"] for wp in waypoints]

            return order

        except httpx.HTTPError as e:
            logger.error("route_optimization_error", error=str(e))
            return None

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class MapLibreService:
    """
    Main MapLibre service combining geocoding and routing

    Provides a unified interface for all mapping operations.
    """

    def __init__(
        self,
        nominatim_url: str = "https://nominatim.openstreetmap.org",
        osrm_url: str = "https://router.project-osrm.org",
        cache_enabled: bool = True
    ):
        self.geocoder = NominatimGeocoder(base_url=nominatim_url)
        self.router = OSRMRouter(base_url=osrm_url)
        self.cache_enabled = cache_enabled
        self._geocode_cache: Dict[str, GeocodingResult] = {}
        self._distance_cache: Dict[str, float] = {}

    async def geocode_address(
        self,
        address: str,
        use_cache: bool = True
    ) -> Optional[GeocodingResult]:
        """Geocode an address with optional caching"""
        if use_cache and self.cache_enabled and address in self._geocode_cache:
            return self._geocode_cache[address]

        result = await self.geocoder.geocode(address, country_codes=["us"])

        if result and self.cache_enabled:
            self._geocode_cache[address] = result

        return result

    async def get_driving_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        waypoints: List[Tuple[float, float]] = None
    ) -> Optional[RouteResult]:
        """Get driving route between points"""
        return await self.router.get_route(origin, destination, waypoints)

    async def calculate_distance(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        use_routing: bool = True
    ) -> float:
        """
        Calculate distance between two points

        Args:
            origin: (lat, lon) tuple
            destination: (lat, lon) tuple
            use_routing: Use actual road routing (slower) vs haversine (faster)

        Returns:
            Distance in miles
        """
        cache_key = f"{origin[0]:.4f},{origin[1]:.4f}-{destination[0]:.4f},{destination[1]:.4f}"

        if self.cache_enabled and cache_key in self._distance_cache:
            return self._distance_cache[cache_key]

        if use_routing:
            route = await self.router.get_route(origin, destination)
            if route:
                distance = route.distance_miles
            else:
                distance = self._haversine_distance(origin, destination)
        else:
            distance = self._haversine_distance(origin, destination)

        if self.cache_enabled:
            self._distance_cache[cache_key] = distance

        return distance

    def _haversine_distance(
        self,
        point1: Tuple[float, float],
        point2: Tuple[float, float]
    ) -> float:
        """Calculate haversine distance in miles"""
        lat1, lon1 = radians(point1[0]), radians(point1[1])
        lat2, lon2 = radians(point2[0]), radians(point2[1])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        return c * 3956  # Earth radius in miles

    async def build_distance_matrix(
        self,
        locations: List[Tuple[float, float]]
    ) -> Optional[DistanceMatrixResult]:
        """Build distance matrix for multiple locations"""
        return await self.router.get_distance_matrix(locations, locations)

    async def optimize_multi_stop_route(
        self,
        stops: List[Tuple[float, float]],
        start_at_first: bool = True,
        return_to_start: bool = False
    ) -> Optional[List[int]]:
        """
        Optimize the order of multiple stops

        Returns list of indices in optimized order
        """
        start_index = 0 if start_at_first else None
        end_index = 0 if return_to_start else None

        return await self.router.optimize_route(
            stops,
            start_index=start_index,
            end_index=end_index,
            roundtrip=return_to_start
        )

    def get_map_config(self) -> Dict[str, Any]:
        """
        Get MapLibre GL JS configuration for frontend

        Returns configuration object for initializing MapLibre in the browser
        """
        return {
            "style": {
                # Free OpenStreetMap-based style
                "version": 8,
                "sources": {
                    "osm": {
                        "type": "raster",
                        "tiles": [
                            "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                        ],
                        "tileSize": 256,
                        "attribution": "&copy; OpenStreetMap contributors"
                    },
                    # Alternative: Use free vector tiles from MapTiler
                    "openmaptiles": {
                        "type": "vector",
                        "url": "https://api.maptiler.com/tiles/v3/tiles.json?key=YOUR_FREE_KEY"
                    }
                },
                "layers": [
                    {
                        "id": "osm-tiles",
                        "type": "raster",
                        "source": "osm",
                        "minzoom": 0,
                        "maxzoom": 19
                    }
                ]
            },
            "center": [-98.5795, 39.8283],  # US center
            "zoom": 4,
            "freeTileProviders": [
                {
                    "name": "OpenStreetMap",
                    "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                    "attribution": "&copy; OpenStreetMap contributors"
                },
                {
                    "name": "CartoDB Positron",
                    "url": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
                    "attribution": "&copy; CartoDB"
                },
                {
                    "name": "CartoDB Dark Matter",
                    "url": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
                    "attribution": "&copy; CartoDB"
                },
                {
                    "name": "Stamen Terrain",
                    "url": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
                    "attribution": "&copy; Stamen Design"
                }
            ]
        }

    async def close(self):
        """Close all HTTP clients"""
        await self.geocoder.close()
        await self.router.close()


# Singleton instance
_map_service: Optional[MapLibreService] = None


def get_map_service() -> MapLibreService:
    """Get singleton MapLibre service instance"""
    global _map_service
    if _map_service is None:
        _map_service = MapLibreService()
    return _map_service
