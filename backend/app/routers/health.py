from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from backend.app.database import get_db
from backend.app.models.core import DataSource
from backend.app.ml.model_loader import model_registry
from backend.app.services.scheduler import scheduler
from backend.app.config import settings

router = APIRouter(prefix="/api", tags=["System Health"])

@router.get("/health")
def get_health_status(db: Session = Depends(get_db)):
    """
    Returns real-time health and connectivity status of all backend subsystems,
    databases, ML engines, and government API connections.
    """
    # 1. Database check
    db_status = "ONLINE"
    db_latency_ms = 0.0
    try:
        t0 = datetime.utcnow()
        db.execute(text("SELECT 1"))
        db_latency_ms = round((datetime.utcnow() - t0).total_seconds() * 1000.0, 2)
    except Exception as e:
        db_status = f"OFFLINE ({str(e)})"

    # 2. ML Engine check
    meta = model_registry.get_metadata()
    ml_status = "ONLINE" if meta else "UNINITIALIZED"

    # 3. Government integrations check
    sources = db.query(DataSource).all()
    source_statuses = {
        s.id: {
            "name": s.name,
            "status": s.status,
            "latency_ms": s.latency_ms,
            "last_successful_sync": s.last_successful_sync.isoformat() + "Z" if s.last_successful_sync else None
        } for s in sources
    }

    return {
        "status": "HEALTHY" if db_status == "ONLINE" else "DEGRADED",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "operational_mode": settings.OPERATIONAL_MODE,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": {
            "database": {
                "status": db_status,
                "latency_ms": db_latency_ms
            },
            "ml_engine": {
                "status": ml_status,
                "active_model_version": meta.get("version_tag", "N/A"),
                "accuracy": meta.get("metrics", {}).get("accuracy")
            },
            "scheduler": {
                "status": "RUNNING" if scheduler.running else "STOPPED",
                "jobs_count": len(scheduler.get_jobs()) if scheduler.running else 0
            },
            "data_sources": source_statuses
        }
    }
