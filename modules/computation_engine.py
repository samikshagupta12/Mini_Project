"""
System-wide Mathematical Computation & Analytics Engine.
Calculates role-weighted proficiencies, Decision Tree predictions,
roadmap tasks, practice mastery, and composite readiness indices.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np

from config.settings import TOPICS, STRONG_THRESHOLD, MODERATE_THRESHOLD, JOB_ROLES
from database.collections import (
    get_assessments_collection,
    get_readiness_collection,
    get_roadmaps_collection,
    get_practice_sessions_collection,
    get_students_collection,
    to_object_id,
    serialize_doc,
)
from utils.helpers import calculate_assessment_metrics, classify_topic_score
from ml.predict import predict_readiness

# Role-specific importance weight vectors (Sum of weights = 1.0)
ROLE_TOPIC_WEIGHTS: Dict[str, Dict[str, float]] = {
    "Software Engineer": {
        "Data Structures and Algorithms": 0.20,
        "Problem-Solving Skills": 0.20,
        "Object-Oriented Programming": 0.15,
        "Python Programming": 0.10,
        "Operating Systems": 0.10,
        "Computer Networks": 0.10,
        "Database Management Systems": 0.05,
        "SQL and MongoDB": 0.05,
        "Machine Learning": 0.025,
        "Data Analysis": 0.025,
    },
    "Backend Developer": {
        "Database Management Systems": 0.18,
        "SQL and MongoDB": 0.18,
        "Object-Oriented Programming": 0.15,
        "Data Structures and Algorithms": 0.15,
        "Python Programming": 0.12,
        "Operating Systems": 0.10,
        "Computer Networks": 0.08,
        "Problem-Solving Skills": 0.04,
        "Machine Learning": 0.00,
        "Data Analysis": 0.00,
    },
    "Data Scientist": {
        "Machine Learning": 0.25,
        "Python Programming": 0.20,
        "Data Analysis": 0.20,
        "SQL and MongoDB": 0.15,
        "Problem-Solving Skills": 0.10,
        "Database Management Systems": 0.05,
        "Data Structures and Algorithms": 0.05,
        "Object-Oriented Programming": 0.00,
        "Operating Systems": 0.00,
        "Computer Networks": 0.00,
    },
    "Machine Learning Engineer": {
        "Machine Learning": 0.28,
        "Python Programming": 0.20,
        "Data Structures and Algorithms": 0.16,
        "Problem-Solving Skills": 0.12,
        "Data Analysis": 0.10,
        "Object-Oriented Programming": 0.08,
        "Database Management Systems": 0.03,
        "SQL and MongoDB": 0.03,
        "Operating Systems": 0.00,
        "Computer Networks": 0.00,
    },
    "Data Analyst": {
        "Data Analysis": 0.30,
        "SQL and MongoDB": 0.25,
        "Python Programming": 0.20,
        "Database Management Systems": 0.15,
        "Problem-Solving Skills": 0.10,
        "Data Structures and Algorithms": 0.00,
        "Object-Oriented Programming": 0.00,
        "Operating Systems": 0.00,
        "Computer Networks": 0.00,
        "Machine Learning": 0.00,
    },
    "Full Stack Developer": {
        "Object-Oriented Programming": 0.15,
        "SQL and MongoDB": 0.15,
        "Python Programming": 0.15,
        "Database Management Systems": 0.15,
        "Computer Networks": 0.12,
        "Data Structures and Algorithms": 0.12,
        "Problem-Solving Skills": 0.10,
        "Operating Systems": 0.06,
        "Machine Learning": 0.00,
        "Data Analysis": 0.00,
    },
}


def calculate_role_weighted_score(topic_scores: Dict[str, float], target_role: str) -> float:
    """
    Computes the role-weighted technical proficiency score based on the target job profile.
    Formula: S_role = Sum(w_i * s_i)
    """
    weights = ROLE_TOPIC_WEIGHTS.get(target_role)
    if not weights:
        # Default to equal uniform weighting
        return round(float(np.mean(list(topic_scores.values()))), 1)

    weighted_sum = 0.0
    for topic, score in topic_scores.items():
        w = weights.get(topic, 0.10)
        weighted_sum += w * score

    return round(float(weighted_sum), 1)


def calculate_composite_readiness_index(
    role_weighted_score: float,
    roadmap_completion_pct: float,
    practice_mastery_pct: float,
    has_practice: bool = False
) -> Dict[str, Any]:
    """
    Computes a holistic 0–100 Composite Interview Readiness Index:
    Formula: 55% Role-Weighted Score + 25% Roadmap Completion + 20% Practice Mastery
    (Adjusted dynamically if no practice sessions have been logged yet).
    """
    if has_practice:
        index_val = (
            0.55 * role_weighted_score +
            0.25 * roadmap_completion_pct +
            0.20 * practice_mastery_pct
        )
    else:
        # If no practice yet, distribute between assessment (75%) and roadmap (25%)
        index_val = (
            0.75 * role_weighted_score +
            0.25 * roadmap_completion_pct
        )

    final_val = round(float(np.clip(index_val, 0.0, 100.0)), 1)

    # Assign Letter Grade
    if final_val >= 90.0:
        grade = "A+"
        tier = "Elite Readiness"
        color = "#2ECC71"
    elif final_val >= 80.0:
        grade = "A"
        tier = "Interview Ready"
        color = "#2ECC71"
    elif final_val >= 70.0:
        grade = "B"
        tier = "Partially Ready"
        color = "#F39C12"
    elif final_val >= 50.0:
        grade = "C"
        tier = "Developing Foundations"
        color = "#E67E22"
    else:
        grade = "D"
        tier = "Needs Intensive Prep"
        color = "#E74C3C"

    return {
        "index_score": final_val,
        "grade": grade,
        "tier": tier,
        "color": color,
    }


def compute_entire_program(student_id_val: Any, force_roadmap_refresh: bool = False) -> Dict[str, Any]:
    """
    Executes the end-to-end computation pipeline for the given student:
    1. Aggregates assessment history and latest metrics.
    2. Computes role-weighted performance.
    3. Executes Decision Tree ML inference.
    4. Synchronizes or generates the personalized roadmap in MongoDB.
    5. Aggregates question practice mastery statistics.
    6. Synthesizes the Composite Interview Readiness Index.
    7. Computes historical progress trajectory.
    """
    student_id = to_object_id(student_id_val)
    if not student_id:
        return {}

    students_col = get_students_collection()
    assessments_col = get_assessments_collection()
    readiness_col = get_readiness_collection()
    roadmaps_col = get_roadmaps_collection()
    practice_col = get_practice_sessions_collection()

    student_doc = students_col.find_one({"_id": student_id}) if students_col is not None else None
    target_role = student_doc.get("target_role", "Software Engineer") if student_doc else "Software Engineer"

    # 1. Fetch Assessments
    history = list(assessments_col.find({"student_id": student_id}).sort("created_at", -1)) if assessments_col is not None else []
    
    if not history:
        return {
            "has_data": False,
            "target_role": target_role,
            "assessments_count": 0,
        }

    latest_assessment = history[0]
    topic_scores = latest_assessment.get("topic_scores", {})
    metrics = calculate_assessment_metrics(topic_scores)

    # 2. Role-weighted Score
    role_weighted_score = calculate_role_weighted_score(topic_scores, target_role)

    # 3. Decision Tree ML Readiness Prediction
    ml_result = predict_readiness(topic_scores)
    now = datetime.now(timezone.utc)

    # Save or update prediction record in MongoDB
    if readiness_col is not None:
        pred_record = {
            "student_id": student_id,
            "assessment_id": latest_assessment["_id"],
            "predicted_readiness": ml_result["prediction"],
            "confidence": ml_result["confidence"],
            "probabilities": ml_result["probabilities"],
            "overall_average": ml_result["overall_average"],
            "role_weighted_score": role_weighted_score,
            "top_influencing_features": ml_result["top_influencing_features"],
            "explanation": ml_result["explanation"],
            "recommendation": ml_result["recommendation"],
            "model_version": "DecisionTree-v1.0",
            "created_at": now,
        }
        readiness_col.update_one(
            {"student_id": student_id, "assessment_id": latest_assessment["_id"]},
            {"$set": pred_record},
            upsert=True
        )

    # 4. Learning Roadmap Synchronization
    roadmap_completion_pct = 0.0
    tasks = []
    if roadmaps_col is not None:
        from modules.learning_roadmap import build_roadmap_for_assessment
        existing_rm = roadmaps_col.find_one({
            "student_id": student_id,
            "assessment_id": latest_assessment["_id"]
        })

        if not existing_rm or force_roadmap_refresh:
            tasks = build_roadmap_for_assessment(latest_assessment, target_role)
            roadmap_doc = {
                "student_id": student_id,
                "assessment_id": latest_assessment["_id"],
                "target_role": target_role,
                "tasks": tasks,
                "completion_percentage": 0.0,
                "created_at": now,
                "updated_at": now,
            }
            if existing_rm:
                roadmaps_col.update_one({"_id": existing_rm["_id"]}, {"$set": roadmap_doc})
            else:
                roadmaps_col.insert_one(roadmap_doc)
            roadmap_completion_pct = 0.0
        else:
            tasks = existing_rm.get("tasks", [])
            total_t = len(tasks)
            done_t = sum(1 for t in tasks if t.get("completed", False))
            roadmap_completion_pct = round((done_t / total_t * 100), 1) if total_t > 0 else 100.0

    # 5. Practice Statistics
    practice_sessions = list(practice_col.find({"student_id": student_id})) if practice_col is not None else []
    total_practiced = len(practice_sessions)
    mastered_count = sum(1 for p in practice_sessions if "Mastered" in p.get("self_rating", ""))
    practice_mastery_pct = round((mastered_count / total_practiced * 100), 1) if total_practiced > 0 else 0.0

    # 6. Composite Readiness Index
    composite_info = calculate_composite_readiness_index(
        role_weighted_score=role_weighted_score,
        roadmap_completion_pct=roadmap_completion_pct,
        practice_mastery_pct=practice_mastery_pct,
        has_practice=(total_practiced > 0)
    )

    # 7. Historical Delta (Current vs Previous)
    delta_score = 0.0
    has_previous = len(history) > 1
    if has_previous:
        prev_scores = history[1].get("topic_scores", {})
        prev_avg = history[1].get("average_score", 0.0)
        delta_score = round(metrics["overall_average"] - prev_avg, 1)

    return {
        "has_data": True,
        "student_id": str(student_id),
        "target_role": target_role,
        "assessments_count": len(history),
        "overall_average": metrics["overall_average"],
        "role_weighted_score": role_weighted_score,
        "strong_topics": metrics["strong_topics"],
        "moderate_topics": metrics["moderate_topics"],
        "weak_topics": metrics["weak_topics"],
        "highest_topic": metrics["highest_topic"],
        "highest_score": metrics["highest_score"],
        "lowest_topic": metrics["lowest_topic"],
        "lowest_score": metrics["lowest_score"],
        "rankings": metrics["rankings"],
        "topic_scores": topic_scores,
        "ml_prediction": ml_result["prediction"],
        "ml_confidence": ml_result["confidence"],
        "ml_probabilities": ml_result["probabilities"],
        "ml_explanation": ml_result["explanation"],
        "ml_recommendation": ml_result["recommendation"],
        "roadmap_tasks_count": len(tasks),
        "roadmap_completion_pct": roadmap_completion_pct,
        "practice_total": total_practiced,
        "practice_mastered": mastered_count,
        "practice_mastery_pct": practice_mastery_pct,
        "composite_index": composite_info["index_score"],
        "composite_grade": composite_info["grade"],
        "composite_tier": composite_info["tier"],
        "composite_color": composite_info["color"],
        "has_previous": has_previous,
        "delta_score": delta_score,
        "computed_at": now.isoformat(),
    }

