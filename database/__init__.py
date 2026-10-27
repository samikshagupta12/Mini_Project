"""Database package initialization."""
from .connection import get_database, check_connection, get_mongo_client
from .collections import (
    get_students_collection,
    get_questions_collection,
    get_assessments_collection,
    get_readiness_collection,
    get_roadmaps_collection,
    get_practice_sessions_collection,
    init_db_indexes,
)

