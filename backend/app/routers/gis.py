from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from backend.app.database import get_db
from backend.app.models.core import (
    Location, District, State, RiskPrediction, 
    RiskZone, HistoricalLandslide, RoadSegment, 
    RoadStatus, CitizenReport, FieldReport
)
from backend.app.utils.provenance import to_ist_string

router = APIRouter(prefix="/api", tags=["GIS & Spatial Intelligence"])

@router.get("/states")
def get_states(db: Session = Depends(get_db)):
    states = db.query(State).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "capital": s.capital,
            "centroid_lat": s.centroid_lat,
            "centroid_lon": s.centroid_lon
        } for s in states
    ]

@router.get("/districts")
def get_districts(
    state_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(District)
    if state_id:
        query = query.filter(District.state_id == state_id)
    districts = query.all()
    return [
        {
            "id": d.id,
            "state_id": d.state_id,
            "name": d.name,
            "centroid_lat": d.centroid_lat,
            "centroid_lon": d.centroid_lon,
            "area_sqkm": d.area_sqkm
        } for d in districts
    ]

@router.get("/locations")
def get_locations(
    state_id: Optional[str] = Query(None),
    district_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Location)
    if state_id:
        query = query.filter(Location.state_id == state_id)
    if district_id:
        query = query.filter(Location.district_id == district_id)
    locations = query.all()

    return [
        {
            "id": l.id,
            "name": l.name,
            "district_id": l.district_id,
            "state_id": l.state_id,
            "latitude": l.latitude,
            "longitude": l.longitude,
            "elevation_m": l.elevation_m,
            "slope_deg": l.slope_deg,
            "geology_type": l.geology_type,
            "hazard_susceptibility": l.hazard_susceptibility
        } for l in locations
    ]

@router.get("/map/layers")
def get_map_layers(
    state_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns aggregated GeoJSON layers for rendering on interactive Leaflet / MapLibre GIS map.
    """
    now = datetime.utcnow()

    # 1. Monitored Hazard Points with latest Risk Scores
    loc_query = db.query(Location).filter(Location.is_active_monitoring == True)
    if state_id:
        loc_query = loc_query.filter(Location.state_id == state_id)
    locations = loc_query.all()

    hazard_features = []
    for loc in locations:
        latest_pred = db.query(RiskPrediction).filter(
            RiskPrediction.location_id == loc.id
        ).order_by(RiskPrediction.prediction_time.desc()).first()

        risk_prob = latest_pred.risk_probability if latest_pred else 0.20
        risk_class = latest_pred.risk_class if latest_pred else "LOW"
        triggers = latest_pred.thresholds_exceeded if latest_pred else []

        hazard_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [loc.longitude, loc.latitude]
            },
            "properties": {
                "id": loc.id,
                "name": loc.name,
                "district_name": loc.district.name if loc.district else loc.district_id,
                "state_id": loc.state_id,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "elevation_m": loc.elevation_m,
                "slope_deg": loc.slope_deg,
                "geology_type": loc.geology_type,
                "risk_probability": risk_prob,
                "risk_class": risk_class, # LOW (green), MODERATE (yellow), HIGH (orange), CRITICAL (red)
                "thresholds_exceeded": triggers,
                "last_update_ist": to_ist_string(latest_pred.prediction_time if latest_pred else loc.updated_at)
            }
        })

    # 2. Historical Landslides from Bhuvan / GSI
    hist_query = db.query(HistoricalLandslide)
    if state_id:
        hist_query = hist_query.filter(HistoricalLandslide.state_id == state_id)
    historical_slides = hist_query.all()

    historical_features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [h.longitude, h.latitude]
            },
            "properties": {
                "id": h.id,
                "location_name": h.location_name,
                "state_id": h.state_id,
                "event_date": h.event_date.strftime("%Y-%m-%d"),
                "trigger_cause": h.trigger_cause,
                "casualties": h.casualties,
                "source": h.source
            }
        } for h in historical_slides
    ]

    # 3. Active Risk Zones
    zones = db.query(RiskZone).filter(RiskZone.valid_until > now).all()
    zone_features = [
        {
            "type": "Feature",
            "geometry": z.geometry_geojson,
            "properties": {
                "id": z.id,
                "name": z.zone_name,
                "risk_level": z.risk_level,
                "area_sqkm": z.area_sqkm,
                "valid_until_ist": to_ist_string(z.valid_until)
            }
        } for z in zones
    ]

    # 4. Road Network Segments
    roads = db.query(RoadSegment).all()
    road_features = []
    for rd in roads:
        latest_st = db.query(RoadStatus).filter(
            RoadStatus.road_segment_id == rd.id
        ).order_by(RoadStatus.updated_at.desc()).first()

        status_val = latest_st.status if latest_st else "OPEN"
        cause_val = latest_st.cause if latest_st else ""

        road_features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [rd.start_lon, rd.start_lat],
                    [rd.end_lon, rd.end_lat]
                ]
            },
            "properties": {
                "id": rd.id,
                "name": rd.name,
                "highway_number": rd.highway_number,
                "state_id": rd.state_id,
                "status": status_val, # OPEN, PARTIALLY_BLOCKED, BLOCKED, UNKNOWN
                "cause": cause_val,
                "source_attribution": latest_st.source_attribution if latest_st else "GOVERNMENT_SOURCE"
            }
        })

    # 5. Citizen & Field Reports
    reports = db.query(CitizenReport).filter(
        CitizenReport.status.in_(["SUBMITTED", "UNDER_REVIEW", "VERIFIED"])
    ).limit(30).all()

    report_features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [rep.longitude, rep.latitude]
            },
            "properties": {
                "id": rep.id,
                "report_number": rep.report_number,
                "report_type": rep.report_type,
                "description": rep.description,
                "status": rep.status,
                "submitted_at_ist": to_ist_string(rep.submitted_at)
            }
        } for rep in reports
    ]

    return {
        "hazard_locations": {
            "type": "FeatureCollection",
            "features": hazard_features
        },
        "risk_zones": {
            "type": "FeatureCollection",
            "features": zone_features
        },
        "historical_landslides": {
            "type": "FeatureCollection",
            "features": historical_features
        },
        "road_network": {
            "type": "FeatureCollection",
            "features": road_features
        },
        "incident_reports": {
            "type": "FeatureCollection",
            "features": report_features
        }
    }
