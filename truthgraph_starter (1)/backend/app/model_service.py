import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import joblib

from .config import MODEL_PATH, FEATURES_PATH, ENCODER_PATH, METADATA_PATH

@dataclass
class ModelArtifacts:
    model: Any = None
    feature_columns: Any = None
    label_encoder: Any = None
    metadata: dict | None = None
    load_error: Optional[str] = None

    @property
    def loaded(self) -> bool:
        return self.model is not None and self.feature_columns is not None and self.label_encoder is not None

def load_artifacts() -> ModelArtifacts:
    missing = [str(p) for p in (MODEL_PATH, FEATURES_PATH, ENCODER_PATH) if not p.exists()]
    if missing:
        return ModelArtifacts(load_error="Model artifact files not found: " + ", ".join(missing))
    try:
        model = joblib.load(MODEL_PATH)
        feature_columns = joblib.load(FEATURES_PATH)
        label_encoder = joblib.load(ENCODER_PATH)
        metadata = {}
        if METADATA_PATH.exists():
            with METADATA_PATH.open("r", encoding="utf-8") as f:
                metadata = json.load(f)
        return ModelArtifacts(model, feature_columns, label_encoder, metadata)
    except Exception as exc:
        return ModelArtifacts(load_error=f"Could not load model artifacts: {type(exc).__name__}: {exc}")
