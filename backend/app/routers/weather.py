from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from backend.app.database import get_db
from backend.app.models.core import WeatherObservation, Location, District, State
from backend.app.utils.provenance import to_ist_string, evaluate_provenance_status

router = APIRouter(prefix="/api/weather", tags=["Weather Observations"])

@router.get("/current")
def get_current_weather(
    state_id: Optional[str] = Query(None, description="State code e.g. AS, AR, ML, SK"),
    district_id: Optional[str] = Query(None, description="District ID"),
    db: Session = Depends(get_db)
):
    """
    Returns latest verified meteorological observations from IMD stations.
    Every record contains explicit provenance, source URL, and timestamp.
    """
    query = db.query(Location).join(WeatherObservation, Location.id == WeatherObservation.location_id)
    if state_id:
        query = query.filter(Location.state_id == state_id)
    if district_id:
        query = query.filter(Location.district_id == district_id)

    locations = query.distinct().all()

    observations = []
    temps = []
    humidities = []

    for loc in locations:
        latest = db.query(WeatherObservation).filter(
            WeatherObservation.location_id == loc.id
        ).order_by(WeatherObservation.observed_at.desc()).first()

        if not latest:
            continue

        status_code, status_display = evaluate_provenance_status(latest.observed_at)
        if latest.temperature_c is not None:
            temps.append(latest.temperature_c)
        if latest.humidity_pct is not None:
            humidities.append(latest.humidity_pct)

        observations.append({
            "id": latest.id,
            "location_id": loc.id,
            "location_name": loc.name,
            "district_name": loc.district.name if loc.district else loc.district_id,
            "state_id": loc.state_id,
            "station_id": latest.station_id,
            "station_name": latest.station_name,
            "temperature_c": latest.temperature_c,
            "humidity_pct": latest.humidity_pct,
            "pressure_hpa": latest.pressure_hpa,
            "wind_speed_kmh": latest.wind_speed_kmh,
            "wind_direction_deg": latest.wind_direction_deg,
            "weather_condition": latest.weather_condition,
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
        "summary": {
            "avg_temperature_c": round(sum(temps)/len(temps), 1) if temps else None,
            "avg_humidity_pct": round(sum(humidities)/len(humidities), 1) if humidities else None,
            "data_source": "India Meteorological Department (api.imd.gov.in)"
        },
        "observations": observations
    }
