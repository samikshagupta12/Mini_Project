"""
MongoDB Connection Manager with Dual-Mode Architecture:
Mode 1: In-Memory Demo Mode (mongomock) - Default, Zero Installation Required.
Mode 2: Real MongoDB Mode (Local mongod or MongoDB Atlas) - Permanent Disk Storage.
Ensures zero crashes, automatic mock data seeding, non-blocking diagnostics, and safe fallbacks.
"""
import logging
from typing import Optional, Tuple, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config.settings import MONGODB_URI, MONGODB_DATABASE, USE_MOCK_DB, DEMO_MODE

logger = logging.getLogger(__name__)

__all__ = [
    "get_mongo_client",
    "get_database",
    "check_connection",
    "get_connection_details",
    "reset_connection",
    "test_and_set_mongo_uri",
    "get_beginner_connection_guide",
]

# Global client singletons
_real_client: Optional[MongoClient] = None
_mock_client: Optional[Any] = None
_active_client: Optional[Any] = None
_active_database: Optional[Database] = None
_is_mock: bool = True
_last_error_message: str = ""
_real_mongo_attempted: bool = False
_real_mongo_failed: bool = False
_custom_uri: Optional[str] = None


def _get_target_uri() -> str:
    """Returns custom runtime URI if specified, else MONGODB_URI from settings."""
    global _custom_uri
    try:
        import streamlit as st
        return st.session_state.get("custom_mongo_uri", _custom_uri or MONGODB_URI)
    except Exception:
        return _custom_uri or MONGODB_URI


def _auto_seed_mock_db(mock_client_instance):
    """Automatically seeds initial questions into the mock database so features work out of the box."""
    try:
        from database.seed_questions import SEED_QUESTIONS
        from datetime import datetime, timezone
        db = mock_client_instance[MONGODB_DATABASE]
        col = db["interview_questions"]
        if col.count_documents({}) == 0:
            now = datetime.now(timezone.utc)
            docs = []
            for item in SEED_QUESTIONS:
                doc = dict(item)
                doc["created_at"] = now
                doc["updated_at"] = now
                docs.append(doc)
            col.insert_many(docs)
            logger.info(f"Auto-seeded {len(docs)} foundational questions into in-memory mock database.")
    except Exception as e:
        logger.warning(f"Note on mock database auto-seeding: {e}")


def _get_or_create_mock_client():
    """Initializes and returns the singleton in-memory mongomock client."""
    global _mock_client
    if _mock_client is None:
        try:
            import mongomock
            _mock_client = mongomock.MongoClient()
            _auto_seed_mock_db(_mock_client)
            logger.info("Initialized singleton mongomock in-memory database.")
        except ImportError:
            logger.error("mongomock package not found. Please install mongomock.")
            return None
    return _mock_client


def get_beginner_connection_guide(target_uri: Optional[str] = None) -> Dict[str, Any]:
    """Translates database connection failures into plain-language troubleshooting steps."""
    uri = target_uri or _get_target_uri()
    host_clean = uri.split("@")[-1].split("/")[0] if "@" in uri else uri.replace("mongodb://", "")
    return {
        "title": "Cannot Connect to Real MongoDB",
        "what_happened": f"The application attempted to connect to '{host_clean}', but received no response within 2.0 seconds.",
        "why_it_happened": (
            "The MongoDB database service (mongod) is not running on your computer, "
            "or the network connection to the database was refused."
        ),
        "windows_steps": [
            "1. Press Win + R, type 'services.msc', and verify if 'MongoDB Server' is running.",
            "2. Or open PowerShell as Administrator and run: net start MongoDB",
            "3. Or start the daemon manually: mongod --dbpath C:\\data\\db",
        ],
        "mac_steps": [
            "1. Open Terminal and run: brew services start mongodb-community",
            "2. Or start directly: mongod --config /usr/local/etc/mongod.conf",
        ],
        "linux_steps": [
            "1. Open Terminal and run: sudo systemctl start mongod",
            "2. Verify status: sudo systemctl status mongod",
        ],
        "cloud_atlas_tip": (
            "Using MongoDB Atlas (Cloud)? Paste your mongodb+srv:// connection string in the connection "
            "expander above or in your .env file, and ensure your current IP address is whitelisted in Atlas Network Access."
        ),
        "demo_mode_solution": (
            "No MongoDB installed? You do NOT need MongoDB to use this system! "
            "Demo Mode runs 100% in-memory using mongomock with all features enabled."
        ),
    }


