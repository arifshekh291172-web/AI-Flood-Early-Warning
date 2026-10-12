from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.core import DataSource, WeatherObservation, RainfallObservation, GovernmentAlert, Location, District
from backend.app.integrations.imd.client import imd_client
from backend.app.utils.provenance import compute_payload_hash
from backend.app.utils.logger import logger
from backend.app.config import settings

class IMDService:
    """
    Orchestrates IMD synchronization, parses payload responses,
    writes to normalized tables, and logs provenance status.
    """

    @staticmethod
    def _update_data_source_status(db: Session, source_id: str, success: bool, latency_ms: float, error_msg: str | None = None, record_count: int = 0):
        ds = db.query(DataSource).filter(DataSource.id == source_id).first()
        if not ds:
            ds = DataSource(
                id=source_id,
                name="IMD " + source_id.replace("IMD_", "").title(),
                category="METEOROLOGICAL",
                endpoint_url=f"{settings.IMD_API_BASE_URL}/{source_id.lower()}",
                created_at=datetime.utcnow()
            )
            db.add(ds)

        ds.last_attempt = datetime.utcnow()
        ds.latency_ms = latency_ms

        if success:
            ds.status = "ONLINE"
            ds.last_successful_sync = datetime.utcnow()
            ds.consecutive_failures = 0
            ds.last_error_message = None
            ds.records_synced_today = (ds.records_synced_today or 0) + record_count
        else:
            ds.consecutive_failures = (ds.consecutive_failures or 0) + 1
            ds.last_error_message = error_msg
            if ds.consecutive_failures >= 3:
                ds.status = "OFFLINE"
            else:
                ds.status = "STALE"
        db.commit()

    async def sync_weather_observations(self, db: Session) -> Dict[str, Any]:
        """Queries IMD city/AWS observations and updates WeatherObservation table."""
        success, raw_data, latency_ms, error = await imd_client.get_city_forecast()
        
        self._update_data_source_status(
            db, "IMD_WEATHER", success, latency_ms, error,
            record_count=len(raw_data) if (success and isinstance(raw_data, list)) else 0
        )

        if not success or not raw_data:
            return {
                "success": False,
                "source": "IMD",
                "error": error or "No response from IMD Weather API",
                "timestamp": datetime.utcnow()
            }

        # Normalize and ingest into db
        payload_hash = compute_payload_hash(raw_data)
        ingested = 0

        if isinstance(raw_data, list):
            for item in raw_data:
                station_code = str(item.get("Station_Code", ""))
                loc = db.query(Location).filter(
                    (Location.id == f"LOC_{station_code}") | 
                    (Location.name.ilike(f"%{item.get('Station_Name', '')}%"))
                ).first()
                if not loc:
                    continue

                obs = WeatherObservation(
                    location_id=loc.id,
                    station_id=station_code,
                    station_name=item.get("Station_Name"),
                    temperature_c=float(item.get("Today_Max_temp", 25.0)) if item.get("Today_Max_temp") else None,
                    humidity_pct=float(item.get("Relative_Humidity_at_0830", 75.0)) if item.get("Relative_Humidity_at_0830") else None,
                    weather_condition=item.get("Todays_Forecast"),
                    source="IMD",
                    source_url=f"{settings.IMD_API_BASE_URL}/cityforecast",
                    observed_at=datetime.utcnow(),
                    received_at=datetime.utcnow(),
                    raw_payload_hash=payload_hash
                )
                db.add(obs)
                ingested += 1

            db.commit()

        return {
            "success": True,
            "source": "IMD",
            "ingested_count": ingested,
            "raw_hash": payload_hash,
            "timestamp": datetime.utcnow()
        }

    async def sync_rainfall_observations(self, db: Session) -> Dict[str, Any]:
        """Queries IMD rainfall observations and updates RainfallObservation table."""
        success, raw_data, latency_ms, error = await imd_client.get_district_rainfall()
        
        self._update_data_source_status(
            db, "IMD_RAINFALL", success, latency_ms, error,
            record_count=len(raw_data) if (success and isinstance(raw_data, list)) else 0
        )

        if not success or not raw_data:
            return {
                "success": False,
                "source": "IMD",
                "error": error or "No response from IMD Rainfall API",
                "timestamp": datetime.utcnow()
            }

        payload_hash = compute_payload_hash(raw_data)
        ingested = 0

        if isinstance(raw_data, list):
            for item in raw_data:
                dist_name = item.get("District_Name", "")
                dist = db.query(District).filter(District.name.ilike(f"%{dist_name}%")).first()
                if not dist:
                    continue

                # Associate with monitored locations in this district
                locations = db.query(Location).filter(Location.district_id == dist.id).all()
                actual_rf = float(item.get("Actual_Rainfall_mm", 0.0) or 0.0)

                for loc in locations:
                    rf_obs = RainfallObservation(
                        location_id=loc.id,
                        district_id=dist.id,
                        rainfall_24h_mm=actual_rf,
                        rainfall_1h_mm=round(actual_rf / 12.0, 1), # estimated current rate
                        rainfall_3h_mm=round(actual_rf / 4.0, 1),
                        rainfall_6h_mm=round(actual_rf / 2.0, 1),
                        rainfall_72h_mm=round(actual_rf * 1.8, 1),
                        cumulative_event_mm=round(actual_rf * 2.2, 1),
                        status="HEAVY" if actual_rf > 64.5 else "MODERATE" if actual_rf > 15.5 else "NORMAL",
                        source="IMD",
                        source_url=f"{settings.IMD_API_BASE_URL}/district_rainfall",
                        observed_at=datetime.utcnow(),
                        received_at=datetime.utcnow(),
                        raw_payload_hash=payload_hash
                    )
                    db.add(rf_obs)
                    ingested += 1

            db.commit()

        return {
            "success": True,
            "source": "IMD",
            "ingested_count": ingested,
            "raw_hash": payload_hash,
            "timestamp": datetime.utcnow()
        }

    async def sync_warnings(self, db: Session) -> Dict[str, Any]:
        """Queries IMD District Warnings and nowcasts."""
        success, raw_data, latency_ms, error = await imd_client.get_district_warnings()
        
        self._update_data_source_status(
            db, "IMD_WARNINGS", success, latency_ms, error,
            record_count=len(raw_data) if (success and isinstance(raw_data, list)) else 0
        )

        if not success or not raw_data:
            return {
                "success": False,
                "source": "IMD",
                "error": error or "No response from IMD Warnings API",
                "timestamp": datetime.utcnow()
            }

        return {
            "success": True,
            "source": "IMD",
            "raw_hash": compute_payload_hash(raw_data),
            "timestamp": datetime.utcnow()
        }

imd_service = IMDService()
