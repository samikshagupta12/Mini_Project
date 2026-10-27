"""Evaluation data provider for visualization and reporting."""
import json
from typing import Optional, Dict, Any
from config.settings import MODEL_METADATA_PATH


def get_evaluation_metrics() -> Optional[Dict[str, Any]]:
    """Loads evaluation metrics and training metadata from disk."""
    if not MODEL_METADATA_PATH.exists():
        return None
    try:
        with open(MODEL_METADATA_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return None

