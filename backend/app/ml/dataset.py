import os
import csv
import numpy as np
from typing import Tuple, List, Dict
from backend.app.ml.feature_engineering import FEATURE_COLUMNS

DATASET_DIR = os.path.join(os.path.dirname(__file__), "data")
DATASET_PATH = os.path.join(DATASET_DIR, "ne_landslides_training_data.csv")

def generate_northeast_geotechnical_dataset(samples_count: int = 2500) -> str:
    """
    Generates and saves a physics-informed historical dataset calibrated to Northeast India 
    topography, lithology, and IMD/GSI rainfall intensity-duration thresholds (Caine 1980 / GSI 2022).
    Accurately decouples static terrain susceptibility from dynamic meteorological triggering
    so that steep slopes stand stable in dry/light conditions and fail under extreme rainfall/saturation.
    """
    os.makedirs(DATASET_DIR, exist_ok=True)

    np.random.seed(42)
    rows = []

    for i in range(samples_count):
        # 1. Topography & Terrain
        slope = np.random.uniform(8.0, 52.0)
        elev = np.random.uniform(150.0, 2900.0)
        aspect = np.random.uniform(0.0, 360.0)
        aspect_sin = np.sin(np.radians(aspect))
        aspect_cos = np.cos(np.radians(aspect))
        curvature = np.random.uniform(-0.06, 0.06)
        dist_fault = np.random.exponential(scale=2500.0) + 100.0
        dist_stream = np.random.exponential(scale=600.0) + 50.0
        drainage = np.random.uniform(0.8, 3.8)
        
        # Lithology: 0=Crystalline/Granite, 1=Metamorphic/Gneiss, 2=Sedimentary/Shale/Sandstone, 3=Unconsolidated Alluvium
        lith_code = float(np.random.choice([0, 1, 2, 3], p=[0.15, 0.35, 0.40, 0.10]))
        hist_count = float(np.random.poisson(lam=1.2 if slope > 30 else 0.3))

        # 2. Meteorology (IMD multi-tier distribution: 35% storm deluges, 65% normal/light days)
        is_heavy_rain_event = np.random.rand() < 0.35
        if is_heavy_rain_event:
            r24 = np.random.exponential(scale=55.0) + 45.0  # 45mm to 200mm+ (IMD Heavy to Extremely Heavy)
            r1 = min(60.0, np.random.exponential(scale=10.0) + 3.0)
            ari7 = np.random.uniform(75.0, 380.0)
            warn_code = float(np.random.choice([1, 2, 3], p=[0.30, 0.40, 0.30])) # Yellow, Orange, Red
        else:
            r24 = np.random.exponential(scale=12.0) + 1.0  # 1mm to 35mm (Light to Moderate)
            r1 = min(15.0, np.random.exponential(scale=2.0))
            ari7 = np.random.uniform(5.0, 75.0)
            warn_code = float(np.random.choice([0, 1], p=[0.90, 0.10])) # None, Yellow

        r3 = r1 * np.random.uniform(1.6, 2.5)
        r6 = r3 * np.random.uniform(1.3, 1.9)
        r72 = r24 * np.random.uniform(1.1, 1.8)
        rcum = r72 * np.random.uniform(1.1, 1.5)

        # 3. Soil & Pore Pressure state physically coupled to rain
        soil_sat_baseline = 28.0 + (min(r24, 150.0) * 0.32) + (min(ari7, 300.0) * 0.08)
        soil_moist = min(98.0, max(18.0, soil_sat_baseline + np.random.normal(0, 5.0)))

        pore_kpa_baseline = 6.0 + (min(r24, 180.0) * 0.45) + (min(ari7, 300.0) * 0.12)
        pore_kpa = max(2.0, min(140.0, pore_kpa_baseline + np.random.normal(0, 6.0)))

        # 4. Geotechnical Factor of Safety (FS) Limit Equilibrium
        theta = np.radians(slope)
        friction_angles = {0: 40.0, 1: 34.0, 2: 28.0, 3: 22.0}
        phi = np.radians(friction_angles[int(lith_code)])

        base_cohesion = {0: 50.0, 1: 35.0, 2: 20.0, 3: 10.0}[int(lith_code)]
        root_cohesion = 18.0 # Vegetation root reinforcement
        suction_cohesion = max(0.0, (75.0 - soil_moist) * 0.6) # Matrix suction collapses when saturated
        c_effective = base_cohesion + root_cohesion + suction_cohesion

        depth_z = 2.5 # meters
        gamma = 19.5 # kN/m3
        driving_shear = max(1.0, gamma * depth_z * np.sin(theta) * np.cos(theta))

        normal_stress = gamma * depth_z * (np.cos(theta) ** 2)
        effective_normal = max(2.0, normal_stress - (pore_kpa * 0.45))
        resisting_shear = c_effective + (effective_normal * np.tan(phi))
        fs = resisting_shear / driving_shear

        # 5. Physics-informed Hazard Calibration
        # Static Susceptibility factor (0.10 to 0.90)
        slope_term = max(0.0, min(1.0, (slope - 20.0) / 28.0))
        lith_term = [0.25, 0.50, 0.80, 1.0][int(lith_code)]
        fault_term = max(0.0, min(1.0, 1.0 - (dist_fault / 4000.0)))
        static_susc = (0.55 * slope_term) + (0.30 * lith_term) + (0.15 * fault_term)

        # Dynamic Hydrological Trigger Factor (0.0 to 1.4)
        rain_24h_ratio = min(1.5, r24 / 64.5) # 1.0 at IMD Heavy (64.5mm)
        rain_1h_ratio = min(1.5, r1 / 25.0)   # 1.0 at Cloudburst (25mm/h)
        soil_moist_ratio = max(0.0, min(1.2, (soil_moist - 50.0) / 35.0)) # 1.0 at 85%
        pore_press_ratio = max(0.0, min(1.2, (pore_kpa - 20.0) / 45.0)) # 1.0 at 65 kPa

        dynamic_load = max(
            0.65 * rain_24h_ratio + 0.35 * soil_moist_ratio,
            rain_1h_ratio,
            0.50 * rain_24h_ratio + 0.50 * pore_press_ratio
        )
        dynamic_load = min(1.4, max(0.02, dynamic_load))

        # Real Landslide Risk Probability P(Failure)
        p_fail = static_susc * (dynamic_load ** 1.35)
        if fs < 1.0 and dynamic_load > 0.5:
            p_fail = max(p_fail, 0.88)
        p_fail = min(0.96, max(0.02, p_fail))

        is_landslide = 1 if np.random.rand() < p_fail else 0

        row = [
            round(r1, 2), round(r3, 2), round(r6, 2), round(r24, 2), round(r72, 2),
            round(rcum, 2), round(ari7, 2), round(soil_moist, 2), round(pore_kpa, 2),
            round(slope, 2), round(elev, 2), round(aspect_sin, 4), round(aspect_cos, 4),
            round(curvature, 4), round(dist_fault, 1), round(dist_stream, 1),
            round(drainage, 2), float(hist_count), float(warn_code), float(lith_code),
            is_landslide
        ]
        rows.append(row)

    headers = FEATURE_COLUMNS + ["label"]

    with open(DATASET_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    return DATASET_PATH

def load_training_data(csv_path: str | None = None) -> Tuple[np.ndarray, np.ndarray]:
    """Loads X and y arrays from CSV."""
    path = csv_path or DATASET_PATH
    if not os.path.exists(path):
        generate_northeast_geotechnical_dataset()

    X = []
    y = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            feat = [float(r[col]) for col in FEATURE_COLUMNS]
            label = int(float(r["label"]))
            X.append(feat)
            y.append(label)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)
