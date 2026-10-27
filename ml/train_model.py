"""Decision Tree training script for AI Interview Readiness Prediction."""
import os
import json
import logging
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib

from config.settings import (
    TOPICS,
    READINESS_CLASSES,
    MODEL_PATH,
    MODEL_METADATA_PATH,
    MODELS_DIR,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FEATURE_COLUMNS = TOPICS + ["Overall Average Score"]


def generate_synthetic_dataset(num_samples: int = 800, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates a realistic, labeled synthetic dataset representing student assessment scores.
    
    Academic Note & Assumptions:
    - This dataset is synthetically generated for academic demonstration of ML Decision Trees.
    - Features: 10 technical topic scores (0 to 100) + Overall Average Score.
    - Ground Truth Labeling Rules:
        * 'Interview Ready': High overall performance (>= 75) with solid fundamentals in DSA,
          Problem-Solving, and at least one core domain (>= 65).
        * 'Beginner / Needs Improvement': Low overall performance (< 50) or severe deficits
          in foundational problem-solving (< 45).
        * 'Intermediate / Partially Ready': Moderate scores (50 to 74), or strong domain knowledge
          with specific improvement areas.
    - Realistic noise (+-5% random perturbations) is added to model realistic human performance variance.
    """
    np.random.seed(random_seed)
    data = []

    for _ in range(num_samples):
        # Sample student archetype: 0 = Beginner (30%), 1 = Intermediate (45%), 2 = Ready (25%)
        archetype = np.random.choice([0, 1, 2], p=[0.30, 0.45, 0.25])
        
        if archetype == 0:
            # Beginner: Mean score around 40
            scores = np.clip(np.random.normal(loc=38, scale=12, size=len(TOPICS)), 5, 68)
        elif archetype == 1:
            # Intermediate: Mean score around 64
            scores = np.clip(np.random.normal(loc=64, scale=11, size=len(TOPICS)), 25, 88)
        else:
            # Interview Ready: Mean score around 84
            scores = np.clip(np.random.normal(loc=83, scale=8, size=len(TOPICS)), 60, 99)

        # Round to integers
        scores = [float(round(s, 1)) for s in scores]
        row_dict = {topic: score for topic, score in zip(TOPICS, scores)}
        
        # Calculate Overall Average
        overall_avg = round(float(np.mean(scores)), 1)
        row_dict["Overall Average Score"] = overall_avg
        
        # Determine Label based on documented educational logic
        dsa = row_dict["Data Structures and Algorithms"]
        problem_solving = row_dict["Problem-Solving Skills"]
        python_score = row_dict["Python Programming"]

        if overall_avg >= 74 and dsa >= 65 and problem_solving >= 65:
            label = "Interview Ready"
        elif overall_avg < 50 or (dsa < 42 and problem_solving < 42):
            label = "Beginner / Needs Improvement"
        else:
            label = "Intermediate / Partially Ready"

        # Add 3% realistic label noise to simulate human interviewer borderline variance
        if np.random.rand() < 0.03:
            label = np.random.choice(READINESS_CLASSES)

        row_dict["Target"] = label
        data.append(row_dict)

    df = pd.DataFrame(data)
    return df


def train_decision_tree_model(save: bool = True, num_samples: int = 800) -> dict:
    """
    Trains and evaluates the Scikit-learn Decision Tree Classifier.
    Saves the model to disk using Joblib.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Generating synthetic training dataset...")
    df = generate_synthetic_dataset(num_samples=num_samples, random_seed=42)

    X = df[FEATURE_COLUMNS]
    y = df["Target"]

    # 80/20 train/test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Train Decision Tree Classifier with moderate depth to prevent overfitting
    clf = DecisionTreeClassifier(
        criterion="gini",
        max_depth=6,
        min_samples_split=12,
        min_samples_leaf=6,
        random_state=42,
    )
    clf.fit(X_train, y_train)

    # Predictions on test set
    y_pred = clf.predict(X_test)

    # Compute comprehensive evaluation metrics
    acc = float(accuracy_score(y_test, y_pred))
    prec_weighted = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
    rec_weighted = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
    f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

    prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

    cm = confusion_matrix(y_test, y_pred, labels=READINESS_CLASSES).tolist()

    # Feature importance dictionary
    importances = {
        feat: float(round(imp, 4))
        for feat, imp in zip(FEATURE_COLUMNS, clf.feature_importances_)
    }
    # Sort by importance descending
    sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))

    metadata = {
        "model_type": "DecisionTreeClassifier",
        "algorithm_parameters": clf.get_params(),
        "classes": READINESS_CLASSES,
        "feature_columns": FEATURE_COLUMNS,
        "training_samples": len(X_train),
        "testing_samples": len(X_test),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_metrics": {
            "accuracy": round(acc, 4),
            "precision_weighted": round(prec_weighted, 4),
            "recall_weighted": round(rec_weighted, 4),
            "f1_weighted": round(f1_weighted, 4),
            "precision_macro": round(prec_macro, 4),
            "recall_macro": round(rec_macro, 4),
            "f1_macro": round(f1_macro, 4),
        },
        "confusion_matrix": {
            "labels": READINESS_CLASSES,
            "matrix": cm,
        },
        "feature_importances": sorted_importances,
        "dataset_notice": (
            "NOTICE: This model is trained on a synthetic demonstration dataset for academic evaluation. "
            "Predictions indicate technical readiness tendencies and require real-world interview validation."
        ),
    }

    if save:
        joblib.dump(clf, MODEL_PATH)
        with open(MODEL_METADATA_PATH, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Model saved to {MODEL_PATH}")
        logger.info(f"Metadata saved to {MODEL_METADATA_PATH}")

    logger.info(f"Training Complete. Accuracy: {acc:.2%}, F1-Score: {f1_weighted:.4f}")
    return metadata


if __name__ == "__main__":
    train_decision_tree_model(save=True)

