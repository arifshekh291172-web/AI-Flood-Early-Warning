import os
import json
import joblib
from typing import Any, Dict, Optional, Tuple
from backend.app.ml.train import (
    DEFAULT_MODEL_PATH, DEFAULT_METADATA_PATH, train_landslide_model
)
from backend.app.utils.logger import logger

class ModelRegistry:
    def __init__(self):
        self.model: Optional[Any] = None
        self.metadata: Optional[Dict[str, Any]] = None
        self._load_active_model()

    def _load_active_model(self):
        try:
            if os.path.exists(DEFAULT_MODEL_PATH) and os.path.exists(DEFAULT_METADATA_PATH):
                self.model = joblib.load(DEFAULT_MODEL_PATH)
                with open(DEFAULT_METADATA_PATH, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded active ML model: {self.metadata.get('version_tag')}")
            else:
                logger.info("No active model artifact found. Initializing training...")
                self.model, self.metadata = train_landslide_model()
        except Exception as e:
            logger.error(f"Error loading active model: {str(e)}. Retraining baseline model...")
            self.model, self.metadata = train_landslide_model()

    def get_model(self) -> Any:
        if self.model is None:
            self._load_active_model()
        return self.model

    def get_metadata(self) -> Dict[str, Any]:
        if self.metadata is None:
            self._load_active_model()
        return self.metadata or {}

    def reload(self):
        self._load_active_model()

model_registry = ModelRegistry()
