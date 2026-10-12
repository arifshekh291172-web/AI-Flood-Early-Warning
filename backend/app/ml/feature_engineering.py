import math
from typing import Dict, Any, List
import numpy as np

# Feature Column Definitions
FEATURE_COLUMNS = [
    "rainfall_1h_mm",
    "rainfall_3h_mm",
    "rainfall_6h_mm",
    "rainfall_24h_mm",
    "rainfall_72h_mm",
    "cumulative_event_mm",
    "antecedent_rainfall_7d_mm",
    "soil_moisture_pct",
    "pore_pressure_kpa",
    "slope_deg",
    "elevation_m",
    "aspect_sin",
    "aspect_cos",
    "curvature",
    "distance_to_fault_m",
    "distance_to_stream_m",
    "drainage_density",
    "historical_landslide_density_5km",
    "weather_warning_severity_code",
    "lithology_code" # 0: Crystalline, 1: Metamorphic, 2: Sandstone/Shale, 3: Unconsolidated Alluvium
]

LITHOLOGY_MAP = {
    "Crystalline": 0,
    "Metamorphic": 1,
    "Sedimentary": 2,
    "Sandstone/Shale": 2,
    "Clayey Loam": 2,
    "Unconsolidated": 3
}

def extract_feature_vector(
    weather_data: Dict[str, Any],
    rainfall_data: Dict[str, Any],
    sensor_data: Dict[str, Any],
    terrain_data: Dict[str, Any],
    warning_data: Dict[str, Any],
    historical_count: int = 0
) -> Dict[str, float]:
    """
    Transforms multi-source environmental, meteorological, and geospatial parameters
    into a standardized feature dictionary.
    """
    # Rainfall features
    r1 = float(rainfall_data.get("rainfall_1h_mm") or 0.0)
    r3 = float(rainfall_data.get("rainfall_3h_mm") or (r1 * 2.5))
    r6 = float(rainfall_data.get("rainfall_6h_mm") or (r3 * 1.8))
    r24 = float(rainfall_data.get("rainfall_24h_mm") or (r6 * 2.2))
    r72 = float(rainfall_data.get("rainfall_72h_mm") or (r24 * 1.6))
    rcum = float(rainfall_data.get("cumulative_event_mm") or (r72 * 1.3))
    ari7 = float(rainfall_data.get("antecedent_rainfall_7d_mm") or (r72 * 1.2))

    # Geotechnical & sensor
    soil_moisture = float(sensor_data.get("soil_moisture_pct") or min(95.0, 35.0 + (r24 * 0.4)))
    pore_kpa = float(sensor_data.get("pore_pressure_kpa") or min(150.0, 15.0 + (r24 * 0.7)))

    # Terrain
    slope = float(terrain_data.get("slope_deg") or 25.0)
    elev = float(terrain_data.get("elevation_m") or 600.0)
    aspect = float(terrain_data.get("aspect_deg") or 180.0)
    rad = math.radians(aspect)
    aspect_sin = round(math.sin(rad), 4)
    aspect_cos = round(math.cos(rad), 4)
    curvature = float(terrain_data.get("curvature") or 0.0)
    dist_fault = float(terrain_data.get("distance_to_fault_m") or 1500.0)
    dist_stream = float(terrain_data.get("distance_to_stream_m") or 300.0)
    drainage = float(terrain_data.get("drainage_density") or 1.8)

    lith_str = str(terrain_data.get("lithology") or "Sedimentary")
    lith_code = float(LITHOLOGY_MAP.get(lith_str, 2))

    # Warning indicator (0: None, 1: Yellow, 2: Orange, 3: Red)
    warn_sev = str(warning_data.get("severity") or "None").lower()
    warn_code = 3.0 if "red" in warn_sev else 2.0 if "orange" in warn_sev else 1.0 if "yellow" in warn_sev else 0.0

    return {
        "rainfall_1h_mm": r1,
        "rainfall_3h_mm": r3,
        "rainfall_6h_mm": r6,
        "rainfall_24h_mm": r24,
        "rainfall_72h_mm": r72,
        "cumulative_event_mm": rcum,
        "antecedent_rainfall_7d_mm": ari7,
        "soil_moisture_pct": soil_moisture,
        "pore_pressure_kpa": pore_kpa,
        "slope_deg": slope,
        "elevation_m": elev,
        "aspect_sin": aspect_sin,
        "aspect_cos": aspect_cos,
        "curvature": curvature,
        "distance_to_fault_m": dist_fault,
        "distance_to_stream_m": dist_stream,
        "drainage_density": drainage,
        "historical_landslide_density_5km": float(historical_count),
        "weather_warning_severity_code": warn_code,
        "lithology_code": lith_code
    }

def feature_dict_to_array(features: Dict[str, float]) -> np.ndarray:
    return np.array([[features[col] for col in FEATURE_COLUMNS]], dtype=np.float32)
