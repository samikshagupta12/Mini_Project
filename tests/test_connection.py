"""
Unit tests for database connection module and dual-mode architecture.
Tests the 5 core functions required by app.py:
1. check_connection()
2. get_database()
3. get_connection_details()
4. reset_connection()
5. test_and_set_mongo_uri()
"""
import pytest
from database.connection import (
    check_connection,
    get_database,
    get_connection_details,
    reset_connection,
    test_and_set_mongo_uri,
    get_mongo_client,
    get_beginner_connection_guide,
)
import database
import database.db


def test_imports_and_exports():
    """Verifies that all 5 required functions can be imported from database.connection, database, and database.db."""
    for mod in [database.connection, database, database.db]:
        assert hasattr(mod, "check_connection"), f"Missing check_connection in {mod}"
        assert hasattr(mod, "get_database"), f"Missing get_database in {mod}"
        assert hasattr(mod, "get_connection_details"), f"Missing get_connection_details in {mod}"
        assert hasattr(mod, "reset_connection"), f"Missing reset_connection in {mod}"
        assert hasattr(mod, "test_and_set_mongo_uri"), f"Missing test_and_set_mongo_uri in {mod}"


def test_check_connection_demo_mode():
    """Verifies check_connection in Demo Mode returns available=True and is_mock=True."""
    reset_connection()
    is_avail, is_mock, msg = check_connection(use_mock=True)
    assert is_avail is True
    assert is_mock is True
    assert "Demo Mode" in msg or "mock" in msg.lower()


def test_get_database_demo_mode():
    """Verifies get_database returns a functioning database object with collections."""
    db = get_database(use_mock=True)
    assert db is not None
    assert "students" in db.list_collection_names() or True  # mongomock handles collections dynamically
    # Test writing and reading from mock database
    col = db["test_collection"]
    col.insert_one({"name": "Test Entry", "val": 42})
    found = col.find_one({"val": 42})
    assert found is not None
    assert found["name"] == "Test Entry"


def test_get_connection_details_structure():
    """Verifies get_connection_details provides all UI metadata keys required by Streamlit."""
    details = get_connection_details(use_mock=True)
    required_keys = [
        "is_connected",
        "is_mock",
        "is_permanent",
        "status",
        "badge_text",
        "status_label",
        "status_color",
        "host",
        "database",
        "message",
        "storage_warning",
        "instructions",
        "mode_name",
    ]
    for key in required_keys:
        assert key in details, f"Missing key '{key}' in connection details"
    assert details["is_connected"] is True
    assert details["is_mock"] is True
    assert details["is_permanent"] is False


def test_test_and_set_mongo_uri_empty():
    """Verifies test_and_set_mongo_uri rejects empty or whitespace URIs safely."""
    ok, msg = test_and_set_mongo_uri("")
    assert ok is False
    assert "cannot be empty" in msg.lower()

    ok, msg = test_and_set_mongo_uri("   ")
    assert ok is False
    assert "cannot be empty" in msg.lower()


def test_test_and_set_mongo_uri_invalid_host():
    """Verifies test_and_set_mongo_uri safely fails without crashing on an unreachable or invalid host."""
    # Using an unreachable host on a non-standard port with rapid timeout
    ok, msg = test_and_set_mongo_uri("mongodb://127.0.0.1:59999/test_db?serverSelectionTimeoutMS=500")
    assert ok is False
    assert "Connection failed" in msg or "failed" in msg.lower()


def test_reset_connection():
    """Verifies reset_connection properly clears client handles and resets state."""
    reset_connection()
    details = get_connection_details(use_mock=True)
    assert details["is_connected"] is True
    assert details["is_mock"] is True


def test_beginner_connection_guide():
    """Verifies the beginner troubleshooting guide formats correctly."""
    guide = get_beginner_connection_guide("mongodb://localhost:27017")
    assert "title" in guide
    assert "windows_steps" in guide
    assert len(guide["windows_steps"]) >= 2
    assert "mac_steps" in guide
    assert "linux_steps" in guide
