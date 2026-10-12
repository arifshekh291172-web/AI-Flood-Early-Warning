import os
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from backend.app.database import get_db
from backend.app.models.core import CitizenReport, MediaFile, AuditLog, User
from backend.app.schemas.reports import CitizenReportItem
from backend.app.utils.security import get_current_user_optional, get_current_user, require_role
from backend.app.utils.provenance import to_ist_string, compute_payload_hash

router = APIRouter(prefix="/api/reports", tags=["Citizen Reporting"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("", response_model=List[CitizenReportItem])
def get_reports(
    status: Optional[str] = Query(None, description="SUBMITTED, UNDER_REVIEW, VERIFIED, REJECTED, RESOLVED"),
    report_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(CitizenReport)
    if status:
        query = query.filter(CitizenReport.status == status)
    if report_type:
        query = query.filter(CitizenReport.report_type == report_type)

    reports = query.order_by(CitizenReport.submitted_at.desc()).limit(100).all()

    return [
        CitizenReportItem(
            id=r.id,
            report_number=r.report_number,
            reporter_name=r.reporter_name,
            reporter_phone=r.reporter_phone,
            report_type=r.report_type,
            description=r.description,
            latitude=r.latitude,
            longitude=r.longitude,
            landmark=r.landmark,
            district=r.district,
            state=r.state,
            media_urls=r.media_urls or [],
            status=r.status,
            verification_notes=r.verification_notes,
            submitted_at_ist=to_ist_string(r.submitted_at),
            updated_at_ist=to_ist_string(r.updated_at)
        ) for r in reports
    ]

@router.post("")
async def submit_citizen_report(
    reporter_name: str = Form(...),
    reporter_phone: str = Form(...),
    report_type: str = Form(...), # Landslide, Road Blockage, Crack, Rockfall, Flooding, Infrastructure Damage, Other
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    landmark: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Submits a geo-tagged disaster report. Generates a unique traceable Report ID.
    Supports photo/video upload.
    """
    report_num = f"CR-{datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
    media_urls = []

    if photo and photo.filename:
        # File type validation
        ext = os.path.splitext(photo.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".mp4"]:
            raise HTTPException(status_code=400, detail="Invalid media type. Allowed: jpg, png, webp, mp4")
        
        file_id = str(uuid.uuid4())
        saved_filename = f"{file_id}{ext}"
        saved_path = os.path.join(UPLOAD_DIR, saved_filename)
        
        content = await photo.read()
        if len(content) > 15 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 15MB")
        
        with open(saved_path, "wb") as f:
            f.write(content)

        media_url = f"/static/uploads/{saved_filename}"
        media_urls.append(media_url)

        # Record in media_files table
        mf = MediaFile(
            filename=photo.filename,
            file_path=saved_path,
            file_type=photo.content_type or "image/jpeg",
            file_size_bytes=len(content),
            sha256_hash=compute_payload_hash(content),
            uploaded_by=current_user.id if current_user else None,
            related_entity_type="citizen_report",
            related_entity_id=report_num
        )
        db.add(mf)

    rep = CitizenReport(
        report_number=report_num,
        user_id=current_user.id if current_user else None,
        reporter_name=reporter_name,
        reporter_phone=reporter_phone,
        report_type=report_type,
        description=description,
        latitude=latitude,
        longitude=longitude,
        landmark=landmark,
        district=district,
        state=state,
        media_urls=media_urls,
        status="SUBMITTED"
    )
    db.add(rep)

    audit = AuditLog(
        user_id=current_user.id if current_user else None,
        user_email=current_user.email if current_user else "anonymous_citizen",
        action="CITIZEN_REPORT_SUBMITTED",
        resource_type="citizen_report",
        resource_id=report_num,
        result_status="SUCCESS"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": "Report successfully registered and queued for district authority verification.",
        "report_number": report_num,
        "status": "SUBMITTED",
        "timestamp_ist": to_ist_string(datetime.utcnow())
    }

@router.patch("/{report_id}")
def update_report_status(
    report_id: str,
    status: str = Form(...), # UNDER_REVIEW, VERIFIED, REJECTED, RESOLVED
    verification_notes: Optional[str] = Form(None),
    current_user: User = Depends(require_role(["ADMIN", "DISTRICT_AUTHORITY", "FIELD_OFFICER"])),
    db: Session = Depends(get_db)
):
    rep = db.query(CitizenReport).filter(
        (CitizenReport.id == report_id) | (CitizenReport.report_number == report_id)
    ).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found")

    rep.status = status
    if verification_notes:
        rep.verification_notes = verification_notes
    rep.verified_by_user_id = current_user.id
    rep.updated_at = datetime.utcnow()

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="REPORT_STATUS_UPDATED",
        resource_type="citizen_report",
        resource_id=rep.report_number,
        details={"new_status": status, "notes": verification_notes},
        result_status="SUCCESS"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "report_number": rep.report_number,
        "new_status": rep.status,
        "verified_by": current_user.full_name
    }
