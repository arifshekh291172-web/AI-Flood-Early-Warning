import math
from typing import Dict, Any, List, Tuple

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def create_circular_polygon_geojson(center_lat: float, center_lon: float, radius_km: float = 3.0, points: int = 24) -> Dict[str, Any]:
    """Generates a GeoJSON Polygon approximating a circular risk buffer zone."""
    coords = []
    lat_deg_per_km = 1.0 / 111.0
    lon_deg_per_km = 1.0 / (111.0 * math.cos(math.radians(center_lat)))

    for i in range(points + 1):
        angle = (2.0 * math.pi * i) / points
        dx = radius_km * math.cos(angle)
        dy = radius_km * math.sin(angle)
        pt_lon = center_lon + (dx * lon_deg_per_km)
        pt_lat = center_lat + (dy * lat_deg_per_km)
        coords.append([round(pt_lon, 5), round(pt_lat, 5)])

    return {
        "type": "Polygon",
        "coordinates": [coords]
    }

def locations_to_geojson_feature_collection(locations_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Transforms location risk entries into GeoJSON FeatureCollection."""
    features = []
    for loc in locations_data:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [loc["longitude"], loc["latitude"]]
            },
            "properties": {
                "id": loc.get("location_id") or loc.get("id"),
                "name": loc.get("location_name") or loc.get("name"),
                "district_id": loc.get("district_id"),
                "state_id": loc.get("state_id"),
                "risk_probability": loc.get("risk_probability"),
                "risk_class": loc.get("risk_class", "LOW"),
                "slope_deg": loc.get("slope_deg"),
                "elevation_m": loc.get("elevation_m"),
                "thresholds_exceeded": loc.get("thresholds_exceeded", [])
            }
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features
    }
