from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime

from backend.app.database import get_db
from backend.app.integrations.satellite.service import satellite_service
from backend.app.integrations.satellite.client import satellite_client
from backend.app.ml.train import train_landslide_model
from backend.app.ml.predict import run_satellite_predictions_all
from backend.app.ml.model_loader import model_registry
from backend.app.models.core import Location, RainfallObservation, SensorReading, WeatherObservation
from backend.app.utils.provenance import to_ist_string
from backend.app.utils.logger import logger

router = APIRouter(prefix="/api/satellite", tags=["Live Satellite Earth Observation & AI Prediction"])

@router.post("/sync")
async def sync_satellite_data(db: Session = Depends(get_db)):
    """
    Fetches real-time satellite Earth observation telemetry for all monitored hazard spots
    across Northeast India and records them in the database.
    """
    try:
        result = await satellite_service.sync_live_satellite_telemetry(db)
        return result
    except Exception as e:
        db.rollback()
        logger.error(f"Error syncing satellite data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Satellite sync error: {str(e)}")

@router.get("/latest")
def get_latest_satellite_telemetry(db: Session = Depends(get_db)):
    """
    Returns latest recorded satellite observations across all monitored locations.
    """
    locations = db.query(Location).filter(Location.is_active_monitoring == True).all()
    results = []

    for loc in locations:
        latest_rf = db.query(RainfallObservation).filter(
            RainfallObservation.location_id == loc.id,
            RainfallObservation.source == "SATELLITE_LIVE"
        ).order_by(RainfallObservation.observed_at.desc()).first()

        latest_wthr = db.query(WeatherObservation).filter(
            WeatherObservation.location_id == loc.id,
            WeatherObservation.source == "SATELLITE_LIVE"
        ).order_by(WeatherObservation.observed_at.desc()).first()

        latest_sm = db.query(SensorReading).filter(
            SensorReading.location_id == loc.id,
            SensorReading.sensor_type == "SoilMoisture"
        ).order_by(SensorReading.recorded_at.desc()).first()

        results.append({
            "location_id": loc.id,
            "location_name": loc.name,
            "district_id": loc.district_id,
            "state_id": loc.state_id,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "satellite_rainfall_1h_mm": latest_rf.rainfall_1h_mm if latest_rf else 0.0,
            "satellite_rainfall_24h_mm": latest_rf.rainfall_24h_mm if latest_rf else 0.0,
            "satellite_soil_moisture_pct": latest_sm.value if latest_sm else 45.0,
            "temperature_c": latest_wthr.temperature_c if latest_wthr else 25.0,
            "observed_at_ist": to_ist_string(latest_rf.observed_at) if latest_rf else None,
            "status": "ONLINE" if latest_rf else "AWAITING_SYNC"
        })

    return {
        "count": len(results),
        "satellite_telemetry": results
    }

@router.post("/predict")
def predict_on_satellite_data(db: Session = Depends(get_db)):
    """
    Executes the trained ML model inference across all monitored locations
    using the latest live satellite Earth observation telemetry.
    """
    try:
        predictions = run_satellite_predictions_all(db)
        meta = model_registry.get_metadata()
        return {
            "success": True,
            "model_version": meta.get("version_tag", "UNKNOWN"),
            "count": len(predictions),
            "generated_at_ist": to_ist_string(datetime.utcnow()),
            "predictions": predictions
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Satellite prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@router.post("/run-pipeline")
async def run_full_pipeline(
    algorithm: str = Query("GradientBoostingClassifier"),
    db: Session = Depends(get_db)
):
    """
    End-to-end Pipeline:
    1. Train ML Model on official Government Geotechnical/IMD/GSI dataset
    2. Ingest real-time Satellite Earth observation data for all locations
    3. Run AI Risk Inference on live satellite data and generate alerts
    """
    try:
        # Step 1: Train model on Gov Data
        logger.info("Pipeline Step 1: Training model on official Government geotechnical data...")
        clf, meta = train_landslide_model(algorithm=algorithm, db=db, user_email="pipeline@ne-shield.gov.in")
        model_registry.reload()

        # Step 2: Fetch live satellite data
        logger.info("Pipeline Step 2: Ingesting live satellite telemetry from Bhuvan & Earth Observation feeds...")
        sat_result = await satellite_service.sync_live_satellite_telemetry(db)

        # Step 3: Predict on live satellite data
        logger.info("Pipeline Step 3: Running AI Landslide/Flood Risk Predictions on live satellite inputs...")
        predictions = run_satellite_predictions_all(db, sat_result.get("telemetry", []))

        # Alert count
        critical_count = sum(1 for p in predictions if p["risk_class"] == "CRITICAL")
        high_count = sum(1 for p in predictions if p["risk_class"] == "HIGH")

        return {
            "success": True,
            "message": "Full end-to-end pipeline executed successfully!",
            "timestamp_ist": to_ist_string(datetime.utcnow()),
            "step1_training": {
                "version_tag": meta["version_tag"],
                "algorithm": meta["algorithm"],
                "dataset_size": meta["dataset_size"],
                "metrics": meta["metrics"]
            },
            "step2_satellite_sync": {
                "locations_synced": sat_result.get("locations_synced", 0),
                "bhuvan_wms_status": sat_result.get("bhuvan_wms_status", "ONLINE"),
                "average_latency_ms": sat_result.get("satellite_average_latency_ms", 0.0)
            },
            "step3_ai_predictions": {
                "total_monitored_spots": len(predictions),
                "critical_hazard_count": critical_count,
                "high_hazard_count": high_count,
                "predictions": predictions
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Pipeline execution failure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
