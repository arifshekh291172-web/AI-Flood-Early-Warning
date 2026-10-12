import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.alerts.rules import evaluate_and_dispatch_risk_alerts
from backend.app.models.core import Notification

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def alert_db():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_critical_risk_alert_dispatch(alert_db):
    pred = {
        "location_id": "LOC_HAFLONG_HILL",
        "location_name": "Haflong Hill Section KM 118",
        "risk_probability": 0.91,
        "risk_class": "CRITICAL",
        "thresholds_exceeded": ["Extreme 24h Rainfall (>115.6mm)", "Steep Escarpment Angle (41.5°)"]
    }
    notifs = evaluate_and_dispatch_risk_alerts(pred, alert_db)
    assert len(notifs) >= 2
    assert any(n.severity == "CRITICAL" for n in notifs)

    db_notifs = alert_db.query(Notification).filter(Notification.entity_id == "LOC_HAFLONG_HILL").all()
    assert len(db_notifs) >= 2

def test_low_risk_no_alert_dispatch(alert_db):
    pred = {
        "location_id": "LOC_AMBASSA",
        "location_name": "Ambassa Ridge Sector",
        "risk_probability": 0.18,
        "risk_class": "LOW",
        "thresholds_exceeded": []
    }
    notifs = evaluate_and_dispatch_risk_alerts(pred, alert_db)
    assert len(notifs) == 0
