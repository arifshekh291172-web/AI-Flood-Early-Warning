from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, Base, engine
from backend.app.models.core import (
    Role, User, State, District, Location, TerrainFeature,
    WeatherObservation, RainfallObservation, SensorReading,
    RoadSegment, RoadStatus, DataSource, RiskZone
)
from backend.app.integrations.bhuvan.client import bhuvan_client
from backend.app.integrations.ndma.client import ndma_client
from backend.app.utils.security import get_password_hash
from backend.app.utils.logger import logger
from backend.app.gis.spatial_utils import create_circular_polygon_geojson

def seed_initial_data(db: Session | None = None):
    close_at_end = False
    if db is None:
        db = SessionLocal()
        close_at_end = True

    try:
        # Create all tables if they don't exist
        Base.metadata.create_all(bind=engine)

        # 1. Seed Roles
        roles_data = [
            {"id": 1, "name": "ADMIN", "description": "Full system administrator with ML model training and audit access", "permissions": ["all"]},
            {"id": 2, "name": "DISTRICT_AUTHORITY", "description": "District Emergency Operations Center & Disaster Authorities", "permissions": ["dashboard", "alerts", "reports", "gis", "risk"]},
            {"id": 3, "name": "FIELD_OFFICER", "description": "Field Ground Verification & Road Network Officers (ASDMA, BRO, PWD)", "permissions": ["field", "reports", "roads"]},
            {"id": 4, "name": "ANALYST", "description": "Scientific Geologist & Meteorological Data Analyst", "permissions": ["analytics", "ml", "data"]},
            {"id": 5, "name": "CITIZEN", "description": "Public User / Community Reporter", "permissions": ["submit_report", "view_warnings"]}
        ]
        for r in roles_data:
            existing_role = db.query(Role).filter(Role.id == r["id"]).first()
            if not existing_role:
                db.add(Role(**r))
        db.commit()

        # 2. Seed Default Users
        users_data = [
            {"email": "admin@ne-shield.gov.in", "full_name": "Dr. Pranjal Saikia (Director NE-SHIELD)", "role_id": 1, "department": "National Disaster Management Center", "phone": "+919864011223"},
            {"email": "authority@asema.gov.in", "full_name": "Kabir Sharma (DEOC Officer)", "role_id": 2, "department": "ASDMA / District Magistrate Office", "phone": "+919864022334", "state_jurisdiction": "AS"},
            {"email": "officer@pwd.gov.in", "full_name": "Tenzing Norbu (Assistant Executive Engineer)", "role_id": 3, "department": "Border Roads Organisation / PWD", "phone": "+919864033445", "state_jurisdiction": "AR"},
            {"email": "analyst@gsi.gov.in", "full_name": "Dr. Ananya Roy (Senior Geologist)", "role_id": 4, "department": "Geological Survey of India (NER)", "phone": "+919864044556"},
            {"email": "citizen@ne-shield.org", "full_name": "Romen Singha", "role_id": 5, "department": "Citizen Volunteer", "phone": "+919864055667", "state_jurisdiction": "MN"}
        ]
        for u in users_data:
            existing_u = db.query(User).filter(User.email == u["email"]).first()
            if not existing_u:
                password = f"{u['role_id']}@ne-shield" if u["role_id"] != 1 else "Admin@123"
                if u["email"] == "authority@asema.gov.in":
                    password = "Authority@123"
                elif u["email"] == "officer@pwd.gov.in":
                    password = "Officer@123"
                elif u["email"] == "analyst@gsi.gov.in":
                    password = "Analyst@123"
                elif u["email"] == "citizen@ne-shield.org":
                    password = "Citizen@123"
                db.add(User(
                    email=u["email"],
                    hashed_password=get_password_hash(password),
                    full_name=u["full_name"],
                    role_id=u["role_id"],
                    department=u["department"],
                    phone=u["phone"],
                    state_jurisdiction=u.get("state_jurisdiction")
                ))
        db.commit()

        # 3. Seed States (8 North Eastern States)
        states_data = [
            {"id": "AS", "name": "Assam", "capital": "Dispur", "centroid_lat": 26.2006, "centroid_lon": 92.9376},
            {"id": "AR", "name": "Arunachal Pradesh", "capital": "Itanagar", "centroid_lat": 28.2180, "centroid_lon": 94.7278},
            {"id": "MN", "name": "Manipur", "capital": "Imphal", "centroid_lat": 24.6637, "centroid_lon": 93.9063},
            {"id": "ML", "name": "Meghalaya", "capital": "Shillong", "centroid_lat": 25.4670, "centroid_lon": 91.3662},
            {"id": "MZ", "name": "Mizoram", "capital": "Aizawl", "centroid_lat": 23.1645, "centroid_lon": 92.9376},
            {"id": "NL", "name": "Nagaland", "capital": "Kohima", "centroid_lat": 26.1584, "centroid_lon": 94.5624},
            {"id": "SK", "name": "Sikkim", "capital": "Gangtok", "centroid_lat": 27.5330, "centroid_lon": 88.5122},
            {"id": "TR", "name": "Tripura", "capital": "Agartala", "centroid_lat": 23.9408, "centroid_lon": 91.9882}
        ]
        for s in states_data:
            if not db.query(State).filter(State.id == s["id"]).first():
                db.add(State(**s))
        db.commit()

        # 4. Seed Key Vulnerable Districts
        districts_data = [
            # Assam
            {"id": "AS_KAMRUP_METRO", "state_id": "AS", "name": "Kamrup Metropolitan", "centroid_lat": 26.1445, "centroid_lon": 91.7362, "area_sqkm": 955.0},
            {"id": "AS_DIMA_HASAO", "state_id": "AS", "name": "Dima Hasao", "centroid_lat": 25.1740, "centroid_lon": 93.0210, "area_sqkm": 4888.0},
            {"id": "AS_CACHAR", "state_id": "AS", "name": "Cachar", "centroid_lat": 24.8333, "centroid_lon": 92.7789, "area_sqkm": 3786.0},

            # Arunachal Pradesh
            {"id": "AR_WEST_KAMENG", "state_id": "AR", "name": "West Kameng", "centroid_lat": 27.2644, "centroid_lon": 92.4243, "area_sqkm": 7422.0},
            {"id": "AR_PAPUM_PARE", "state_id": "AR", "name": "Papum Pare", "centroid_lat": 27.1500, "centroid_lon": 93.6000, "area_sqkm": 2875.0},
            {"id": "AR_TAWANG", "state_id": "AR", "name": "Tawang", "centroid_lat": 27.5861, "centroid_lon": 91.8594, "area_sqkm": 2172.0},

            # Meghalaya
            {"id": "ML_EAST_KHASI", "state_id": "ML", "name": "East Khasi Hills", "centroid_lat": 25.5788, "centroid_lon": 91.8933, "area_sqkm": 2748.0},
            {"id": "ML_RI_BHOI", "state_id": "ML", "name": "Ri-Bhoi", "centroid_lat": 25.9000, "centroid_lon": 91.8800, "area_sqkm": 2448.0},

            # Manipur
            {"id": "MN_NONEY", "state_id": "MN", "name": "Noney", "centroid_lat": 24.7890, "centroid_lon": 93.6330, "area_sqkm": 1050.0},
            {"id": "MN_IMPHAL_WEST", "state_id": "MN", "name": "Imphal West", "centroid_lat": 24.8170, "centroid_lon": 93.9368, "area_sqkm": 558.0},

            # Mizoram
            {"id": "MZ_AIZAWL", "state_id": "MZ", "name": "Aizawl", "centroid_lat": 23.7271, "centroid_lon": 92.7176, "area_sqkm": 3575.0},

            # Nagaland
            {"id": "NL_KOHIMA", "state_id": "NL", "name": "Kohima", "centroid_lat": 25.6701, "centroid_lon": 94.1077, "area_sqkm": 1463.0},

            # Sikkim
            {"id": "SK_EAST", "state_id": "SK", "name": "Gangtok (East Sikkim)", "centroid_lat": 27.3314, "centroid_lon": 88.6138, "area_sqkm": 954.0},

            # Tripura
            {"id": "TR_DHALAI", "state_id": "TR", "name": "Dhalai", "centroid_lat": 23.8500, "centroid_lon": 91.9000, "area_sqkm": 2522.0}
        ]
        for d in districts_data:
            if not db.query(District).filter(District.id == d["id"]).first():
                db.add(District(**d))
        db.commit()

        # 5. Seed Monitored Landslide Hazard Locations
        locations_data = [
            {"id": "LOC_HAFLONG_HILL", "name": "Haflong Hill Section KM 118", "district_id": "AS_DIMA_HASAO", "state_id": "AS", "latitude": 25.1780, "longitude": 93.0230, "elevation_m": 850.0, "slope_deg": 41.5, "geology_type": "Disang Shale & Sandstone", "hazard_susceptibility": "VERY_HIGH"},
            {"id": "LOC_GUWAHATI_NARAKASUR", "name": "Narakasur Hill Escarpment, Guwahati", "district_id": "AS_KAMRUP_METRO", "state_id": "AS", "latitude": 26.1360, "longitude": 91.7610, "elevation_m": 220.0, "slope_deg": 38.0, "geology_type": "Precambrian Gneiss weathered saprolite", "hazard_susceptibility": "HIGH"},
            {"id": "LOC_BHALUKPONG_NH13", "name": "Bhalukpong-Tenga NH-13 Sector", "district_id": "AR_WEST_KAMENG", "state_id": "AR", "latitude": 27.2150, "longitude": 92.5400, "elevation_m": 1280.0, "slope_deg": 44.0, "geology_type": "Lesser Himalayan Quartzite & Phyllite", "hazard_susceptibility": "CRITICAL"},
            {"id": "LOC_ITANAGAR_KARSINGSA", "name": "Karsingsa Sinking Zone, Itanagar", "district_id": "AR_PAPUM_PARE", "state_id": "AR", "latitude": 27.1280, "longitude": 93.7140, "elevation_m": 720.0, "slope_deg": 36.5, "geology_type": "Siwalik Sandstone & Mudstone", "hazard_susceptibility": "HIGH"},
            {"id": "LOC_SOHRA_ECOPARK", "name": "Sohra (Cherrapunji) Cliff Edge", "district_id": "ML_EAST_KHASI", "state_id": "ML", "latitude": 25.2890, "longitude": 91.7240, "elevation_m": 1430.0, "slope_deg": 46.0, "geology_type": "Cretaceous-Tertiary Sandstone", "hazard_susceptibility": "CRITICAL"},
            {"id": "LOC_UMIAM_BYPASS", "name": "NH-6 Umiam Lake Cut Slopes", "district_id": "ML_RI_BHOI", "state_id": "ML", "latitude": 25.6810, "longitude": 91.9050, "elevation_m": 1020.0, "slope_deg": 35.0, "geology_type": "Shillong Group Quartzite", "hazard_susceptibility": "MODERATE"},
            {"id": "LOC_TUPUL_YARD", "name": "Tupul Railway Station Axis", "district_id": "MN_NONEY", "state_id": "MN", "latitude": 24.7890, "longitude": 93.6330, "elevation_m": 780.0, "slope_deg": 42.0, "geology_type": "Disang Shale (highly sheared)", "hazard_susceptibility": "CRITICAL"},
            {"id": "LOC_AIZAWL_MELTHUM", "name": "Melthum Ridge & Quarry Corridor, Aizawl", "district_id": "MZ_AIZAWL", "state_id": "MZ", "latitude": 23.6870, "longitude": 92.7120, "elevation_m": 1150.0, "slope_deg": 43.5, "geology_type": "Bhuban Sandstone & Siltstone", "hazard_susceptibility": "VERY_HIGH"},
            {"id": "LOC_KOHIMA_PHESAMA", "name": "Phesama Sinking Sector, NH-29", "district_id": "NL_KOHIMA", "state_id": "NL", "latitude": 25.6230, "longitude": 94.1080, "elevation_m": 1420.0, "slope_deg": 37.0, "geology_type": "Barail Sandstone over Disang Shale", "hazard_susceptibility": "HIGH"},
            {"id": "LOC_GANGTOK_JNROAD", "name": "9th Mile JN Road, Gangtok-Nathu La", "district_id": "SK_EAST", "state_id": "SK", "latitude": 27.3590, "longitude": 88.6830, "elevation_m": 2450.0, "slope_deg": 48.0, "geology_type": "Chungthang Formation Schist & Gneiss", "hazard_susceptibility": "CRITICAL"},
            {"id": "LOC_AMBASSA_RIDGE", "name": "Ambassa Ridge Sector", "district_id": "TR_DHALAI", "state_id": "TR", "latitude": 23.9180, "longitude": 91.8540, "elevation_m": 290.0, "slope_deg": 32.0, "geology_type": "Tipam Sandstone", "hazard_susceptibility": "MODERATE"}
        ]

        for loc in locations_data:
            if not db.query(Location).filter(Location.id == loc["id"]).first():
                db.add(Location(**loc))
        db.commit()

        # 6. Seed Terrain Features for each location
        for loc in locations_data:
            if not db.query(TerrainFeature).filter(TerrainFeature.location_id == loc["id"]).first():
                db.add(TerrainFeature(
                    id=f"TF_{loc['id']}",
                    location_id=loc["id"],
                    slope_deg=loc["slope_deg"],
                    aspect_deg=180.0,
                    elevation_m=loc["elevation_m"],
                    curvature=-0.02 if loc["slope_deg"] > 40 else 0.01,
                    lithology=loc["geology_type"],
                    land_use="Degraded Forest / Road Slopes",
                    distance_to_fault_m=650.0 if "Disang" in loc["geology_type"] or "Metamorphic" in loc["geology_type"] else 1800.0,
                    distance_to_stream_m=180.0,
                    drainage_density=2.6,
                    soil_type="Clayey Silty Sand"
                ))
        db.commit()

        # 7. Seed Road Segments and initial Status
        road_segments = [
            {"id": "RD_NH27_HAFLONG", "name": "NH-27 Lumding-Haflong-Silchar Corridor", "highway_number": "NH-27", "state_id": "AS", "district_id": "AS_DIMA_HASAO", "start_lat": 25.750, "start_lon": 93.150, "end_lat": 24.833, "end_lon": 92.778, "source_type": "GOVERNMENT_SOURCE"},
            {"id": "RD_NH13_BHALUKPONG", "name": "NH-13 Trans-Arunachal Highway (Bhalukpong-Bomdila)", "highway_number": "NH-13", "state_id": "AR", "district_id": "AR_WEST_KAMENG", "start_lat": 27.012, "start_lon": 92.650, "end_lat": 27.350, "end_lon": 92.350, "source_type": "FIELD_VERIFIED"},
            {"id": "RD_NH6_SHILLONG", "name": "NH-6 Guwahati-Shillong-Silchar Lifeline", "highway_number": "NH-6", "state_id": "ML", "district_id": "ML_EAST_KHASI", "start_lat": 26.100, "start_lon": 91.800, "end_lat": 25.550, "end_lon": 91.900, "source_type": "GOVERNMENT_SOURCE"},
            {"id": "RD_NH29_KOHIMA", "name": "NH-29 Dimapur-Kohima-Imphal Highway", "highway_number": "NH-29", "state_id": "NL", "district_id": "NL_KOHIMA", "start_lat": 25.900, "start_lon": 93.750, "end_lat": 25.670, "end_lon": 94.110, "source_type": "FIELD_VERIFIED"},
            {"id": "RD_JNROAD_GANGTOK", "name": "Jawaharlal Nehru Road (Gangtok to Nathu La)", "highway_number": "JN-RD", "state_id": "SK", "district_id": "SK_EAST", "start_lat": 27.330, "start_lon": 88.610, "end_lat": 27.390, "end_lon": 88.830, "source_type": "FIELD_VERIFIED"}
        ]
        for rd in road_segments:
            if not db.query(RoadSegment).filter(RoadSegment.id == rd["id"]).first():
                db.add(RoadSegment(**rd))
                # Add default road status
                status_val = "PARTIALLY_BLOCKED" if "BHALUKPONG" in rd["id"] else "OPEN"
                cause_val = "Debris slide clearance ongoing at KM 52" if "BHALUKPONG" in rd["id"] else "Normal vehicular traffic moving smoothly"
                db.add(RoadStatus(
                    road_segment_id=rd["id"],
                    status=status_val,
                    cause=cause_val,
                    source_attribution=rd["source_type"],
                    updated_at=datetime.utcnow() - timedelta(minutes=45)
                ))
        db.commit()

        # 8. Seed Verified Historical Landslide Catalog & Government Alerts
        bhuvan_client.sync_historical_catalog(db)
        ndma_client.sync_verified_official_warnings(db)

        # 9. Seed Active Risk Zones
        critical_spots = [
            {"name": "Bhalukpong-Tenga Active Slide Zone", "district_id": "AR_WEST_KAMENG", "lat": 27.215, "lon": 92.540, "radius": 4.5, "level": "CRITICAL"},
            {"name": "Sohra Escarpment Hazard Zone", "district_id": "ML_EAST_KHASI", "lat": 25.289, "lon": 91.724, "radius": 3.8, "level": "HIGH"},
            {"name": "Haflong Sinking Hill Sector", "district_id": "AS_DIMA_HASAO", "lat": 25.178, "lon": 93.023, "radius": 5.0, "level": "HIGH"}
        ]
        for spot in critical_spots:
            if not db.query(RiskZone).filter(RiskZone.zone_name == spot["name"]).first():
                poly_geojson = create_circular_polygon_geojson(spot["lat"], spot["lon"], radius_km=spot["radius"])
                rz = RiskZone(
                    district_id=spot["district_id"],
                    zone_name=spot["name"],
                    risk_level=spot["level"],
                    geometry_geojson=poly_geojson,
                    area_sqkm=round(3.14159 * (spot["radius"] ** 2), 1),
                    valid_from=datetime.utcnow() - timedelta(hours=2),
                    valid_until=datetime.utcnow() + timedelta(hours=48)
                )
                db.add(rz)
        db.commit()

        # 10. Seed Initial Weather and Rainfall Observations (with strict IMD attribution)
        now = datetime.utcnow()
        for loc in locations_data:
            # Weather observation
            if not db.query(WeatherObservation).filter(WeatherObservation.location_id == loc["id"]).first():
                db.add(WeatherObservation(
                    location_id=loc["id"],
                    station_id=f"STN_{loc['id']}",
                    station_name=f"{loc['name']} IMD Station",
                    temperature_c=22.4 if loc["elevation_m"] > 1000 else 28.5,
                    humidity_pct=88.0 if "CRITICAL" in loc["hazard_susceptibility"] else 72.0,
                    pressure_hpa=1008.2,
                    wind_speed_kmh=14.5,
                    weather_condition="Heavy Rain Showers" if "CRITICAL" in loc["hazard_susceptibility"] else "Scattered Clouds",
                    source="IMD",
                    source_url="https://api.imd.gov.in/public/api_reference.html",
                    observed_at=now - timedelta(minutes=15),
                    received_at=now - timedelta(minutes=12),
                    raw_payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                ))

            # Rainfall observation
            if not db.query(RainfallObservation).filter(RainfallObservation.location_id == loc["id"]).first():
                rf24 = 124.5 if "CRITICAL" in loc["hazard_susceptibility"] else 68.0 if "HIGH" in loc["hazard_susceptibility"] else 18.2
                db.add(RainfallObservation(
                    location_id=loc["id"],
                    district_id=loc["district_id"],
                    rainfall_1h_mm=round(rf24 / 8.0, 1),
                    rainfall_3h_mm=round(rf24 / 3.0, 1),
                    rainfall_6h_mm=round(rf24 / 1.8, 1),
                    rainfall_24h_mm=rf24,
                    rainfall_72h_mm=round(rf24 * 1.7, 1),
                    cumulative_event_mm=round(rf24 * 2.1, 1),
                    status="EXTREME" if rf24 > 115.6 else "HEAVY" if rf24 > 64.5 else "NORMAL",
                    source="IMD",
                    source_url="https://api.imd.gov.in/public/api_reference.html",
                    observed_at=now - timedelta(minutes=15),
                    received_at=now - timedelta(minutes=12),
                    raw_payload_hash="a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0"
                ))

            # Sensor readings
            if not db.query(SensorReading).filter(SensorReading.location_id == loc["id"]).first():
                db.add(SensorReading(
                    sensor_id=f"IOT_{loc['id']}_SM",
                    location_id=loc["id"],
                    sensor_type="SoilMoisture",
                    value=88.5 if "CRITICAL" in loc["hazard_susceptibility"] else 52.0,
                    unit="%",
                    battery_level_pct=94.0,
                    signal_strength_dbm=-68.0,
                    recorded_at=now - timedelta(minutes=5),
                    source="FIELD_IOT_GATEWAY"
                ))
        db.commit()

        # 11. Seed Data Sources Registry
        data_sources_initial = [
            {"id": "IMD_WEATHER", "name": "IMD City & Weather Forecast API", "category": "METEOROLOGICAL", "endpoint_url": "https://api.imd.gov.in/api/v1/cityforecast", "status": "ONLINE", "last_successful_sync": now - timedelta(minutes=12), "latency_ms": 118.5, "records_synced_today": 88},
            {"id": "IMD_RAINFALL", "name": "IMD District & AWS Rainfall Service", "category": "METEOROLOGICAL", "endpoint_url": "https://api.imd.gov.in/api/v1/district_rainfall", "status": "ONLINE", "last_successful_sync": now - timedelta(minutes=12), "latency_ms": 142.0, "records_synced_today": 74},
            {"id": "IMD_WARNINGS", "name": "IMD District Warning & Nowcast Feed", "category": "METEOROLOGICAL", "endpoint_url": "https://api.imd.gov.in/api/v1/district_warnings", "status": "ONLINE", "last_successful_sync": now - timedelta(minutes=20), "latency_ms": 98.0, "records_synced_today": 16},
            {"id": "BHUVAN_LEWS", "name": "ISRO / NRSC Bhuvan Disaster Services", "category": "GEOSPATIAL", "endpoint_url": "https://bhuvan-vec1.nrsc.gov.in/bhuvan/wms", "status": "ONLINE", "last_successful_sync": now - timedelta(hours=1), "latency_ms": 85.0, "records_synced_today": 12},
            {"id": "NDMA_SACHET", "name": "NDMA / SACHET Machine-Readable Feed", "category": "DISASTER_WARNING", "endpoint_url": "https://sachet.ndma.gov.in/cap_feed", "status": "ONLINE", "last_successful_sync": now - timedelta(minutes=30), "latency_ms": 92.0, "records_synced_today": 3},
            {"id": "IOT_SENSORS", "name": "North East Hill Slope In-situ Sensor Network", "category": "IOT_TELEMETRY", "endpoint_url": "gateway.sensors.ne-shield.gov.in", "status": "ONLINE", "last_successful_sync": now - timedelta(minutes=5), "latency_ms": 34.0, "records_synced_today": 110},
            {"id": "ML_SERVICE", "name": "NE-SHIELD AI Landslide Inference Pipeline", "category": "AI_PREDICTION", "endpoint_url": "internal://ne_shield_ml_engine", "status": "ONLINE", "last_successful_sync": now - timedelta(minutes=2), "latency_ms": 4.5, "records_synced_today": 220}
        ]
        for ds in data_sources_initial:
            if not db.query(DataSource).filter(DataSource.id == ds["id"]).first():
                db.add(DataSource(**ds))
        db.commit()

        logger.info("Successfully completed database seeding for NE-SHIELD.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error during database initialization/seeding: {str(e)}")
        raise e
    finally:
        if close_at_end:
            db.close()

if __name__ == "__main__":
    seed_initial_data()
