from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

# Citizen & Field Reporting Schemas
class CitizenReportCreate(BaseModel):
    reporter_name: str
    reporter_phone: str
    report_type: str # Landslide, Road Blockage, Crack, Rockfall, Flooding, Infrastructure Damage, Other
    description: str
    latitude: float
    longitude: float
    landmark: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    media_urls: Optional[List[str]] = []

class CitizenReportItem(BaseModel):
    id: str
    report_number: str
    reporter_name: str
    reporter_phone: str
    report_type: str
    description: str
    latitude: float
    longitude: float
    landmark: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    media_urls: List[str]
    status: str # SUBMITTED, UNDER_REVIEW, VERIFIED, REJECTED, RESOLVED
    verification_notes: Optional[str] = None
    submitted_at_ist: str
    updated_at_ist: str

class FieldReportCreate(BaseModel):
    citizen_report_id: Optional[str] = None
    location_id: Optional[str] = None
    latitude: float
    longitude: float
    incident_type: str
    landslide_dimensions: Optional[str] = None
    movement_active: bool = False
    estimated_volume_m3: Optional[float] = None
    road_blocked: bool = False
    immediate_danger: str = "LOW" # LOW, MEDIUM, HIGH, CRITICAL_EVACUATE
    actions_taken: Optional[str] = None
    media_urls: Optional[List[str]] = []
    offline_client_id: Optional[str] = None

class FieldReportItem(BaseModel):
    id: str
    report_number: str
    officer_name: str
    incident_type: str
    latitude: float
    longitude: float
    landslide_dimensions: Optional[str] = None
    movement_active: bool
    estimated_volume_m3: Optional[float] = None
    road_blocked: bool
    immediate_danger: str
    actions_taken: Optional[str] = None
    media_urls: List[str]
    sync_status: str
    created_at_ist: str

# Road Connectivity Schemas
class RoadSegmentItem(BaseModel):
    id: str
    name: str
    highway_number: Optional[str] = None
    state_id: str
    district_id: str
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    current_status: str # OPEN, PARTIALLY_BLOCKED, BLOCKED, UNKNOWN
    cause: Optional[str] = None
    detour_advice: Optional[str] = None
    estimated_cleared_at_ist: Optional[str] = None
    source_attribution: str # FIELD_VERIFIED or GOVERNMENT_SOURCE
    last_updated_ist: str

class RoadStatusUpdate(BaseModel):
    status: str # OPEN, PARTIALLY_BLOCKED, BLOCKED, UNKNOWN
    cause: Optional[str] = None
    detour_advice: Optional[str] = None
    estimated_cleared_at: Optional[datetime] = None
    source_attribution: str = "FIELD_VERIFIED"

# ML Training & Monitoring Schemas
class ModelMetricDetails(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    confusion_matrix: List[List[int]]
    feature_importances: Dict[str, float]

class ModelStatusResponse(BaseModel):
    active_version: str
    model_name: str
    algorithm: str
    dataset_size: int
    training_status: str # PRODUCTION_ACTIVE, DEVELOPMENT_MODE, TRAINING
    metrics: ModelMetricDetails
    features: List[str]
    trained_at_ist: str
    last_inference_time_ist: Optional[str] = None
    total_inferences_today: int

class ModelTrainRequest(BaseModel):
    algorithm: Optional[str] = "GradientBoostingClassifier"
    n_estimators: Optional[int] = 100
    learning_rate: Optional[float] = 0.1
    max_depth: Optional[int] = 5
    notes: Optional[str] = None
