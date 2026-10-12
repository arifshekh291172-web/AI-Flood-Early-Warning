import pytest
from backend.app.integrations.imd.schemas import IMDCityForecastItem, IMDDistrictRainfallItem
from backend.app.utils.provenance import compute_payload_hash, evaluate_provenance_status
from datetime import datetime, timedelta

def test_imd_city_forecast_schema_parsing():
    raw_item = {
        "Date": "2026-09-23",
        "Station_Code": "42182",
        "Station_Name": "Guwahati Airport",
        "Today_Max_temp": "31.2",
        "Today_Min_temp": "24.6",
        "Past_24_hrs_Rainfall": "14.2",
        "Relative_Humidity_at_0830": "84",
        "Todays_Forecast": "Generally cloudy sky with a few spells of rain or thundershowers"
    }
    parsed = IMDCityForecastItem(**raw_item)
    assert parsed.Station_Code == "42182"
    assert parsed.Station_Name == "Guwahati Airport"
    assert parsed.Todays_Forecast == raw_item["Todays_Forecast"]

def test_imd_rainfall_schema_parsing():
    raw_rf = {
        "State_Name": "Assam",
        "District_Name": "Dima Hasao",
        "Actual_Rainfall_mm": 78.4,
        "Normal_Rainfall_mm": 12.0,
        "Departure_pct": 553.3,
        "Date": "2026-09-23"
    }
    parsed = IMDDistrictRainfallItem(**raw_rf)
    assert parsed.District_Name == "Dima Hasao"
    assert parsed.Actual_Rainfall_mm == 78.4

def test_payload_hash_provenance():
    payload = {"station": "Cherrapunji", "rain_mm": 182.4}
    h1 = compute_payload_hash(payload)
    h2 = compute_payload_hash(payload)
    assert len(h1) == 64
    assert h1 == h2

def test_provenance_status_staleness():
    now = datetime.utcnow()
    live_status, _ = evaluate_provenance_status(now - timedelta(minutes=5))
    assert live_status == "LIVE"

    recent_status, _ = evaluate_provenance_status(now - timedelta(minutes=45))
    assert recent_status == "RECENT"

    stale_status, _ = evaluate_provenance_status(now - timedelta(hours=3))
    assert stale_status == "STALE"

    offline_status, _ = evaluate_provenance_status(now - timedelta(days=2))
    assert offline_status == "OFFLINE"
