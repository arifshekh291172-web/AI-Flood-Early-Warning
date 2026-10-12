from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from backend.app.database import get_db
from backend.app.models.core import Location, RiskPrediction, RiskZone, District
from backend.app.ml.predict import run_prediction_for_location, run_predictions_all_locations
from backend.app.ml.model_loader import model_registry
from backend.app.utils.provenance import to_ist_string

router = APIRouter(prefix="/api/risk", tags=["AI Landslide Risk Engine"])

@router.get("/current")
def get_current_risk_predictions(
    state_id: Optional[str] = Query(None),
    risk_class: Optional[str] = Query(None, description="LOW, MODERATE, HIGH, CRITICAL"),
    db: Session = Depends(get_db)
):
    """
    Returns latest ML model landslide failure risk scores and triggered geotechnical thresholds
    for all actively monitored hill slope locations across Northeast India.
    """
    query = db.query(Location).filter(Location.is_active_monitoring == True)
    if state_id:
        query = query.filter(Location.state_id == state_id)

    locations = query.all()
    results = []

    for loc in locations:
        latest = db.query(RiskPrediction).filter(
            RiskPrediction.location_id == loc.id
        ).order_by(RiskPrediction.prediction_time.desc()).first()

        # If no prediction exists yet, generate on-the-fly
        if not latest:
            pred_data = run_prediction_for_location(loc.id, db, save_to_db=True)
            prob = pred_data["risk_probability"]
            r_class = pred_data["risk_class"]
            triggers = pred_data["thresholds_exceeded"]
            features = pred_data["features"]
            model_ver = pred_data["model_version"]
            pred_time = pred_data["prediction_time"]
        else:
            prob = latest.risk_probability
            r_class = latest.risk_class
            triggers = latest.thresholds_exceeded or []
            features = latest.feature_snapshot
            model_ver = latest.model_version
            pred_time = latest.prediction_time

        if risk_class and r_class != risk_class:
            continue

        results.append({
            "category": "NE-SHIELD_AI_PREDICTION",
            "location_id": loc.id,
            "location_name": loc.name,
            "district_id": loc.district_id,
            "district_name": loc.district.name if loc.district else loc.district_id,
            "state_id": loc.state_id,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "slope_deg": loc.slope_deg,
            "elevation_m": loc.elevation_m,
            "geology_type": loc.geology_type,
            "risk_probability": prob,
            "risk_class": r_class,
            "model_version": model_ver,
            "thresholds_exceeded": triggers,
            "feature_snapshot": features,
            "prediction_time_ist": to_ist_string(pred_time),
            "provenance": {
                "engine": "NE-SHIELD Gradient Boosted Ensemble",
                "calibrated_for": "Northeast India Himalayan & Indo-Burma Ranges",
                "generated_at_ist": to_ist_string(pred_time)
            }
        })

    results.sort(key=lambda x: x["risk_probability"], reverse=True)

    meta = model_registry.get_metadata()

    return {
        "count": len(results),
        "active_model_version": meta.get("version_tag", "NE-SHIELD-v1.0"),
        "model_accuracy": meta.get("metrics", {}).get("accuracy"),
        "predictions": results
    }

@router.get("/history")
def get_risk_history(
    location_id: str = Query(..., description="Location ID to query history for"),
    limit: int = Query(50, ge=5, le=500),
    db: Session = Depends(get_db)
):
    """
    Returns immutable time-series historical risk predictions for trend analysis.
    """
    preds = db.query(RiskPrediction).filter(
        RiskPrediction.location_id == location_id
    ).order_by(RiskPrediction.prediction_time.desc()).limit(limit).all()

    items = [
        {
            "id": p.id,
            "prediction_time_ist": to_ist_string(p.prediction_time),
            "risk_probability": p.risk_probability,
            "risk_class": p.risk_class,
            "model_version": p.model_version,
            "rainfall_24h_mm": p.feature_snapshot.get("rainfall_24h_mm", 0.0),
            "soil_moisture_pct": p.feature_snapshot.get("soil_moisture_pct", 0.0)
        } for p in reversed(preds)
    ]

    return {
        "location_id": location_id,
        "history_count": len(items),
        "timeseries": items
    }

@router.get("/zones")
def get_risk_zones(db: Session = Depends(get_db)):
    """
    Returns active spatial polygon risk zones.
    """
    now = datetime.utcnow()
    zones = db.query(RiskZone).filter(RiskZone.valid_until > now).all()

    items = [
        {
            "id": z.id,
            "zone_name": z.zone_name,
            "district_id": z.district_id,
            "risk_level": z.risk_level,
            "area_sqkm": z.area_sqkm,
            "valid_from_ist": to_ist_string(z.valid_from),
            "valid_until_ist": to_ist_string(z.valid_until),
            "geometry_geojson": z.geometry_geojson
        } for z in zones
    ]

    return {
        "count": len(items),
        "zones": items
    }
