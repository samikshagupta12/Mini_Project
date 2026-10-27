"""Collection accessors, index management, and schema helpers."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId
from pymongo.database import Database
from pymongo.collection import Collection
import pymongo
from database.connection import get_database


def to_object_id(val: Any) -> Optional[ObjectId]:
    """Converts a string or ObjectId to ObjectId safely."""
    if isinstance(val, ObjectId):
        return val
    if isinstance(val, str) and ObjectId.is_valid(val):
        return ObjectId(val)
    return None


def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Recursively converts ObjectId and datetime fields into strings for UI display."""
    if doc is None:
        return None
    res = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            res[k] = str(v)
        elif isinstance(v, datetime):
            res[k] = v.isoformat()
        elif isinstance(v, dict):
            res[k] = serialize_doc(v)
        elif isinstance(v, list):
            res[k] = [serialize_doc(i) if isinstance(i, dict) else (str(i) if isinstance(i, ObjectId) else i) for i in v]
        else:
            res[k] = v
    return res


# Collection getters
def get_students_collection(db: Optional[Database] = None) -> Optional[Collection]:
    db = db or get_database()
    return db["students"] if db is not None else None


def get_questions_collection(db: Optional[Database] = None) -> Optional[Collection]:
    db = db or get_database()
    return db["interview_questions"] if db is not None else None


def get_assessments_collection(db: Optional[Database] = None) -> Optional[Collection]:
    db = db or get_database()
    return db["assessments"] if db is not None else None


def get_readiness_collection(db: Optional[Database] = None) -> Optional[Collection]:
    db = db or get_database()
    return db["readiness_predictions"] if db is not None else None


def get_roadmaps_collection(db: Optional[Database] = None) -> Optional[Collection]:
    db = db or get_database()
    return db["learning_roadmaps"] if db is not None else None


def get_practice_sessions_collection(db: Optional[Database] = None) -> Optional[Collection]:
    db = db or get_database()
    return db["practice_sessions"] if db is not None else None


def init_db_indexes(db: Optional[Database] = None):
    """Initializes indexes on all collections for performance and uniqueness."""
    db = db or get_database()
    if db is None:
        return False
    try:
        # Students: unique index on email
        db["students"].create_index("email", unique=True)
        
        # Interview Questions: indexes on topic, difficulty, question_id
        db["interview_questions"].create_index([("topic", pymongo.ASCENDING), ("difficulty", pymongo.ASCENDING)])
        db["interview_questions"].create_index("question_id", unique=True, sparse=True)
        
        # Assessments: index on student_id and created_at
        db["assessments"].create_index([("student_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
        
        # Readiness Predictions: index on student_id
        db["readiness_predictions"].create_index([("student_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
        
        # Roadmaps: index on student_id and assessment_id
        db["learning_roadmaps"].create_index([("student_id", pymongo.ASCENDING), ("assessment_id", pymongo.ASCENDING)])
        
        # Practice sessions: index on student_id
        db["practice_sessions"].create_index([("student_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
        return True
    except Exception as e:
        # For mock databases or environments where indexes might be restricted
        return False

