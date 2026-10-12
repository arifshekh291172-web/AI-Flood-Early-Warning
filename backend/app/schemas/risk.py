from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from backend.app.schemas.common import ProvenanceMetadata

# Explicit distinction schemas
class OfficialGovernmentWarningItem(BaseModel):
    id: str
    official_alert_id: str
    alert_source: str # IMD or NDMA/SACHET
    alert_type: str # Heavy Rainfall, Landslide Warning, Flash Flood
    severity: str # Red Warning, Orange Alert, Yellow Watch
    headline: str
    description: str
    state_id: str
    district_name: Optional[str] = None
    issued_at_ist: str
    valid_until_ist: str
    official_source_url: Optional[str] = None
    status: str # ACTIVE, EXPIRED

class MLRiskPredictionItem(BaseModel):
    id: str
    location_id: str
    location_name: str
    district_name: str
    state_id: str
    latitude: float
    longitude: float
    slope_deg: float
    elevation_m: float
    risk_probability: float # 0.00 to 1.00
    risk_class: str # LOW, MODERATE, HIGH, CRITICAL
    model_version: str
    feature_snapshot: Dict[str, Any]
    thresholds_exceeded: Optional[List[str]] = None
    prediction_time_ist: str
    provenance: ProvenanceMetadata

class RiskZoneItem(BaseModel):
    id: str
    zone_name: str
    district_name: str
    state_id: str
    risk_level: str
    area_sqkm: float
    valid_until_ist: str
    geometry_geojson: Dict[str, Any]

class RiskSummary(BaseModel):
    total_monitored_locations: int
    critical_locations_count: int
    high_risk_locations_count: int
    moderate_risk_locations_count: int
    low_risk_locations_count: int
    active_risk_zones_count: int
    top_critical_locations: List[MLRiskPredictionItem]
    model_version_active: str
    generated_at_ist: str
