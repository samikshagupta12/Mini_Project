"""
End-to-End Integration Tests for In-Memory Demo Mode (mongomock).
Verifies:
- Zero-installation startup without local MongoDB
- Registration and login
- Database CRUD operations
- Skill assessment submission and metric calculation
- CART Decision Tree inference
- Entire program computation pipeline and learning roadmap persistence
- Roadmap task completion tracking
- Demo archetypes creation
"""
import pytest
from datetime import datetime, timezone
from config.settings import TOPICS, READINESS_CLASSES
from database.connection import get_mongo_client, get_database, get_connection_details, reset_connection
from database.collections import (
    get_students_collection,
    get_questions_collection,
    get_assessments_collection,
    get_readiness_collection,
    get_roadmaps_collection,
    init_db_indexes,
    to_object_id,
)
from utils.auth import register_student, authenticate_student, get_or_create_demo_student
from ml.predict import predict_readiness, ensure_model_initialized
from utils.helpers import calculate_assessment_metrics
from modules.computation_engine import compute_entire_program


@pytest.fixture(autouse=True)
def setup_demo_environment():
    """Ensures in-memory demo database client is active."""
    reset_connection()
    client, is_mock, _ = get_mongo_client(use_mock=True)
    db = get_database(use_mock=True)
    init_db_indexes(db)
    return db


def test_demo_mode_auto_seeding():
    db = get_database(use_mock=True)
    q_col = get_questions_collection(db)
    assert q_col is not None
    count_q = q_col.count_documents({})
    assert count_q >= 32


def test_demo_mode_registration_and_auth():
    test_email = "test.e2e@university.edu"
    profile_data = {
        "name": "Jane E2E",
        "email": test_email,
        "education": "B.Tech / B.E. (Computer Science / IT)",
        "course": "Computer Science and Engineering",
        "target_role": "Software Engineer",
        "experience_level": "Student / College Fresher",
        "preferred_language": "Python",
    }
    ok, student_doc, errors = register_student(profile_data, "securepass123")
    assert ok is True
    assert student_doc is not None
    assert student_doc["email"] == test_email

    auth_ok, auth_user, auth_msg = authenticate_student(test_email, "securepass123")
    assert auth_ok is True
    assert auth_user["name"] == "Jane E2E"


def test_demo_mode_assessment_and_computation():
    db = get_database(use_mock=True)
    # Register candidate
    email = "eval.candidate@university.edu"
    profile = {
        "name": "Eval Candidate",
        "email": email,
        "education": "B.Tech / B.E. (Computer Science / IT)",
        "course": "IT",
        "target_role": "Software Engineer",
        "experience_level": "Student / College Fresher",
        "preferred_language": "Python",
    }
    ok, student_doc, _ = register_student(profile, "mypassword123")
    assert ok is True
    student_id = to_object_id(student_doc["_id"])

    # Submit assessment
    scores = {topic: 75.0 for topic in TOPICS}
    scores["Data Structures and Algorithms"] = 88.0
    scores["Problem-Solving Skills"] = 85.0
    metrics = calculate_assessment_metrics(scores)

    assmt_col = get_assessments_collection(db)
    assmt_doc = {
        "student_id": student_id,
        "student_email": email,
        "topic_scores": scores,
        "average_score": metrics["overall_average"],
        "strong_topics": metrics["strong_topics"],
        "moderate_topics": metrics["moderate_topics"],
        "weak_topics": metrics["weak_topics"],
        "created_at": datetime.now(timezone.utc),
    }
    res = assmt_col.insert_one(assmt_doc)
    assert res.inserted_id is not None

    # Run ML prediction
    pred = predict_readiness(scores)
    assert pred["prediction"] in READINESS_CLASSES
    assert pred["confidence"] > 0
    assert pred["is_academic_demonstration"] is True

    # Run entire program computation
    comp = compute_entire_program(student_id, force_roadmap_refresh=True)
    assert "composite_index" in comp
    assert "composite_grade" in comp
    assert "roadmap_tasks_count" in comp
    assert comp["roadmap_tasks_count"] > 0

    # Verify roadmap saved
    rm_col = get_roadmaps_collection(db)
    rm_doc = rm_col.find_one({"student_id": student_id})
    assert rm_doc is not None

    # Test task update in mock database
    rm_col.update_one(
        {"_id": rm_doc["_id"]},
        {"$set": {"tasks.0.completed": True, "completion_percentage": 25.0}}
    )
    updated_rm = rm_col.find_one({"_id": rm_doc["_id"]})
    assert updated_rm["tasks"][0]["completed"] is True


def test_demo_archetypes():
    alice = get_or_create_demo_student("ready")
    assert alice["name"] == "Alice Johnson"
    assert alice["target_role"] == "Software Engineer"

    bob = get_or_create_demo_student("improving")
    assert bob["name"] == "Bob Smith"
    assert bob["target_role"] == "Data Scientist"
