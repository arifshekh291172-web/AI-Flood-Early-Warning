import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, 
    Text, JSON, Enum, Index
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

# 1. Roles
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True) # ADMIN, DISTRICT_AUTHORITY, FIELD_OFFICER, ANALYST, CITIZEN
    description = Column(String(255), nullable=True)
    permissions = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="role")

# 2. Users
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True) # e.g. ASDMA, GSI, PWD, BRO, Citizen
    state_jurisdiction = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship("Role", back_populates="users")
    citizen_reports = relationship("CitizenReport", back_populates="user")
    field_reports = relationship("FieldReport", back_populates="officer")
    audit_logs = relationship("AuditLog", back_populates="user")

# 3. States
class State(Base):
    __tablename__ = "states"

    id = Column(String(10), primary_key=True) # e.g. "AS", "AR", "MN", "ML", "MZ", "NL", "SK", "TR"
    name = Column(String(100), unique=True, nullable=False)
    capital = Column(String(100), nullable=True)
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    boundary_geojson = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    districts = relationship("District", back_populates="state")
    locations = relationship("Location", back_populates="state")

# 4. Districts
class District(Base):
    __tablename__ = "districts"

    id = Column(String(50), primary_key=True) # e.g. "AS_KAMRUP", "ML_EAST_KHASI"
    state_id = Column(String(10), ForeignKey("states.id"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    area_sqkm = Column(Float, nullable=True)
    boundary_geojson = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    state = relationship("State", back_populates="districts")
    locations = relationship("Location", back_populates="district")
    government_alerts = relationship("GovernmentAlert", back_populates="district")

# 5. Locations (Monitored hazard/station points)
class Location(Base):
    __tablename__ = "locations"

    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False, index=True)
    district_id = Column(String(50), ForeignKey("districts.id"), nullable=False)
    state_id = Column(String(10), ForeignKey("states.id"), nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    elevation_m = Column(Float, nullable=False, default=500.0)
    slope_deg = Column(Float, nullable=False, default=25.0)
    geology_type = Column(String(100), nullable=True)
    hazard_susceptibility = Column(String(50), default="MODERATE") # LOW, MODERATE, HIGH, VERY_HIGH
    is_active_monitoring = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    district = relationship("District", back_populates="locations")
    state = relationship("State", back_populates="locations")
    weather_observations = relationship("WeatherObservation", back_populates="location")
    rainfall_observations = relationship("RainfallObservation", back_populates="location")
    sensor_readings = relationship("SensorReading", back_populates="location")
    terrain_features = relationship("TerrainFeature", back_populates="location", uselist=False)
    risk_predictions = relationship("RiskPrediction", back_populates="location")

# 6. Weather Observations
class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_id = Column(String(50), ForeignKey("locations.id"), nullable=False, index=True)
    station_id = Column(String(50), nullable=True)
    station_name = Column(String(100), nullable=True)
    temperature_c = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)
    pressure_hpa = Column(Float, nullable=True)
    wind_speed_kmh = Column(Float, nullable=True)
    wind_direction_deg = Column(Float, nullable=True)
    weather_condition = Column(String(100), nullable=True) # e.g. Heavy Rain, Thunderstorm, Fog
    source = Column(String(50), nullable=False, default="IMD") # IMD, AWS, SENSOR
    source_url = Column(String(255), nullable=True)
    observed_at = Column(DateTime, nullable=False, index=True)
    received_at = Column(DateTime, default=datetime.utcnow)
    raw_payload_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    location = relationship("Location", back_populates="weather_observations")

# 7. Rainfall Observations
class RainfallObservation(Base):
    __tablename__ = "rainfall_observations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_id = Column(String(50), ForeignKey("locations.id"), nullable=False, index=True)
    district_id = Column(String(50), nullable=True, index=True)
    rainfall_1h_mm = Column(Float, nullable=True)
    rainfall_3h_mm = Column(Float, nullable=True)
    rainfall_6h_mm = Column(Float, nullable=True)
    rainfall_24h_mm = Column(Float, nullable=True)
    rainfall_72h_mm = Column(Float, nullable=True)
    cumulative_event_mm = Column(Float, nullable=True)
    status = Column(String(20), default="NORMAL") # NORMAL, MODERATE, HEAVY, VERY_HEAVY, EXTREME
    source = Column(String(50), nullable=False, default="IMD")
    source_url = Column(String(255), nullable=True)
    observed_at = Column(DateTime, nullable=False, index=True)
    received_at = Column(DateTime, default=datetime.utcnow)
    raw_payload_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    location = relationship("Location", back_populates="rainfall_observations")

# 8. Sensor Readings (Field IoT Telemetry)
class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sensor_id = Column(String(50), nullable=False, index=True)
    location_id = Column(String(50), ForeignKey("locations.id"), nullable=False)
    sensor_type = Column(String(50), nullable=False) # PorePressure, SoilMoisture, Inclinometer, RainGauge, Tilt
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False) # kPa, %, mm, degrees
    battery_level_pct = Column(Float, nullable=True)
    signal_strength_dbm = Column(Float, nullable=True)
    status = Column(String(20), default="HEALTHY")
    recorded_at = Column(DateTime, nullable=False, index=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(50), default="FIELD_IOT_GATEWAY")

    location = relationship("Location", back_populates="sensor_readings")

