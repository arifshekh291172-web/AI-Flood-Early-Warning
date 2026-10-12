from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import uuid

from backend.app.database import get_db
from backend.app.models.core import FieldReport, CitizenReport, User, AuditLog
from backend.app.schemas.reports import FieldReportCreate, FieldReportItem
from backend.app.utils.security import get_current_user, require_role
from backend.app.utils.provenance import to_ist_string

router = APIRouter(prefix="/api/field", tags=["Field Officer Ground Operations"])

@router.get("/incidents")
def get_field_incidents(
    current_user: User = Depends(require_role(["ADMIN", "FIELD_OFFICER", "DISTRICT_AUTHORITY"])),
    db: Session = Depends(get_db)
):
    """
    Returns field verified incidents and pending citizen reports requiring ground inspection.
    """
    field_reports = db.query(FieldReport).order_by(FieldReport.created_at.desc()).limit(50).all()
    pending_citizen = db.query(CitizenReport).filter(
        CitizenReport.status.in_(["SUBMITTED", "UNDER_REVIEW"])
    ).order_by(CitizenReport.submitted_at.desc()).limit(30).all()

    return {
        "officer": {
            "name": current_user.full_name,
            "department": current_user.department,
            "jurisdiction": current_user.state_jurisdiction or "All NER"
        },
        "pending_ground_checks": [
            {
                "id": c.id,
                "report_number": c.report_number,
                "type": c.report_type,
                "description": c.description,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "landmark": c.landmark,
                "submitted_at_ist": to_ist_string(c.submitted_at)
            } for c in pending_citizen
        ],
        "verified_field_reports": [
            {
                "id": f.id,
                "report_number": f.report_number,
                "incident_type": f.incident_type,
                "movement_active": f.movement_active,
                "road_blocked": f.road_blocked,
                "immediate_danger": f.immediate_danger,
                "latitude": f.latitude,
                "longitude": f.longitude,
                "sync_status": f.sync_status,
                "created_at_ist": to_ist_string(f.created_at)
            } for f in field_reports
        ]
    }

@router.post("/sync")
def sync_offline_reports(
    reports: List[Dict[str, Any]] = Body(...),
    current_user: User = Depends(require_role(["ADMIN", "FIELD_OFFICER"])),
    db: Session = Depends(get_db)
):
    """
    Handles offline-first field synchronization.
    Accepts encrypted/batched reports accumulated in IndexedDB when network was down.
    """
    synced_count = 0
    synced_ids = []

    for r in reports:
        client_id = r.get("offline_client_id") or str(uuid.uuid4())
        
        # Check if already synced by offline_client_id
        existing = db.query(FieldReport).filter(FieldReport.offline_client_id == client_id).first()
        if existing:
            synced_ids.append(existing.report_number)
            continue

        report_num = f"FR-{datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

        fr = FieldReport(
            report_number=report_num,
            officer_id=current_user.id,
            citizen_report_id=r.get("citizen_report_id"),
            location_id=r.get("location_id"),
            latitude=float(r.get("latitude", 0.0)),
            longitude=float(r.get("longitude", 0.0)),
            incident_type=r.get("incident_type", "Landslide"),
            landslide_dimensions=r.get("landslide_dimensions"),
            movement_active=bool(r.get("movement_active", False)),
            estimated_volume_m3=float(r.get("estimated_volume_m3") or 0.0) if r.get("estimated_volume_m3") else None,
            road_blocked=bool(r.get("road_blocked", False)),
            immediate_danger=r.get("immediate_danger", "LOW"),
            actions_taken=r.get("actions_taken"),
            media_urls=r.get("media_urls", []),
            sync_status="SYNCED",
            offline_client_id=client_id,
            created_at=datetime.utcnow(),
            synced_at=datetime.utcnow()
        )
        db.add(fr)

        # If citizen report referenced, update its status
        if r.get("citizen_report_id"):
            cit = db.query(CitizenReport).filter(CitizenReport.id == r.get("citizen_report_id")).first()
            if cit:
                cit.status = "VERIFIED"
                cit.verification_notes = f"Ground verified by Officer {current_user.full_name}: {r.get('actions_taken', '')}"
                cit.updated_at = datetime.utcnow()

        synced_count += 1
        synced_ids.append(report_num)

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="FIELD_OFFLINE_SYNC_COMPLETED",
        resource_type="field_reports",
        details={"synced_records": synced_count, "report_numbers": synced_ids},
        result_status="SUCCESS"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "synced_count": synced_count,
        "synced_report_numbers": synced_ids,
        "timestamp_ist": to_ist_string(datetime.utcnow())
    }
