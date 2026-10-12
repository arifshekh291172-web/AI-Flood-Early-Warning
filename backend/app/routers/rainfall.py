from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from backend.app.database import get_db
from backend.app.models.core import RainfallObservation, Location, District
from backend.app.utils.provenance import to_ist_string, evaluate_provenance_status

router = APIRouter(prefix="/api/rainfall", tags=["Rainfall Analytics"])

@router.get("/latest")
def get_latest_rainfall(
    state_id: Optional[str] = Query(None),
    district_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns latest 1h, 3h, 6h, 24h, 72h accumulated rainfall observations.
    All figures link directly to IMD district/station rain gauge feeds.
    """
    query = db.query(Location)
    if state_id:
        query = query.filter(Location.state_id == state_id)
    if district_id:
        query = query.filter(Location.district_id == district_id)

    locations = query.all()
    observations = []
    max_24h = 0.0
    highest_station = None
    districts_heavy = set()

    for loc in locations:
        latest = db.query(RainfallObservation).filter(
            RainfallObservation.location_id == loc.id
        ).order_by(RainfallObservation.observed_at.desc()).first()

        if not latest:
            continue

        status_code, status_display = evaluate_provenance_status(latest.observed_at)
        rf24 = latest.rainfall_24h_mm or 0.0

        if rf24 > max_24h:
            max_24h = rf24
            highest_station = loc.name

        if rf24 >= 64.5:
            districts_heavy.add(loc.district.name if loc.district else loc.district_id)

        observations.append({
            "id": latest.id,
            "location_id": loc.id,
            "location_name": loc.name,
            "district_name": loc.district.name if loc.district else loc.district_id,
            "state_id": loc.state_id,
            "rainfall_1h_mm": latest.rainfall_1h_mm,
            "rainfall_3h_mm": latest.rainfall_3h_mm,
            "rainfall_6h_mm": latest.rainfall_6h_mm,
            "rainfall_24h_mm": latest.rainfall_24h_mm,
            "rainfall_72h_mm": latest.rainfall_72h_mm,
            "cumulative_event_mm": latest.cumulative_event_mm,
            "status": latest.status,
            "provenance": {
                "source_name": latest.source,
                "source_url": latest.source_url,
                "observed_at_ist": to_ist_string(latest.observed_at),
                "retrieved_at_ist": to_ist_string(latest.received_at),
                "status": status_code,
                "status_display": status_display,
                "raw_payload_hash": latest.raw_payload_hash
            }
        })

    return {
        "count": len(observations),
        "analytics": {
            "highest_24h_station": highest_station,
            "highest_24h_mm": max_24h,
            "districts_under_heavy_rain": list(districts_heavy),
            "imd_heavy_rain_threshold_mm": 64.5,
            "imd_very_heavy_threshold_mm": 115.6
        },
        "observations": observations
    }

@router.get("/history")
def get_rainfall_history(
    location_id: Optional[str] = Query(None),
    hours: int = Query(72, ge=6, le=168),
    db: Session = Depends(get_db)
):
    """
    Returns time-series precipitation points for interactive charting.
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    query = db.query(RainfallObservation).filter(RainfallObservation.observed_at >= cutoff)
    if location_id:
        query = query.filter(RainfallObservation.location_id == location_id)

    records = query.order_by(RainfallObservation.observed_at.asc()).all()

    series = [
        {
            "timestamp_ist": to_ist_string(r.observed_at),
            "rainfall_mm": r.rainfall_24h_mm or 0.0,
            "rainfall_1h_mm": r.rainfall_1h_mm or 0.0,
            "location_id": r.location_id,
            "status": r.status
        } for r in records
    ]

    return {
        "location_id": location_id,
        "hours_requested": hours,
        "points_count": len(series),
        "series": series
    }
