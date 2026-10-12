from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from backend.app.schemas.common import ProvenanceMetadata

class WeatherObservationItem(BaseModel):
    id: str
    location_id: str
    location_name: str
    district_name: str
    state_id: str
    station_id: Optional[str] = None
    station_name: Optional[str] = None
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    weather_condition: Optional[str] = None
    provenance: ProvenanceMetadata

class WeatherSummary(BaseModel):
    station_count: int
    avg_temperature_c: Optional[float] = None
    max_temperature_c: Optional[float] = None
    min_temperature_c: Optional[float] = None
    avg_humidity_pct: Optional[float] = None
    dominant_condition: str
    observations: List[WeatherObservationItem]

class RainfallObservationItem(BaseModel):
    id: str
    location_id: str
    location_name: str
    district_name: str
    state_id: str
    rainfall_1h_mm: Optional[float] = None
    rainfall_3h_mm: Optional[float] = None
    rainfall_6h_mm: Optional[float] = None
    rainfall_24h_mm: Optional[float] = None
    rainfall_72h_mm: Optional[float] = None
    cumulative_event_mm: Optional[float] = None
    status: str
    provenance: ProvenanceMetadata

class RainfallTimeseriesPoint(BaseModel):
    timestamp_ist: str
    rainfall_mm: float
    location_name: str

class RainfallAnalytics(BaseModel):
    highest_24h_station: Optional[str] = None
    highest_24h_mm: Optional[float] = None
    districts_under_heavy_rain: List[str] = []
    average_ne_rainfall_24h: Optional[float] = None
    latest_observations: List[RainfallObservationItem]
    trend_history: List[RainfallTimeseriesPoint]
