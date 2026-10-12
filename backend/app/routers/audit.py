from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from backend.app.database import get_db
from backend.app.models.core import AuditLog, User
from backend.app.utils.security import require_role
from backend.app.utils.provenance import to_ist_string

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Trail"])

@router.get("")
def get_audit_logs(
    action: Optional[str] = Query(None),
    limit: int = Query(50, ge=5, le=200),
    current_user: User = Depends(require_role(["ADMIN", "DISTRICT_AUTHORITY"])),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)

    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

    return [
        {
            "id": l.id,
            "action": l.action,
            "user_email": l.user_email or "SYSTEM",
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "details": l.details,
            "result_status": l.result_status,
            "timestamp_ist": to_ist_string(l.timestamp)
        } for l in logs
    ]