# 9. Terrain Features (Geotechnical parameters for ML)
class TerrainFeature(Base):
    __tablename__ = "terrain_features"

    id = Column(String(50), primary_key=True) # maps to location_id
    location_id = Column(String(50), ForeignKey("locations.id"), unique=True, nullable=False)
    slope_deg = Column(Float, nullable=False)
    aspect_deg = Column(Float, nullable=False, default=180.0)
    elevation_m = Column(Float, nullable=False)
    curvature = Column(Float, nullable=False, default=0.0)
    lithology = Column(String(100), nullable=False, default="Sedimentary")
    land_use = Column(String(100), nullable=False, default="Forest")
    distance_to_fault_m = Column(Float, nullable=False, default=1500.0)
    distance_to_stream_m = Column(Float, nullable=False, default=300.0)
    drainage_density = Column(Float, nullable=False, default=1.8)
    soil_type = Column(String(100), nullable=False, default="Clayey Loam")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    location = relationship("Location", back_populates="terrain_features")

# 10. Historical Landslides
class HistoricalLandslide(Base):
    __tablename__ = "historical_landslides"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    state_id = Column(String(10), nullable=False)
    district_id = Column(String(50), nullable=False)
    location_name = Column(String(150), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    event_date = Column(DateTime, nullable=False, index=True)
    trigger_cause = Column(String(100), nullable=False) # Continuous Heavy Rainfall, Cloudburst, Road Cutting, Earthquake
    volume_m3 = Column(Float, nullable=True)
    casualties = Column(Integer, default=0)
    road_blocked_hours = Column(Float, default=0.0)
    source = Column(String(100), default="GSI / BHUVAN CATALOG")
    created_at = Column(DateTime, default=datetime.utcnow)

# 11. Risk Predictions (Time-series ML outputs)
class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_id = Column(String(50), ForeignKey("locations.id"), nullable=False, index=True)
    prediction_time = Column(DateTime, nullable=False, index=True)
    risk_probability = Column(Float, nullable=False) # 0.00 to 1.00
    risk_class = Column(String(20), nullable=False, index=True) # LOW, MODERATE, HIGH, CRITICAL
    model_version = Column(String(50), nullable=False)
    feature_snapshot = Column(JSON, nullable=False) # Snapshot of all input features
    thresholds_exceeded = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    location = relationship("Location", back_populates="risk_predictions")

# 12. Risk Zones (Spatial dynamic polygons)
class RiskZone(Base):
    __tablename__ = "risk_zones"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    district_id = Column(String(50), nullable=False, index=True)
    zone_name = Column(String(150), nullable=False)
    risk_level = Column(String(20), nullable=False) # HIGH, CRITICAL
    geometry_geojson = Column(JSON, nullable=False)
    area_sqkm = Column(Float, nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    generated_by_run_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 13. Government Alerts (Official NDMA/IMD machine-readable feeds)
class GovernmentAlert(Base):
    __tablename__ = "government_alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    alert_source = Column(String(50), nullable=False) # IMD, NDMA/SACHET
    official_alert_id = Column(String(100), unique=True, nullable=False)
    alert_type = Column(String(50), nullable=False) # Landslide Warning, Heavy Rainfall, Flash Flood, Cyclone
    severity = Column(String(30), nullable=False) # Red Warning, Orange Alert, Yellow Watch
    headline = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    district_id = Column(String(50), ForeignKey("districts.id"), nullable=True)
    state_id = Column(String(10), nullable=False)
    issued_at = Column(DateTime, nullable=False, index=True)
    valid_until = Column(DateTime, nullable=False)
    official_source_url = Column(String(255), nullable=True)
    raw_payload_json = Column(JSON, nullable=True)
    status = Column(String(20), default="ACTIVE") # ACTIVE, EXPIRED, CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow)

    district = relationship("District", back_populates="government_alerts")

# 14. Citizen Reports
class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_number = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    reporter_name = Column(String(100), nullable=False)
    reporter_phone = Column(String(20), nullable=False)
    report_type = Column(String(50), nullable=False) # Landslide, Road Blockage, Crack, Rockfall, Flooding, Infrastructure Damage, Other
    description = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    landmark = Column(String(200), nullable=True)
    district = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    media_urls = Column(JSON, default=list)
    status = Column(String(30), default="SUBMITTED", index=True) # SUBMITTED, UNDER_REVIEW, VERIFIED, REJECTED, RESOLVED
    verified_by_user_id = Column(String(36), nullable=True)
    verification_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="citizen_reports")
    field_reports = relationship("FieldReport", back_populates="citizen_report")

# 15. Field Reports (Officer Ground Verification)
class FieldReport(Base):
    __tablename__ = "field_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_number = Column(String(20), unique=True, nullable=False)
    officer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    citizen_report_id = Column(String(36), ForeignKey("citizen_reports.id"), nullable=True)
    location_id = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    incident_type = Column(String(50), nullable=False)
    landslide_dimensions = Column(String(100), nullable=True) # e.g. "30m width x 15m depth"
    movement_active = Column(Boolean, default=False)
    estimated_volume_m3 = Column(Float, nullable=True)
    road_blocked = Column(Boolean, default=False)
    immediate_danger = Column(String(50), default="LOW") # LOW, MEDIUM, HIGH, CRITICAL_EVACUATE
    actions_taken = Column(Text, nullable=True)
    media_urls = Column(JSON, default=list)
    sync_status = Column(String(20), default="SYNCED") # PENDING, SYNCED, FAILED
    offline_client_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    synced_at = Column(DateTime, default=datetime.utcnow)

    officer = relationship("User", back_populates="field_reports")
    citizen_report = relationship("CitizenReport", back_populates="field_reports")

# 16. Media Files
class MediaFile(Base):
    __tablename__ = "media_files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False) # image/jpeg, image/png, video/mp4
    file_size_bytes = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    uploaded_by = Column(String(36), nullable=True)
    related_entity_type = Column(String(50), nullable=True) # citizen_report, field_report
    related_entity_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 17. Road Segments
class RoadSegment(Base):
    __tablename__ = "road_segments"

    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    highway_number = Column(String(50), nullable=True) # e.g. NH-27, NH-6, NH-10
    state_id = Column(String(10), nullable=False)
    district_id = Column(String(50), nullable=False)
    start_lat = Column(Float, nullable=False)
    start_lon = Column(Float, nullable=False)
    end_lat = Column(Float, nullable=False)
    end_lon = Column(Float, nullable=False)
    path_geojson = Column(JSON, nullable=True)
    source_type = Column(String(50), default="GOVERNMENT_SOURCE") # FIELD_VERIFIED or GOVERNMENT_SOURCE
    created_at = Column(DateTime, default=datetime.utcnow)

    status_records = relationship("RoadStatus", back_populates="road_segment")

# 18. Road Status
class RoadStatus(Base):
    __tablename__ = "road_status"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    road_segment_id = Column(String(50), ForeignKey("road_segments.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False) # OPEN, PARTIALLY_BLOCKED, BLOCKED, UNKNOWN
    cause = Column(String(150), nullable=True) # e.g. "Debris fall at KM 42", "Waterlogging"
    detour_advice = Column(Text, nullable=True)
    estimated_cleared_at = Column(DateTime, nullable=True)
    updated_by_user_id = Column(String(36), nullable=True)
    source_attribution = Column(String(50), default="FIELD_VERIFIED") # FIELD_VERIFIED or GOVERNMENT_SOURCE
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)

    road_segment = relationship("RoadSegment", back_populates="status_records")

# 19. Notifications
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    recipient_id = Column(String(36), nullable=True)
    channel = Column(String(30), default="DASHBOARD") # DASHBOARD, BROWSER, EMAIL, SMS
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="INFO") # INFO, WARNING, CRITICAL
    entity_type = Column(String(50), nullable=True) # risk_prediction, government_alert, citizen_report
    entity_id = Column(String(36), nullable=True)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)