def get_mongo_client(
    uri: Optional[str] = None,
    force_new: bool = False,
    use_mock: Optional[bool] = None
) -> Tuple[Optional[MongoClient], bool, str]:
    """
    Returns an active MongoDB client instance.
    Defaults to In-Memory Demo Mode (mongomock) for zero-setup execution.
    If Real MongoDB is requested and offline, safely falls back to Demo Mode with clear notification.
    Returns: (client, is_mock, status_message)
    """
    global _real_client, _mock_client, _active_client, _is_mock
    global _last_error_message, _real_mongo_attempted, _real_mongo_failed

    # Determine desired mode
    if use_mock is not None:
        desired_mock = use_mock
    else:
        try:
            import streamlit as st
            desired_mock = st.session_state.get("demo_mode", None)
        except Exception:
            desired_mock = None

        if desired_mock is None:
            if _custom_uri is not None and not _is_mock and _real_client is not None:
                desired_mock = False
            else:
                desired_mock = USE_MOCK_DB

    target_uri = uri or _get_target_uri()

    # 1. DEMO MODE REQUESTED (DEFAULT)
    if desired_mock:
        mock_c = _get_or_create_mock_client()
        if mock_c is not None:
            _active_client = mock_c
            _is_mock = True
            _last_error_message = ""
            msg = "Demo Mode Active: Running with in-memory mock database (no MongoDB installation required)."
            return _active_client, True, msg
        else:
            return None, False, "mongomock package unavailable."

    # 2. REAL MONGODB REQUESTED
    _real_mongo_attempted = True
    if _real_client is not None and not force_new and not _is_mock:
        return _real_client, False, f"Connected to Real MongoDB ({MONGODB_DATABASE})"

    try:
        logger.info(f"Connecting to Real MongoDB at {target_uri}...")
        client = MongoClient(target_uri, serverSelectionTimeoutMS=2000)
        # Ping command to ensure live communication
        client.admin.command("ping")
        
        _real_client = client
        _active_client = client
        _is_mock = False
        _real_mongo_failed = False
        _last_error_message = ""
        
        host_name = target_uri.split("@")[-1].split("/")[0] if "@" in target_uri else target_uri.replace("mongodb://", "")
        msg = f"Connected to Real MongoDB at {host_name} (Database: {MONGODB_DATABASE})"
        logger.info(msg)
        return _active_client, False, msg

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        _real_client = None
        _real_mongo_failed = True
        host_name = target_uri.split("@")[-1].split("/")[0] if "@" in target_uri else target_uri.replace("mongodb://", "")
        err_msg = f"Cannot connect to Real MongoDB at '{host_name}'. Service is offline or unreachable."
        _last_error_message = f"{err_msg} Details: {str(e)}"
        logger.warning(f"{_last_error_message} Safely activating Demo Mode (mongomock).")

        # Graceful fallback: Do NOT crash or block. Provide working mock client
        mock_c = _get_or_create_mock_client()
        _active_client = mock_c
        _is_mock = True
        return _active_client, True, f"{err_msg} -> Running in In-Memory Demo Mode."

    except Exception as e:
        _real_client = None
        _real_mongo_failed = True
        err_msg = f"Unexpected error connecting to Real MongoDB: {str(e)}"
        _last_error_message = err_msg
        logger.error(err_msg)

        mock_c = _get_or_create_mock_client()
        _active_client = mock_c
        _is_mock = True
        return _active_client, True, f"{err_msg} -> Running in In-Memory Demo Mode."


def get_database(db_name: Optional[str] = None, use_mock: Optional[bool] = None) -> Optional[Database]:
    """Retrieves the active database handle (real or mock)."""
    global _active_database
    client, is_mock, msg = get_mongo_client(use_mock=use_mock)
    if client is None:
        return None
    target_db_name = db_name or MONGODB_DATABASE
    _active_database = client[target_db_name]
    return _active_database


def check_connection(use_mock: Optional[bool] = None) -> Tuple[bool, bool, str]:
    """
    Checks database connectivity.
    Returns: (is_available, is_mock, status_message)
    """
    client, is_mock, msg = get_mongo_client(use_mock=use_mock)
    if client is None:
        return False, False, msg
    return True, is_mock, msg


