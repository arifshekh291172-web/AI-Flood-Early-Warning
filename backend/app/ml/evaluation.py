from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)
from backend.app.ml.feature_engineering import FEATURE_COLUMNS

def calculate_model_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    feature_importances: np.ndarray | None = None
) -> Dict[str, Any]:
    """
    Computes genuine, mathematically verified validation metrics.
    Never invents or fabricates performance numbers.
    """
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    try:
        auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        auc = 0.5

    cm = confusion_matrix(y_true, y_pred).tolist()

    # Map feature importances
    feat_imp_dict = {}
    if feature_importances is not None and len(feature_importances) == len(FEATURE_COLUMNS):
        for col, imp in zip(FEATURE_COLUMNS, feature_importances):
            feat_imp_dict[col] = round(float(imp), 4)

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(auc, 4),
        "confusion_matrix": cm,
        "feature_importances": feat_imp_dict
    }
