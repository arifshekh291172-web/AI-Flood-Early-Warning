import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models.core import (
    Role, User, State, District, Location,
    WeatherObservation, RainfallObservation, RiskPrediction,
    GovernmentAlert, RoadSegment, DataSource
)

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def test_db():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_state_and_district_creation(test_db):
    state = State(id="AS", name="Assam", capital="Dispur", centroid_lat=26.20, centroid_lon=92.93)
    test_db.add(state)
    test_db.commit()

    district = District(id="AS_KAMRUP", state_id="AS", name="Kamrup", centroid_lat=26.14, centroid_lon=91.73)
    test_db.add(district)
    test_db.commit()

    fetched = test_db.query(District).filter(District.id == "AS_KAMRUP").first()
    assert fetched is not None
    assert fetched.name == "Kamrup"
    assert fetched.state.name == "Assam"

def test_location_and_risk_prediction(test_db):
    state = State(id="ML", name="Meghalaya", centroid_lat=25.46, centroid_lon=91.36)
    district = District(id="ML_EAST_KHASI", state_id="ML", name="East Khasi Hills", centroid_lat=25.57, centroid_lon=91.89)
    test_db.add(state)
    test_db.add(district)
    test_db.commit()

    loc = Location(
        id="LOC_SOHRA",
        name="Sohra Cliff",
        district_id="ML_EAST_KHASI",
        state_id="ML",
        latitude=25.289,
        longitude=91.724,
        elevation_m=1430.0,
        slope_deg=46.0
    )
    test_db.add(loc)
    test_db.commit()

    pred = RiskPrediction(
        location_id="LOC_SOHRA",
        prediction_time=loc.created_at,
        risk_probability=0.88,
        risk_class="CRITICAL",
        model_version="v1.0",
        feature_snapshot={"rainfall_24h_mm": 180.0, "slope_deg": 46.0}
    )
    test_db.add(pred)
    test_db.commit()

    fetched_pred = test_db.query(RiskPrediction).filter(RiskPrediction.location_id == "LOC_SOHRA").first()
    assert fetched_pred.risk_class == "CRITICAL"
    assert fetched_pred.risk_probability == 0.88
