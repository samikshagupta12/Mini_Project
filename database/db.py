"""
Database Facade & Unified Access Layer.
Provides backward-compatible and standard exports for database connection management,
collection getters, indexing, document serialization, and mode switching.
"""
from typing import Optional, Tuple, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from database.connection import (
    get_mongo_client,
    get_database,
    check_connection,
    get_connection_details,
    reset_connection,
    test_and_set_mongo_uri,
    get_beginner_connection_guide,
)
from database.collections import (
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

# Standard alias names for convenience
get_client = get_mongo_client
get_db = get_database
check_db_connection = check_connection

__all__ = [
    "get_client",
    "get_mongo_client",
    "get_db",
    "get_database",
    "check_connection",
    "check_db_connection",
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
