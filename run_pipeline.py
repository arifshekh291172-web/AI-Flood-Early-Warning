#!/usr/bin/env python3
"""
NE-SHIELD: AI-Powered Landslide & Flood Early Warning System
Complete Operational Pipeline:
1. Train ML Model on Official Government Data (GSI & IMD Geotechnical Dataset)
2. Ingest Live Satellite Telemetry (ISRO Bhuvan & Earth Observation Assimilation)
3. Execute Real-Time AI Inference on Live Satellite Data
"""

import sys
import os
import argparse
import asyncio
from datetime import datetime

# Configure Windows console utf-8 encoding
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.database import SessionLocal, Base, engine
from backend.app.services.seed_data import seed_initial_data
from backend.app.ml.train import train_landslide_model
from backend.app.ml.model_loader import model_registry
from backend.app.integrations.satellite.service import satellite_service
from backend.app.ml.predict import run_satellite_predictions_all

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

def print_banner():
    print(f"\n{CYAN}{BOLD}" + "=" * 80)
    print("  NE-SHIELD: SATELLITE DISASTER INTELLIGENCE & AI PREDICTION ENGINE")
    print("  North Eastern Region Landslide & Flood Early Warning (GSI / IMD / ISRO)")
    print("=" * 80 + f"{RESET}\n")

def run_step_1_training(db):
    print(f"{YELLOW}{BOLD}[STEP 1/3] Training Machine Learning Model with Government Data...{RESET}")
    print(f"{DIM}Source: Geological Survey of India (GSI) & IMD Calibrated Geotechnical Thresholds{RESET}")
    
    clf, meta = train_landslide_model(
        algorithm="GradientBoostingClassifier",
        n_estimators=90,
        learning_rate=0.1,
        max_depth=4,
        db=db,
        user_email="pipeline-admin@ne-shield.gov.in"
    )
    model_registry.reload()

    m = meta["metrics"]
    print(f"\n{GREEN}{BOLD}[OK] Model Trained Successfully! Version: {meta['version_tag']}{RESET}")
    print(f"  • Algorithm:       {meta['algorithm']}")
    print(f"  • Dataset Size:    {meta['dataset_size']} verified geotechnical records")
    print(f"  • Accuracy:        {m['accuracy'] * 100:.2f}% (Held-out validation test set)")
    print(f"  • ROC-AUC:         {m['roc_auc']:.4f}")
    print(f"  • F1 Score:        {m['f1_score']:.4f} (Precision: {m['precision']:.4f}, Recall: {m['recall']:.4f})")
    
    print(f"\n  {BOLD}Top Geotechnical Drivers (Feature Importance):{RESET}")
    sorted_feats = sorted(m.get("feature_importances", {}).items(), key=lambda x: x[1], reverse=True)[:5]
    for feat, imp in sorted_feats:
        print(f"    - {feat:<32}: {imp * 100:>5.2f}%")
    print()
    return meta

async def run_step_2_satellite(db):
    print(f"{YELLOW}{BOLD}[STEP 2/3] Fetching Live Satellite Telemetry...{RESET}")
    print(f"{DIM}Connecting to ISRO Bhuvan WMS & Live Multi-Satellite Earth Observation feeds...{RESET}")

    result = await satellite_service.sync_live_satellite_telemetry(db)

    print(f"\n{GREEN}{BOLD}[OK] Live Satellite Data Ingested!{RESET}")
    print(f"  * ISRO Bhuvan WMS Status:  {result.get('bhuvan_wms_status', 'ONLINE')} ({result.get('bhuvan_latency_ms')} ms)")
    print(f"  * Locations Ingested:      {result.get('locations_synced', 0)}")
    print(f"  * Average Satellite RTT:   {result.get('satellite_average_latency_ms', 0.0)} ms")

    print(f"\n  {BOLD}{'Location':<34} {'Lat/Lon':<18} {'Sat Rain 24h':<14} {'Soil Moist %':<14} {'Cloud %':<8}{RESET}")
    print("  " + "-" * 90)
    for t in result.get("telemetry", []):
        coords = f"{t['latitude']:.2f}, {t['longitude']:.2f}"
        print(f"  {t['location_name'][:32]:<34} {coords:<18} {t['rainfall_24h_mm']:>6.1f} mm       {t['soil_moisture_pct']:>6.1f}%       {t['cloud_cover_pct']:>4.0f}%")
    print()
    return result

def run_step_3_prediction(db, telemetry_list=None):
    print(f"{YELLOW}{BOLD}[STEP 3/3] Running AI Landslide/Flood Risk Prediction on Live Satellite Data...{RESET}")
    print(f"{DIM}Executing trained model on real-time satellite telemetry & slope parameters...{RESET}")

    predictions = run_satellite_predictions_all(db, telemetry_list)

    print(f"\n{GREEN}{BOLD}[OK] Inference Completed for {len(predictions)} Monitored Hazard Points!{RESET}\n")
    print(f"  {BOLD}{'Hazard Location':<34} {'State':<7} {'Risk Level':<12} {'Probability':<12} {'Key Thresholds / Status'}{RESET}")
    print("  " + "-" * 105)

    critical_count = 0
    high_count = 0

    for p in predictions:
        r_class = p["risk_class"]
        prob_pct = p["risk_probability"] * 100.0

        if r_class == "CRITICAL":
            badge = f"{RED}{BOLD}CRITICAL   {RESET}"
            critical_count += 1
        elif r_class == "HIGH":
            badge = f"{YELLOW}{BOLD}HIGH       {RESET}"
            high_count += 1
        elif r_class == "MODERATE":
            badge = f"{CYAN}MODERATE   {RESET}"
        else:
            badge = f"{GREEN}LOW        {RESET}"

        triggers = ", ".join(p.get("thresholds_exceeded", []))
        if not triggers:
            triggers = "Slope & pore pressure within normal stability limits"

        print(f"  {p['location_name'][:32]:<34} {p['state_id']:<7} {badge} {prob_pct:>6.2f}%      {triggers[:52]}")

    print("  " + "-" * 105)
    print(f"\n{BOLD}Disaster Advisory Summary:{RESET}")
    print(f"  * {RED}{BOLD}CRITICAL EVACUATION ALERTS:{RESET} {critical_count}")
    print(f"  * {YELLOW}{BOLD}HIGH READINESS ALERTS:{RESET}      {high_count}")
    print(f"  * {GREEN}MODERATE / NORMAL LOCATIONS:{RESET} {len(predictions) - critical_count - high_count}")
    print()
    return predictions

async def main():
    parser = argparse.ArgumentParser(description="NE-SHIELD Satellite AI Prediction Pipeline")
    parser.add_argument("--train-only", action="store_true", help="Only train the model on Government Data")
    parser.add_argument("--satellite-only", action="store_true", help="Only fetch live satellite telemetry")
    parser.add_argument("--predict-only", action="store_true", help="Only predict on existing satellite data")
    parser.add_argument("--all", action="store_true", default=True, help="Run complete 3-step pipeline")
    args = parser.parse_args()

    print_banner()

    # Ensure database tables exist
    db = SessionLocal()
    seed_initial_data(db)

    try:
        if args.train_only:
            run_step_1_training(db)
        elif args.satellite_only:
            await run_step_2_satellite(db)
        elif args.predict_only:
            run_step_3_prediction(db)
        else:
            # Full pipeline
            run_step_1_training(db)
            sat_result = await run_step_2_satellite(db)
            run_step_3_prediction(db, sat_result.get("telemetry", []))

        print(f"{GREEN}{BOLD}Pipeline execution completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST.{RESET}\n")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
