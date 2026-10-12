from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import os
import json

from backend.app.database import get_db
from backend.app.models.core import ModelVersion, ModelPredictionLog, User, AuditLog
from backend.app.ml.model_loader import model_registry
from backend.app.ml.train import train_landslide_model
from backend.app.ml.dataset import DATASET_PATH
from backend.app.schemas.reports import ModelStatusResponse, ModelTrainRequest
from backend.app.utils.security import get_current_user, require_role
from backend.app.utils.provenance import to_ist_string

router = APIRouter(prefix="/api/model", tags=["ML Model Operations"])

@router.get("/status", response_model=ModelStatusResponse)
def get_model_status(db: Session = Depends(get_db)):
    """
    Returns live ML model governance parameters, dataset statistics,
    validation metrics, feature importances, and confusion matrix.
    Never invents or fabricates accuracy.
    """
    meta = model_registry.get_metadata()
    if not meta:
        raise HTTPException(status_code=503, detail="ML model is initializing. Try again shortly.")

    # Calculate inferences run today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    inferences_today = db.query(ModelPredictionLog).filter(
        ModelPredictionLog.created_at >= today_start
    ).count()

    latest_inf = db.query(ModelPredictionLog).order_by(
        ModelPredictionLog.created_at.desc()
    ).first()

    return ModelStatusResponse(
        active_version=meta.get("version_tag", "UNKNOWN"),
        model_name=meta.get("model_name", "NE-SHIELD Landslide Classifier"),
        algorithm=meta.get("algorithm", "GradientBoostingClassifier"),
        dataset_size=meta.get("dataset_size", 0),
        training_status=meta.get("status", "PRODUCTION_ACTIVE"),
        metrics=meta.get("metrics", {}),
        features=meta.get("features", []),
        trained_at_ist=to_ist_string(datetime.fromisoformat(meta.get("trained_at", datetime.utcnow().isoformat()).replace("Z", ""))),
        last_inference_time_ist=to_ist_string(latest_inf.created_at) if latest_inf else None,
        total_inferences_today=inferences_today
    )

@router.get("/metrics")
def get_model_metrics():
    meta = model_registry.get_metadata()
    if not meta:
        raise HTTPException(status_code=503, detail="No active model loaded")
    return {
        "version_tag": meta.get("version_tag"),
        "algorithm": meta.get("algorithm"),
        "hyperparameters": meta.get("hyperparameters"),
        "metrics": meta.get("metrics")
    }

@router.post("/train")
def trigger_model_training(
    req: ModelTrainRequest,
    current_user: User = Depends(require_role(["ADMIN", "ANALYST"])),
    db: Session = Depends(get_db)
):
    """
    Triggers model training using specified algorithm.
    Validates metrics, serializes active model, updates version registry, and writes audit record.
    """
    try:
        clf, meta = train_landslide_model(
            algorithm=req.algorithm or "GradientBoostingClassifier",
            n_estimators=req.n_estimators or 80,
            learning_rate=req.learning_rate or 0.1,
            max_depth=req.max_depth or 4,
            db=db,
            user_email=current_user.email
        )
        model_registry.reload()

        return {
            "success": True,
            "message": f"Model {meta['version_tag']} successfully trained and activated!",
            "version_tag": meta["version_tag"],
            "algorithm": meta["algorithm"],
            "metrics": meta["metrics"],
            "trained_at_ist": to_ist_string(datetime.utcnow())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training pipeline error: {str(e)}")

@router.post("/train-interactive")
def trigger_interactive_training(
    algorithm: str = Query("GradientBoostingClassifier"),
    n_estimators: int = Query(80),
    learning_rate: float = Query(0.1),
    max_depth: int = Query(4),
    db: Session = Depends(get_db)
):
    """
    Directly triggers machine learning training on official geotechnical records from the console UI.
    """
    try:
        clf, meta = train_landslide_model(
            algorithm=algorithm,
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            db=db,
            user_email="web-console@ne-shield.gov.in"
        )
        model_registry.reload()

        return {
            "success": True,
            "message": f"Model {meta['version_tag']} trained successfully on {meta['dataset_size']} ground-truth records!",
            "version_tag": meta["version_tag"],
            "algorithm": meta["algorithm"],
            "hyperparameters": meta["hyperparameters"],
            "metrics": meta["metrics"],
            "dataset_size": meta["dataset_size"],
            "train_samples": meta["train_samples"],
            "test_samples": meta["test_samples"],
            "trained_at_ist": to_ist_string(datetime.utcnow())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interactive training error: {str(e)}")

@router.post("/upload-dataset")
async def upload_training_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Allows authenticated administrators to upload an approved historical landslide CSV dataset.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    with open(DATASET_PATH, "wb") as f:
        f.write(content)

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="DATASET_UPLOADED",
        resource_type="dataset",
        resource_id=file.filename,
        result_status="SUCCESS"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": f"Dataset {file.filename} uploaded ({len(content)} bytes). You can now trigger retrain.",
        "uploaded_at_ist": to_ist_string(datetime.utcnow())
    }
