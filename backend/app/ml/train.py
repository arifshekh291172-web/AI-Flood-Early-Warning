import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import json
import joblib
import datetime
from typing import Dict, Any, Tuple
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session

from backend.app.ml.dataset import load_training_data
from backend.app.ml.evaluation import calculate_model_metrics
from backend.app.ml.feature_engineering import FEATURE_COLUMNS
from backend.app.utils.logger import logger

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

DEFAULT_MODEL_PATH = os.path.join(MODELS_DIR, "active_model.joblib")
DEFAULT_METADATA_PATH = os.path.join(MODELS_DIR, "active_model.json")

def train_landslide_model(
    algorithm: str = "GradientBoostingClassifier",
    n_estimators: int = 80,
    learning_rate: float = 0.1,
    max_depth: int = 4,
    db: Session | None = None,
    user_email: str = "system"
) -> Tuple[Any, Dict[str, Any]]:
    """
    Trains the NE-SHIELD Landslide Risk Machine Learning model on geotechnical data.
    Computes genuine validation metrics and stores the active artifact.
    """
    logger.info(f"Initiating ML Model Training using {algorithm}...")
    X, y = load_training_data()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    if algorithm == "RandomForestClassifier":
        clf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42
        )
    else:
        algorithm = "GradientBoostingClassifier"
        clf = GradientBoostingClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=42
        )

    clf.fit(X_train, y_train)

    # Evaluate on held-out test set
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    metrics = calculate_model_metrics(
        y_true=y_test,
        y_pred=y_pred,
        y_prob=y_prob,
        feature_importances=clf.feature_importances_
    )

    now = datetime.datetime.utcnow()
    version_tag = f"NE-SHIELD-v{now.strftime('%Y%m%d-%H%M%S')}"

    metadata = {
        "version_tag": version_tag,
        "model_name": "NE-SHIELD Landslide Susceptibility & Risk Classifier",
        "algorithm": algorithm,
        "dataset_size": len(X),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "features": FEATURE_COLUMNS,
        "hyperparameters": {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate if algorithm != "RandomForestClassifier" else None
        },
        "metrics": metrics,
        "trained_at": now.isoformat() + "Z",
        "trained_by": user_email,
        "status": "PRODUCTION_ACTIVE"
    }

    # Save artifacts
    joblib.dump(clf, DEFAULT_MODEL_PATH)
    with open(DEFAULT_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(
        f"Model {version_tag} trained successfully! "
        f"Accuracy: {metrics['accuracy']:.4f}, ROC-AUC: {metrics['roc_auc']:.4f}, F1: {metrics['f1_score']:.4f}"
    )

    if db:
        try:
            from backend.app.models.core import ModelVersion, AuditLog
            # Check if version_tag exists to prevent unique constraint violation
            existing_mv = db.query(ModelVersion).filter(ModelVersion.version_tag == version_tag).first()
            if existing_mv:
                version_tag = f"{version_tag}-{datetime.datetime.utcnow().strftime('%f')[:4]}"
                metadata["version_tag"] = version_tag

            mv = ModelVersion(
                version_tag=version_tag,
                model_name=metadata["model_name"],
                algorithm=algorithm,
                dataset_size=len(X),
                features_list=FEATURE_COLUMNS,
                hyperparameters=metadata["hyperparameters"],
                validation_metrics=metrics,
                status="ACTIVE",
                trained_at=datetime.datetime.utcnow(),
                activated_at=datetime.datetime.utcnow(),
                trained_by=user_email
            )
            db.query(ModelVersion).filter(ModelVersion.status == "ACTIVE").update({"status": "ARCHIVED"})
            db.add(mv)

            audit = AuditLog(
                action="MODEL_TRAINED_AND_ACTIVATED",
                resource_type="model_version",
                resource_id=version_tag,
                details=metadata,
                result_status="SUCCESS",
                user_email=user_email
            )
            db.add(audit)
            db.commit()
        except Exception as dbe:
            db.rollback()
            logger.error(f"Error recording model version to DB: {str(dbe)}")

    return clf, metadata

if __name__ == "__main__":
    train_landslide_model()
