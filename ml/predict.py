"""Inference module for AI Interview Readiness using the trained Decision Tree."""
import json
import logging
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
import joblib

from config.settings import (
    TOPICS,
    READINESS_CLASSES,
    MODEL_PATH,
    MODEL_METADATA_PATH,
)

logger = logging.getLogger(__name__)

_model = None
_metadata = None


def load_model():
    """Loads the serialized Decision Tree model and metadata."""
    global _model, _metadata
    if _model is not None and _metadata is not None:
        return _model, _metadata

    if not MODEL_PATH.exists() or not MODEL_METADATA_PATH.exists():
        # Automatically trigger training if model artifact does not exist
        logger.info("Trained model not found. Automatically triggering training...")
        from ml.train_model import train_decision_tree_model
        train_decision_tree_model(save=True)

    try:
        _model = joblib.load(MODEL_PATH)
        with open(MODEL_METADATA_PATH, "r") as f:
            _metadata = json.load(f)
        return _model, _metadata
    except Exception as e:
        logger.error(f"Failed to load Decision Tree model: {e}")
        return None, None


def get_model_status() -> Tuple[bool, Optional[dict]]:
    """Checks whether the model artifact is loaded and returns metadata."""
    model, metadata = load_model()
    return (model is not None), metadata


def predict_readiness(scores: Dict[str, float]) -> Dict[str, Any]:
    """
    Predicts interview readiness level from a dictionary of 10 topic scores.
    Returns:
        dict: {
            "prediction": str,
            "confidence": float,
            "probabilities": dict,
            "overall_average": float,
            "top_influencing_features": list,
            "explanation": str,
            "recommendation": str,
            "is_synthetic": bool
        }
    """
    model, metadata = load_model()
    if model is None:
        raise RuntimeError("Decision Tree model could not be loaded or trained.")

    feature_cols = metadata["feature_columns"]
    
    # Calculate Overall Average Score
    topic_values = [float(scores.get(t, 0.0)) for t in TOPICS]
    overall_avg = round(float(np.mean(topic_values)), 1)
    
    # Build feature row
    row = {t: float(scores.get(t, 0.0)) for t in TOPICS}
    row["Overall Average Score"] = overall_avg
    
    df_input = pd.DataFrame([row])[feature_cols]

    # Predict class & probabilities
    prediction = model.predict(df_input)[0]
    probabilities = {}
    confidence = 0.0

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(df_input)[0]
        classes = model.classes_
        for cls_name, p in zip(classes, probs):
            probabilities[cls_name] = round(float(p) * 100, 1)
        confidence = float(np.max(probs)) * 100

    # Determine top influential features for explanation
    feat_importances = metadata.get("feature_importances", {})
    top_features = []
    for feat, imp in list(feat_importances.items())[:3]:
        val = row.get(feat, 0.0)
        top_features.append({"feature": feat, "importance": imp, "score": val})

    # Generate student-friendly explanation
    if prediction == "Interview Ready":
        explanation = (
            f"Your strong technical performance (Overall Average: {overall_avg}%) across core algorithmic and domain "
            f"topics indicates a high level of interview preparedness."
        )
        recommendation = (
            "Focus on timed mock interviews, system design fundamentals, and behavioral questions (STAR technique)."
        )
    elif prediction == "Intermediate / Partially Ready":
        explanation = (
            f"You have demonstrated solid understanding in several key subjects (Overall Average: {overall_avg}%), "
            f"but targeted practice is required in weaker areas before real-world interviews."
        )
        recommendation = (
            "Complete your personalized roadmap exercises and practice medium-difficulty coding questions."
        )
    else:
        explanation = (
            f"Your current foundational scores (Overall Average: {overall_avg}%) suggest substantial room for growth "
            f"in data structures, syntax mastery, and problem-solving fundamentals."
        )
        recommendation = (
            "Start with beginner-level concept reviews in your weakest topics, build small projects, and retake the assessment."
        )

    return {
        "prediction": prediction,
        "confidence": round(confidence, 1),
        "probabilities": probabilities,
        "overall_average": overall_avg,
        "top_influencing_features": top_features,
        "explanation": explanation,
        "recommendation": recommendation,
        "is_synthetic": True,
        "notice": metadata.get("dataset_notice", "")
    }

