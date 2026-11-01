import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = Path(os.getenv("TRUTHGRAPH_MODELS_DIR", BACKEND_DIR / "models"))

MODEL_PATH = Path(os.getenv("TRUTHGRAPH_MODEL_PATH", MODELS_DIR / "truthgraph_final_model.pkl"))
FEATURES_PATH = Path(os.getenv("TRUTHGRAPH_FEATURES_PATH", MODELS_DIR / "truthgraph_feature_columns.pkl"))
ENCODER_PATH = Path(os.getenv("TRUTHGRAPH_ENCODER_PATH", MODELS_DIR / "truthgraph_label_encoder.pkl"))
METADATA_PATH = Path(os.getenv("TRUTHGRAPH_METADATA_PATH", MODELS_DIR / "truthgraph_model_metadata.json"))

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("TRUTHGRAPH_ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
    if origin.strip()
]
