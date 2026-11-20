"""Decision Tree training script for AI Interview Readiness Prediction."""
import os
import json
import logging
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)
import joblib

from config.settings import (
    TOPICS,
    READINESS_CLASSES,
    MODEL_PATH,
    MODEL_METADATA_PATH,
    MODELS_DIR,
    SYNTHETIC_DATASET_PATH,
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
    Employs an 80/20 stratified train/test split alongside 5-fold Stratified Cross-Validation.
    Computes per-class performance metrics and saves synthetic data to an isolated CSV file,
    ensuring 100% separation from MongoDB student assessment records.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Generating synthetic training dataset for academic demonstration...")
    df = generate_synthetic_dataset(num_samples=num_samples, random_seed=42)

    # Strictly isolate synthetic training data in dedicated CSV file
    df.to_csv(SYNTHETIC_DATASET_PATH, index=False)
    logger.info(f"Synthetic training data saved separately to: {SYNTHETIC_DATASET_PATH}")

    X = df[FEATURE_COLUMNS]
    y = df["Target"]

    # 1. 80/20 train/test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # 2. Decision Tree Classifier with moderate depth to prevent overfitting
    clf = DecisionTreeClassifier(
        criterion="gini",
        max_depth=6,
        min_samples_split=12,
        min_samples_leaf=6,
        random_state=42,
    )
    clf.fit(X_train, y_train)

    # Predictions on holdout test set
    y_pred = clf.predict(X_test)

    # Compute holdout evaluation metrics
    acc = float(accuracy_score(y_test, y_pred))
    prec_weighted = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
    rec_weighted = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
    f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

    prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

    cm = confusion_matrix(y_test, y_pred, labels=READINESS_CLASSES).tolist()

    # 3. 5-Fold Stratified Cross-Validation across dataset
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scoring = {
        "accuracy": "accuracy",
        "precision_weighted": "precision_weighted",
        "recall_weighted": "recall_weighted",
        "f1_weighted": "f1_weighted",
    }
    cv_res = cross_validate(clf, X, y, cv=cv, scoring=cv_scoring)

    cv_summary = {
        "n_splits": 5,
        "mean_accuracy": round(float(np.mean(cv_res["test_accuracy"])), 4),
        "std_accuracy": round(float(np.std(cv_res["test_accuracy"])), 4),
        "mean_f1_weighted": round(float(np.mean(cv_res["test_f1_weighted"])), 4),
        "std_f1_weighted": round(float(np.std(cv_res["test_f1_weighted"])), 4),
        "mean_precision_weighted": round(float(np.mean(cv_res["test_precision_weighted"])), 4),
        "std_precision_weighted": round(float(np.std(cv_res["test_precision_weighted"])), 4),
        "mean_recall_weighted": round(float(np.mean(cv_res["test_recall_weighted"])), 4),
        "std_recall_weighted": round(float(np.std(cv_res["test_recall_weighted"])), 4),
        "fold_accuracies": [round(float(v), 4) for v in cv_res["test_accuracy"]],
        "fold_f1_scores": [round(float(v), 4) for v in cv_res["test_f1_weighted"]],
    }

    # 4. Detailed Classification Report & Per-Class Performance
    raw_report = classification_report(
        y_test, y_pred, labels=READINESS_CLASSES, target_names=READINESS_CLASSES, output_dict=True, zero_division=0
    )
    report_text = classification_report(
        y_test, y_pred, labels=READINESS_CLASSES, target_names=READINESS_CLASSES, zero_division=0
    )

    per_class_performance = {}
    for cls in READINESS_CLASSES:
        cls_data = raw_report.get(cls, {})
        per_class_performance[cls] = {
            "precision": round(float(cls_data.get("precision", 0.0)), 4),
            "recall": round(float(cls_data.get("recall", 0.0)), 4),
            "f1_score": round(float(cls_data.get("f1-score", 0.0)), 4),
            "support": int(cls_data.get("support", 0)),
        }

    # Feature importance dictionary
    importances = {
        feat: float(round(imp, 4))
        for feat, imp in zip(FEATURE_COLUMNS, clf.feature_importances_)
    }
    sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))

    metadata = {
        "model_type": "DecisionTreeClassifier",
        "algorithm_parameters": clf.get_params(),
        "classes": READINESS_CLASSES,
        "feature_columns": FEATURE_COLUMNS,
        "training_samples": len(X_train),
        "testing_samples": len(X_test),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "is_academic_demonstration": True,
        "model_purpose": "Academic Demonstration & Prototype Pedagogical Readiness Model",
        "synthetic_data_isolation": f"Saved separately to {SYNTHETIC_DATASET_PATH}. Never mixed into MongoDB student records.",
        "evaluation_metrics": {
            "accuracy": round(acc, 4),
            "precision_weighted": round(prec_weighted, 4),
            "recall_weighted": round(rec_weighted, 4),
            "f1_weighted": round(f1_weighted, 4),
            "precision_macro": round(prec_macro, 4),
            "recall_macro": round(rec_macro, 4),
            "f1_macro": round(f1_macro, 4),
        },
        "cross_validation": cv_summary,
        "per_class_performance": per_class_performance,
        "classification_report_text": report_text,
        "confusion_matrix": {
            "labels": READINESS_CLASSES,
            "matrix": cm,
        },
        "feature_importances": sorted_importances,
        "dataset_notice": (
            "ACADEMIC DEMONSTRATION NOTICE: This Decision Tree model is trained on a synthetic dataset for "
            "academic evaluation and pedagogical assessment. Prediction confidence represents archetype "
            "classification alignment, NOT a guaranteed probability of receiving a commercial job offer."
        ),
    }

    if save:
        joblib.dump(clf, MODEL_PATH)
        with open(MODEL_METADATA_PATH, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Model saved to {MODEL_PATH}")
        logger.info(f"Metadata saved to {MODEL_METADATA_PATH}")

    logger.info(
        f"Training Complete. Holdout Acc: {acc:.2%}, 5-Fold CV Mean Acc: {cv_summary['mean_accuracy']:.2%} (+/- {cv_summary['std_accuracy']:.2%})"
    )
    return metadata


if __name__ == "__main__":
    train_decision_tree_model(save=True)

