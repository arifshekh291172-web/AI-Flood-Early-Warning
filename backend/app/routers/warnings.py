from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from backend.app.database import get_db
from backend.app.models.core import GovernmentAlert
from backend.app.utils.provenance import to_ist_string

router = APIRouter(prefix="/api/warnings", tags=["Official Government Warnings"])

@router.get("")
def get_official_government_warnings(
    state_id: Optional[str] = Query(None, description="State filter (e.g. AS, AR, ML)"),
    status: Optional[str] = Query("ACTIVE", description="ACTIVE, EXPIRED, or ALL"),
    db: Session = Depends(get_db)
):
    """
    Returns official, verified government disaster alerts and meteorological warnings
    originating exclusively from IMD and NDMA/SACHET platforms.
    """
    query = db.query(GovernmentAlert)
    if state_id:
        query = query.filter(GovernmentAlert.state_id == state_id)
    if status != "ALL":
        query = query.filter(GovernmentAlert.status == status)

    warnings = query.order_by(GovernmentAlert.issued_at.desc()).all()

    items = [
        {
            "id": w.id,
            "category": "OFFICIAL_GOVERNMENT_WARNING",
            "alert_source": w.alert_source,
            "official_alert_id": w.official_alert_id,
            "alert_type": w.alert_type,
            "severity": w.severity,
            "headline": w.headline,
            "description": w.description,
            "state_id": w.state_id,
            "district_id": w.district_id,
            "issued_at_ist": to_ist_string(w.issued_at),
            "valid_until_ist": to_ist_string(w.valid_until),
            "official_source_url": w.official_source_url,
            "status": w.status
        } for w in warnings
    ]

    return {
        "count": len(items),
        "source_disclaimer": "All bulletins in this feed are authoritative publications of Government of India agencies (IMD/NDMA). They are distinct from NE-SHIELD ML algorithmic predictions.",
        "warnings": items
    }
