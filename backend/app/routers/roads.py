from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from backend.app.database import get_db
from backend.app.models.core import RoadSegment, RoadStatus, User, AuditLog
from backend.app.schemas.reports import RoadSegmentItem, RoadStatusUpdate
from backend.app.utils.security import get_current_user, require_role
from backend.app.utils.provenance import to_ist_string

router = APIRouter(prefix="/api/roads", tags=["Road Connectivity Network"])

@router.get("", response_model=List[RoadSegmentItem])
def get_road_segments(
    status: Optional[str] = None,
    state_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns monitored highway and mountain road connectivity states.
    Clearly labels source as 'Field Verified' or 'Government Source'.
    """
    query = db.query(RoadSegment)
    if state_id:
        query = query.filter(RoadSegment.state_id == state_id)

    segments = query.all()
    results = []

    for seg in segments:
        latest = db.query(RoadStatus).filter(
            RoadStatus.road_segment_id == seg.id
        ).order_by(RoadStatus.updated_at.desc()).first()

        current_st = latest.status if latest else "UNKNOWN"
        if status and current_st != status:
            continue

        results.append(RoadSegmentItem(
            id=seg.id,
            name=seg.name,
            highway_number=seg.highway_number,
            state_id=seg.state_id,
            district_id=seg.district_id,
            start_lat=seg.start_lat,
            start_lon=seg.start_lon,
            end_lat=seg.end_lat,
            end_lon=seg.end_lon,
            current_status=current_st,
            cause=latest.cause if latest else None,
            detour_advice=latest.detour_advice if latest else None,
            estimated_cleared_at_ist=to_ist_string(latest.estimated_cleared_at) if (latest and latest.estimated_cleared_at) else None,
            source_attribution=latest.source_attribution if latest else "GOVERNMENT_SOURCE",
            last_updated_ist=to_ist_string(latest.updated_at if latest else seg.created_at)
        ))

    return results

@router.patch("/{segment_id}")
def update_road_status(
    segment_id: str,
    update: RoadStatusUpdate,
    current_user: User = Depends(require_role(["ADMIN", "FIELD_OFFICER", "DISTRICT_AUTHORITY"])),
    db: Session = Depends(get_db)
):
    """
    Updates road connectivity status. Restricted to authorized field engineers and disaster authorities.
    """
    seg = db.query(RoadSegment).filter(RoadSegment.id == segment_id).first()
    if not seg:
        raise HTTPException(status_code=404, detail="Road segment not found")

    new_status = RoadStatus(
        road_segment_id=segment_id,
        status=update.status.upper(),
        cause=update.cause,
        detour_advice=update.detour_advice,
        estimated_cleared_at=update.estimated_cleared_at,
        updated_by_user_id=current_user.id,
        source_attribution=update.source_attribution or "FIELD_VERIFIED",
        updated_at=datetime.utcnow()
    )
    db.add(new_status)

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="ROAD_STATUS_UPDATED",
        resource_type="road_segment",
        resource_id=segment_id,
        details={"status": update.status, "cause": update.cause, "attribution": update.source_attribution},
        result_status="SUCCESS"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "segment_id": segment_id,
        "name": seg.name,
        "new_status": update.status.upper(),
        "attribution": new_status.source_attribution,
        "updated_at_ist": to_ist_string(datetime.utcnow())
    }