# 20. Data Sources (Health and provenance monitoring)
class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(50), primary_key=True) # e.g. IMD_WEATHER, IMD_RAINFALL, IMD_WARNINGS, BHUVAN_LEWS, NDMA_SACHET, IOT_SENSORS
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False) # METEOROLOGICAL, GEOSPATIAL, DISASTER_WARNING, IOT_TELEMETRY
    endpoint_url = Column(String(255), nullable=True)
    status = Column(String(20), default="ONLINE") # LIVE, RECENT, STALE, OFFLINE
    last_successful_sync = Column(DateTime, nullable=True)
    last_attempt = Column(DateTime, nullable=True)
    consecutive_failures = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    last_error_message = Column(Text, nullable=True)
    dataset_version = Column(String(50), nullable=True)
    records_synced_today = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 21. API Logs
class ApiLog(Base):
    __tablename__ = "api_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    path = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    latency_ms = Column(Float, nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_id = Column(String(36), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

# 22. Model Versions
class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    version_tag = Column(String(50), unique=True, nullable=False)
    model_name = Column(String(100), nullable=False)
    algorithm = Column(String(100), nullable=False) # e.g. GradientBoostingClassifier, XGBoostClassifier, RandomForestClassifier
    dataset_size = Column(Integer, nullable=False)
    features_list = Column(JSON, nullable=False)
    hyperparameters = Column(JSON, nullable=True)
    validation_metrics = Column(JSON, nullable=False) # accuracy, precision, recall, f1, roc_auc, confusion_matrix
    status = Column(String(20), default="ACTIVE") # ACTIVE, ARCHIVED, STAGING
    trained_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    trained_by = Column(String(100), default="SYSTEM_PIPELINE")

# 23. Model Predictions (Audit inference log)
class ModelPredictionLog(Base):
    __tablename__ = "model_predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_version_id = Column(String(36), nullable=False)
    location_id = Column(String(50), nullable=False, index=True)
    input_vector = Column(JSON, nullable=False)
    output_probability = Column(Float, nullable=False)
    output_class = Column(String(20), nullable=False)
    inference_time_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# 24. Audit Logs
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True) # MODEL_ACTIVATED, REPORT_VERIFIED, ROAD_STATUS_UPDATED, ALERT_CREATED, USER_LOGIN
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    result_status = Column(String(20), default="SUCCESS") # SUCCESS, FAILED
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")