def get_connection_details(use_mock: Optional[bool] = None) -> Dict[str, Any]:
    """
    Returns structured connection metadata for the UI:
    Real Connected, Demo Mode, or Real Failed with Demo Fallback.
    """
    global _real_mongo_failed, _last_error_message, _real_mongo_attempted
    client, is_mock, msg = get_mongo_client(use_mock=use_mock)
    target_uri = _get_target_uri()
    target_host = target_uri.split("@")[-1].split("/")[0] if "@" in target_uri else target_uri.replace("mongodb://", "")

    # REAL MONGODB CONNECTED & PERSISTENT
    if client is not None and not is_mock:
        return {
            "is_connected": True,
            "is_mock": False,
            "is_permanent": True,
            "status": "connected",
            "badge_text": "🟢 Real MongoDB (Persistent Storage Active)",
            "status_label": "Connected to Real MongoDB",
            "status_color": "green",
            "host": target_host,
            "database": MONGODB_DATABASE,
            "message": msg,
            "storage_warning": None,
            "real_mongo_failed": False,
            "instructions": f"Connected to active MongoDB at {target_host} ({MONGODB_DATABASE}). All user profiles, assessments, and roadmaps persist permanently to disk.",
            "beginner_guide": None,
            "mode_name": "Real MongoDB (Persistent)",
        }

    # DEMO MODE ACTIVE (EITHER BY DEFAULT OR FALLBACK)
    guide = get_beginner_connection_guide(target_uri)
    if _real_mongo_failed:
        badge = "⚠️ Real MongoDB Offline -> Demo Mode Active"
        storage_warn = "⚠️ Real MongoDB is unreachable. The application is running in In-Memory Demo Mode. Records will not persist to disk after server shutdown."
    else:
        badge = "🟡 Demo Mode (In-Memory Database Active)"
        storage_warn = "ℹ️ Running in Demo Mode (In-Memory). No MongoDB installation required! Data is held in-memory for this session."

    return {
        "is_connected": True,
        "is_mock": True,
        "is_permanent": False,
        "status": "mock",
        "badge_text": badge,
        "status_label": "In-Memory Simulation (mongomock Active)",
        "status_color": "orange",
        "host": "In-Memory RAM (mongomock)",
        "database": MONGODB_DATABASE,
        "message": msg,
        "storage_warning": storage_warn,
        "real_mongo_failed": _real_mongo_failed,
        "real_mongo_error": _last_error_message,
        "instructions": "Operating in Demo Mode with in-memory storage. All 10 modules function normally without requiring MongoDB installation.",
        "beginner_guide": guide,
        "mode_name": "Demo Mode (In-Memory)",
    }


def test_and_set_mongo_uri(custom_uri: str) -> Tuple[bool, str]:
    """Tests connection to a specified MongoDB URI and switches to it if successful."""
    global _custom_uri, _real_client, _active_client, _active_database, _is_mock, _real_mongo_failed, _last_error_message
    if not custom_uri or not isinstance(custom_uri, str):
        return False, "URI cannot be empty or invalid."
    clean_uri = custom_uri.strip()
    if not clean_uri:
        return False, "URI cannot be empty."

    try:
        test_client = MongoClient(clean_uri, serverSelectionTimeoutMS=2500)
        test_client.admin.command("ping")
        _custom_uri = clean_uri
        _real_client = test_client
        _active_client = test_client
        _active_database = test_client[MONGODB_DATABASE]
        _is_mock = False
        _real_mongo_failed = False
        _last_error_message = ""
        
        # Save to Streamlit session state if available
        try:
            import streamlit as st
            st.session_state["custom_mongo_uri"] = clean_uri
            st.session_state["demo_mode"] = False
        except Exception:
            pass

        # Ensure collections & indexes exist on the new database
        try:
            from database.collections import init_db_indexes
            init_db_indexes(_active_database)
        except Exception as e:
            logger.warning(f"Index initialization on custom database: {e}")

        host_part = clean_uri.split("@")[-1].split("/")[0] if "@" in clean_uri else clean_uri.replace("mongodb://", "").replace("mongodb+srv://", "")
        return True, f"Successfully connected to MongoDB at '{host_part}'!"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


# Tell pytest not to collect test_and_set_mongo_uri as a test case
test_and_set_mongo_uri.__test__ = False


def reset_connection(reset_custom_uri: bool = False):
    """Resets cached client connections."""
    global _real_client, _active_client, _active_database, _is_mock, _last_error_message, _real_mongo_failed, _custom_uri
    if _real_client is not None:
        try:
            _real_client.close()
        except Exception:
            pass
    _real_client = None
    _active_client = None
    _active_database = None
    if reset_custom_uri:
        _custom_uri = None

    try:
        import streamlit as st
        _is_mock = st.session_state.get("demo_mode", USE_MOCK_DB)
    except Exception:
        _is_mock = USE_MOCK_DB

    _last_error_message = ""
    _real_mongo_failed = False
