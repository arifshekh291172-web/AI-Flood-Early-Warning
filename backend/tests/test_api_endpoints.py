import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["HEALTHY", "DEGRADED"]
    assert "components" in data
    assert "database" in data["components"]
    assert "ml_engine" in data["components"]

def test_dashboard_summary():
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "active_risk_zones" in data["kpis"]
    assert "top_critical_locations" in data

def test_weather_current():
    res = client.get("/api/weather/current")
    assert res.status_code == 200
    data = res.json()
    assert "observations" in data
    if data["observations"]:
        obs = data["observations"][0]
        assert "provenance" in obs
        assert obs["provenance"]["source_name"] in ["IMD", "SATELLITE_LIVE", "AWS"]

def test_rainfall_latest():
    res = client.get("/api/rainfall/latest")
    assert res.status_code == 200
    data = res.json()
    assert "observations" in data
    assert "analytics" in data

def test_warnings_official():
    res = client.get("/api/warnings")
    assert res.status_code == 200
    data = res.json()
    assert "warnings" in data
    if data["warnings"]:
        w = data["warnings"][0]
        assert w["category"] == "OFFICIAL_GOVERNMENT_WARNING"

def test_risk_current():
    res = client.get("/api/risk/current")
    assert res.status_code == 200
    data = res.json()
    assert "predictions" in data
    assert "active_model_version" in data

def test_map_layers():
    res = client.get("/api/map/layers")
    assert res.status_code == 200
    data = res.json()
    assert "hazard_locations" in data
    assert "risk_zones" in data
    assert "road_network" in data

def test_roads():
    res = client.get("/api/roads")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:
        assert data[0]["source_attribution"] in ["FIELD_VERIFIED", "GOVERNMENT_SOURCE"]

def test_model_status():
    res = client.get("/api/model/status")
    assert res.status_code == 200
    data = res.json()
    assert "active_version" in data
    assert "metrics" in data
    assert "confusion_matrix" in data["metrics"]

def test_data_sources_status():
    res = client.get("/api/data-sources/status")
    assert res.status_code == 200
    data = res.json()
    assert "data_sources" in data
    assert len(data["data_sources"]) > 0

def test_auth_login():
    res = client.post("/api/auth/login", json={
        "email": "admin@ne-shield.gov.in",
        "password": "Admin@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "ADMIN"

def test_satellite_latest():
    res = client.get("/api/satellite/latest")
    assert res.status_code == 200
    data = res.json()
    assert "satellite_telemetry" in data
    assert data["count"] > 0

def test_satellite_predict():
    res = client.post("/api/satellite/predict")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "predictions" in data
    assert len(data["predictions"]) > 0
    assert "risk_probability" in data["predictions"][0]

