"""Database package initialization with dual-mode MongoDB support."""
from .connection import (
    get_mongo_client,
    get_database,
    check_connection,
    get_connection_details,
    reset_connection,
    test_and_set_mongo_uri,
    get_beginner_connection_guide,
)
from .collections import (
    get_students_collection,
    get_questions_collection,
    get_assessments_collection,
    get_readiness_collection,
    get_roadmaps_collection,
    get_practice_sessions_collection,
    get_research_data_collection,
    init_db_indexes,
    to_object_id,
    serialize_doc,
)

__all__ = [
    "get_mongo_client",
    "get_database",
    "check_connection",
    "get_connection_details",
    "reset_connection",
    "test_and_set_mongo_uri",
    "get_beginner_connection_guide",
    "get_students_collection",
    "get_questions_collection",
    "get_assessments_collection",
    "get_readiness_collection",
    "get_roadmaps_collection",
    "get_practice_sessions_collection",
    "get_research_data_collection",
    "init_db_indexes",
    "to_object_id",
    "serialize_doc",
]


