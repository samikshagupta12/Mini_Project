"""Unit tests for ML readiness prediction with Decision Tree."""
import pytest
from ml.train_model import train_decision_tree_model
from ml.predict import predict_readiness, ensure_model_initialized
from config.settings import TOPICS, READINESS_CLASSES


@pytest.fixture(scope="session", autouse=True)
def ensure_model_trained():
    """Ensures model artifact is trained and saved prior to test assertions."""
    train_decision_tree_model(save=True, num_samples=300)


def test_predict_readiness_high_scores():
    scores = {topic: 88.0 for topic in TOPICS}
    result = predict_readiness(scores)

    assert result["prediction"] in READINESS_CLASSES
    assert result["prediction"] == "Interview Ready"
    assert result["overall_average"] == 88.0
    assert "probabilities" in result
    assert sum(result["probabilities"].values()) == pytest.approx(100.0, rel=1e-1)
    assert result["is_synthetic"] is True


def test_predict_readiness_low_scores():
    scores = {topic: 30.0 for topic in TOPICS}
    result = predict_readiness(scores)

    assert result["prediction"] == "Beginner / Needs Improvement"
    assert result["overall_average"] == 30.0
    assert len(result["top_influencing_features"]) > 0


def test_predict_readiness_intermediate_scores():
    scores = {topic: 62.0 for topic in TOPICS}
    result = predict_readiness(scores)

    assert result["prediction"] == "Intermediate / Partially Ready"
    assert result["overall_average"] == 62.0


def test_ensure_model_initialization():
    ok, metadata, msg = ensure_model_initialized(force_retrain=False)
    assert ok is True
    assert metadata is not None
    assert "evaluation_metrics" in metadata
    assert metadata["evaluation_metrics"]["accuracy"] > 0.60
    assert "feature_columns" in metadata


def test_ensure_model_initialization_when_file_missing(tmp_path):
    from config.settings import MODEL_PATH, MODEL_METADATA_PATH
    import os
    # Temporarily remove artifacts if present
    if MODEL_PATH.exists():
        os.remove(MODEL_PATH)
    if MODEL_METADATA_PATH.exists():
        os.remove(MODEL_METADATA_PATH)

    # Actual initialization must re-create both files
    ok, metadata, msg = ensure_model_initialized(force_retrain=True)
    assert ok is True
    assert MODEL_PATH.exists()
    assert MODEL_METADATA_PATH.exists()
    assert metadata["evaluation_metrics"]["accuracy"] > 0.60

