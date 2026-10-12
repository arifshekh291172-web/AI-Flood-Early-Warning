from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from backend.app.database import get_db
from backend.app.models.core import DataSource
from backend.app.utils.provenance import to_ist_string

router = APIRouter(prefix="/api/data-sources", tags=["Data Sources & Provenance"])

@router.get("/status")
def get_data_sources_status(db: Session = Depends(get_db)):
    """
    Returns real-time status, synchronization timestamps, latency, and provenance
    for all official government integrations and sensor networks.
    """
    sources = db.query(DataSource).all()
    results = []

    for s in sources:
        results.append({
            "id": s.id,
            "name": s.name,
            "category": s.category,
            "endpoint_url": s.endpoint_url,
            "status": s.status, # ONLINE, RECENT, STALE, OFFLINE
            "last_successful_sync_ist": to_ist_string(s.last_successful_sync),
            "last_attempt_ist": to_ist_string(s.last_attempt),
            "latency_ms": round(s.latency_ms, 1),
            "consecutive_failures": s.consecutive_failures,
            "records_synced_today": s.records_synced_today or 0,
            "last_error_message": s.last_error_message
        })

    return {
        "count": len(results),
        "data_sources": results
    }
