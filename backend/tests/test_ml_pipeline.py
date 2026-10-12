import pytest
import numpy as np
from backend.app.ml.feature_engineering import extract_feature_vector, FEATURE_COLUMNS, feature_dict_to_array
from backend.app.ml.predict import classify_risk, check_exceeded_thresholds
from backend.app.ml.evaluation import calculate_model_metrics

def test_feature_vector_extraction():
    weather = {"temperature_c": 26.5, "humidity_pct": 85.0}
    rainfall = {"rainfall_1h_mm": 20.0, "rainfall_24h_mm": 130.0}
    sensor = {"soil_moisture_pct": 82.0, "pore_pressure_kpa": 65.0}
    terrain = {"slope_deg": 42.0, "elevation_m": 1200.0, "lithology": "Metamorphic"}
    warning = {"severity": "Orange Alert"}

    features = extract_feature_vector(weather, rainfall, sensor, terrain, warning, historical_count=4)
    for col in FEATURE_COLUMNS:
        assert col in features
        assert isinstance(features[col], (int, float))

    arr = feature_dict_to_array(features)
    assert arr.shape == (1, len(FEATURE_COLUMNS))

def test_risk_classification():
    assert classify_risk(0.15) == "LOW"
    assert classify_risk(0.45) == "MODERATE"
    assert classify_risk(0.72) == "HIGH"
    assert classify_risk(0.92) == "CRITICAL"

def test_exceeded_thresholds():
    features = {
        "rainfall_24h_mm": 125.0,
        "rainfall_1h_mm": 30.0,
        "soil_moisture_pct": 88.0,
        "slope_deg": 41.0,
        "weather_warning_severity_code": 2.0
    }
    triggers = check_exceeded_thresholds(features)
    assert any("Extreme 24h Rainfall" in t for t in triggers)
    assert any("Cloudburst" in t for t in triggers)
    assert any("Steep Escarpment" in t for t in triggers)

def test_genuine_metrics_calculation():
    y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0])
    y_pred = np.array([0, 0, 1, 1, 0, 0, 1, 0])
    y_prob = np.array([0.1, 0.2, 0.8, 0.9, 0.4, 0.1, 0.85, 0.3])

    metrics = calculate_model_metrics(y_true, y_pred, y_prob)
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["accuracy"] == 0.875
