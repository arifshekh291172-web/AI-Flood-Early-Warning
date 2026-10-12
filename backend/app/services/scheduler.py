import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.integrations.imd.service import imd_service
from backend.app.integrations.bhuvan.client import bhuvan_client
from backend.app.integrations.ndma.client import ndma_client
from backend.app.ml.predict import run_predictions_all_locations
from backend.app.alerts.rules import evaluate_and_dispatch_risk_alerts
from backend.app.models.core import DataSource, ApiLog
from backend.app.utils.logger import logger

scheduler = AsyncIOScheduler()

async def job_imd_weather_sync():
    """Job 1: Ingests IMD current weather observations."""
    db: Session = SessionLocal()
    try:
        logger.info("Executing scheduled job: IMD Weather Ingestion")
        await imd_service.sync_weather_observations(db)
    except Exception as e:
        logger.error(f"Error in job_imd_weather_sync: {str(e)}")
    finally:
        db.close()

async def job_imd_rainfall_sync():
    """Job 2: Ingests IMD district/station rainfall observations."""
    db: Session = SessionLocal()
    try:
        logger.info("Executing scheduled job: IMD Rainfall Ingestion")
        await imd_service.sync_rainfall_observations(db)
    except Exception as e:
        logger.error(f"Error in job_imd_rainfall_sync: {str(e)}")
    finally:
        db.close()

async def job_imd_warnings_sync():
    """Job 3: Ingests IMD district warnings."""
    db: Session = SessionLocal()
    try:
        logger.info("Executing scheduled job: IMD Warnings Ingestion")
        await imd_service.sync_warnings(db)
    except Exception as e:
        logger.error(f"Error in job_imd_warnings_sync: {str(e)}")
    finally:
        db.close()

async def job_sensor_telemetry_sync():
    """Job 4: Ingests field IoT sensor telemetry."""
    # In production, queries IoT MQTT broker or REST gateway
    pass

async def job_ndma_alerts_sync():
    """Job 5: Ingests NDMA / SACHET CAP emergency feeds."""
    db: Session = SessionLocal()
    try:
        logger.info("Executing scheduled job: NDMA/SACHET Alert Sync")
        await ndma_client.fetch_active_alerts()
    except Exception as e:
        logger.error(f"Error in job_ndma_alerts_sync: {str(e)}")
    finally:
        db.close()

async def job_risk_prediction_engine():
    """Job 6: Refreshes real-time ML risk predictions across all monitored hazard points."""
    db: Session = SessionLocal()
    try:
        logger.info("Executing scheduled job: Real-time ML Risk Prediction Engine")
        results = run_predictions_all_locations(db)
        for res in results:
            if res.get("risk_class") in ["CRITICAL", "HIGH"]:
                evaluate_and_dispatch_risk_alerts(res, db)
    except Exception as e:
        logger.error(f"Error in job_risk_prediction_engine: {str(e)}")
    finally:
        db.close()

async def job_database_cleanup():
    """Job 7: Purges transient logs older than retention period (30 days)."""
    db: Session = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=30)
        deleted = db.query(ApiLog).filter(ApiLog.timestamp < cutoff).delete()
        db.commit()
        if deleted > 0:
            logger.info(f"Purged {deleted} stale API log records.")
    except Exception as e:
        logger.error(f"Error in job_database_cleanup: {str(e)}")
    finally:
        db.close()

async def job_data_sources_health_check():
    """Job 8: Monitors latency and health status of all integrated sources."""
    db: Session = SessionLocal()
    try:
        sources = db.query(DataSource).all()
        for src in sources:
            # If last successful sync is older than 6 hours, mark STALE
            if src.last_successful_sync:
                diff_hours = (datetime.utcnow() - src.last_successful_sync).total_seconds() / 3600.0
                if diff_hours > 6 and src.status == "ONLINE":
                    src.status = "STALE"
            elif not src.last_successful_sync and src.status == "ONLINE":
                src.status = "RECENT"
        db.commit()
    except Exception as e:
        logger.error(f"Error in job_data_sources_health_check: {str(e)}")
    finally:
        db.close()

def start_scheduler():
    """Starts all 8 scheduled jobs."""
    scheduler.add_job(job_imd_weather_sync, "interval", minutes=settings.IMD_WEATHER_INTERVAL, id="imd_weather_sync", replace_existing=True)
    scheduler.add_job(job_imd_rainfall_sync, "interval", minutes=settings.RAINFALL_INTERVAL, id="imd_rainfall_sync", replace_existing=True)
    scheduler.add_job(job_imd_warnings_sync, "interval", minutes=settings.WARNING_INTERVAL, id="imd_warnings_sync", replace_existing=True)
    scheduler.add_job(job_sensor_telemetry_sync, "interval", minutes=settings.SENSOR_INTERVAL, id="sensor_telemetry_sync", replace_existing=True)
    scheduler.add_job(job_ndma_alerts_sync, "interval", minutes=settings.GOV_ALERT_INTERVAL, id="ndma_alerts_sync", replace_existing=True)
    scheduler.add_job(job_risk_prediction_engine, "interval", minutes=settings.RISK_PREDICTION_INTERVAL, id="risk_prediction_engine", replace_existing=True)
    scheduler.add_job(job_data_sources_health_check, "interval", minutes=settings.DATA_SOURCE_HEALTH_INTERVAL, id="data_sources_health_check", replace_existing=True)
    scheduler.add_job(job_database_cleanup, "interval", hours=24, id="database_cleanup", replace_existing=True)

    scheduler.start()
    logger.info("APScheduler initialized with all 8 real-time disaster ingestion jobs.")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")
