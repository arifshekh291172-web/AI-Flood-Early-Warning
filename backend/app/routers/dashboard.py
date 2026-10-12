from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from backend.app.database import get_db
from backend.app.models.core import (
    RiskZone, Location, RiskPrediction, GovernmentAlert, 
    RainfallObservation, CitizenReport, FieldReport, DataSource
)
from backend.app.ml.model_loader import model_registry
from backend.app.utils.provenance import to_ist_string
from backend.app.config import settings

router = APIRouter(prefix="/api/dashboard", tags=["Operational Dashboard"])

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Returns live Operational Command Center metrics.
    All numbers are computed strictly from real database tables.
    """
    now = datetime.utcnow()

    # 1. Active Risk Zones
    active_risk_zones = db.query(RiskZone).filter(RiskZone.valid_until > now).count()

    # 2. High & Critical Risk Locations (based on latest predictions)
    # Get latest prediction per location
    locations = db.query(Location).filter(Location.is_active_monitoring == True).all()
    high_risk_count = 0
    critical_risk_count = 0
    top_critical = []

    for loc in locations:
        latest_pred = db.query(RiskPrediction).filter(
            RiskPrediction.location_id == loc.id
        ).order_by(RiskPrediction.prediction_time.desc()).first()

        if latest_pred:
            if latest_pred.risk_class == "CRITICAL":
                critical_risk_count += 1
                top_critical.append({
                    "location_id": loc.id,
                    "location_name": loc.name,
                    "district_id": loc.district_id,
                    "state_id": loc.state_id,
                    "risk_class": "CRITICAL",
                    "risk_probability": latest_pred.risk_probability,
                    "elevation_m": loc.elevation_m,
                    "slope_deg": loc.slope_deg,
                    "thresholds_exceeded": latest_pred.thresholds_exceeded or []
                })
            elif latest_pred.risk_class == "HIGH":
                high_risk_count += 1
                top_critical.append({
                    "location_id": loc.id,
                    "location_name": loc.name,
                    "district_id": loc.district_id,
                    "state_id": loc.state_id,
                    "risk_class": "HIGH",
                    "risk_probability": latest_pred.risk_probability,
                    "elevation_m": loc.elevation_m,
                    "slope_deg": loc.slope_deg,
                    "thresholds_exceeded": latest_pred.thresholds_exceeded or []
                })

    top_critical.sort(key=lambda x: x["risk_probability"], reverse=True)

    # 3. Official Government Warnings (IMD / NDMA)
    official_warnings_count = db.query(GovernmentAlert).filter(
        GovernmentAlert.status == "ACTIVE",
        GovernmentAlert.valid_until > now
    ).count()

    # 4. Rainfall Alerts (Districts with heavy or extreme rainfall)
    rainfall_alerts_count = db.query(RainfallObservation).filter(
        RainfallObservation.status.in_(["HEAVY", "VERY_HEAVY", "EXTREME"])
    ).count()

    # 5. Citizen & Field Reports
    field_reports_pending = db.query(CitizenReport).filter(
        CitizenReport.status.in_(["SUBMITTED", "UNDER_REVIEW"])
    ).count()

    # 6. Data Sources Online
    total_sources = db.query(DataSource).count()
    online_sources = db.query(DataSource).filter(DataSource.status == "ONLINE").count()

    # 7. Recent Official Warnings Feed
    active_warnings = db.query(GovernmentAlert).filter(
        GovernmentAlert.status == "ACTIVE"
    ).order_by(GovernmentAlert.issued_at.desc()).limit(5).all()

    warnings_feed = [
        {
            "id": w.id,
            "source": w.alert_source,
            "official_alert_id": w.official_alert_id,
            "alert_type": w.alert_type,
            "severity": w.severity,
            "headline": w.headline,
            "state_id": w.state_id,
            "issued_at_ist": to_ist_string(w.issued_at),
            "valid_until_ist": to_ist_string(w.valid_until)
        } for w in active_warnings
    ]

    meta = model_registry.get_metadata()

    return {
        "operational_mode": settings.OPERATIONAL_MODE,
        "timestamp_ist": to_ist_string(now),
        "kpis": {
            "active_risk_zones": active_risk_zones,
            "high_risk_locations": high_risk_count + critical_risk_count,
            "critical_locations": critical_risk_count,
            "official_warnings": official_warnings_count,
            "rainfall_alerts": rainfall_alerts_count,
            "pending_field_reports": field_reports_pending,
            "data_sources_online": f"{online_sources}/{total_sources}"
        },
        "top_critical_locations": top_critical[:6],
        "active_warnings_feed": warnings_feed,
        "active_model_version": meta.get("version_tag", "NE-SHIELD-v1.0")
    }
