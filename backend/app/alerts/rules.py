from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.core import Notification, AuditLog, RiskPrediction, Location
from backend.app.utils.logger import logger

def evaluate_and_dispatch_risk_alerts(
    prediction_result: Dict[str, Any],
    db: Session
) -> List[Notification]:
    """
    Evaluates ML predictions and dispatches role-based notifications
    if risk reaches HIGH or CRITICAL severity.
    """
    risk_class = prediction_result.get("risk_class")
    prob = prediction_result.get("risk_probability", 0.0)
    loc_name = prediction_result.get("location_name")
    loc_id = prediction_result.get("location_id")
    thresholds = prediction_result.get("thresholds_exceeded", [])

    created_notifications = []

    if risk_class in ["CRITICAL", "HIGH"]:
        title = f"NE-SHIELD {risk_class} LANDSLIDE RISK: {loc_name}"
        msg = (
            f"AI Landslide Model evaluated {prob*100:.1f}% failure probability at {loc_name}. "
            f"Triggers: {', '.join(thresholds) if thresholds else 'Antecedent saturation & terrain threshold breached'}."
        )

        # 1. Dashboard Notification
        notif = Notification(
            channel="DASHBOARD",
            title=title,
            message=msg,
            severity="CRITICAL" if risk_class == "CRITICAL" else "WARNING",
            entity_type="risk_prediction",
            entity_id=loc_id,
            sent_at=datetime.utcnow()
        )
        db.add(notif)
        created_notifications.append(notif)

        # 2. Browser Push notification record
        notif_push = Notification(
            channel="BROWSER_PUSH",
            title=title,
            message=msg,
            severity="CRITICAL" if risk_class == "CRITICAL" else "WARNING",
            entity_type="risk_prediction",
            entity_id=loc_id,
            sent_at=datetime.utcnow()
        )
        db.add(notif_push)
        created_notifications.append(notif_push)

        # Audit
        audit = AuditLog(
            action="ALERT_TRIGGERED",
            resource_type="risk_prediction",
            resource_id=loc_id,
            details={"risk_class": risk_class, "probability": prob, "triggers": thresholds},
            result_status="SUCCESS"
        )
        db.add(audit)
        db.commit()

        logger.warning(f"ALERT DISPATCHED: {title}")

    return created_notifications
