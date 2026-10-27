"""MongoDB connection manager with error handling and optional mock support."""
import logging
from typing import Optional, Tuple
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config.settings import MONGODB_URI, MONGODB_DATABASE, USE_MOCK_DB

logger = logging.getLogger(__name__)

# Global client cache
_client: Optional[MongoClient] = None
_database: Optional[Database] = None
_is_mock: bool = False


def get_mongo_client(uri: Optional[str] = None, force_new: bool = False, use_mock: Optional[bool] = None) -> Tuple[Optional[MongoClient], bool, str]:
    """
    Returns a MongoDB client instance.
    Returns: (client, is_mock, status_message)
    """
    global _client, _is_mock
    
    mock_mode = USE_MOCK_DB if use_mock is None else use_mock
    
    if _client is not None and not force_new and _is_mock == mock_mode:
        return _client, _is_mock, "Using cached client"

    if mock_mode:
        try:
            import mongomock
            _client = mongomock.MongoClient()
            _is_mock = True
            msg = "Running with in-memory Mock MongoDB (USE_MOCK_DB=True)"
            logger.info(msg)
            return _client, True, msg
        except ImportError:
            msg = "mongomock is not installed. Falling back to real MongoDB."
            logger.warning(msg)

    target_uri = uri or MONGODB_URI
    try:
        # Connect with a fast 2-second timeout so offline database doesn't hang UI
        client = MongoClient(target_uri, serverSelectionTimeoutMS=2000)
        # Verify connection by issuing a ping command
        client.admin.command("ping")
        _client = client
        _is_mock = False
        msg = f"Connected to MongoDB at {target_uri.split('@')[-1]}"
        logger.info(msg)
        return _client, False, msg
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"MongoDB connection failed: {e}")
        # If real DB fails but USE_MOCK_DB wasn't forced, we can check if mongomock is available for safe fallback
        try:
            import mongomock
            logger.warning("MongoDB service unreachable. Initializing in-memory mock database for fallback testing.")
            _client = mongomock.MongoClient()
            _is_mock = True
            return _client, True, f"MongoDB offline ({e.__class__.__name__}). Fallback in-memory database active."
        except ImportError:
            _client = None
            _is_mock = False
            return None, False, f"Could not connect to MongoDB at {target_uri}: {e}"


def get_database(db_name: Optional[str] = None) -> Optional[Database]:
    """Retrieves the active database handle."""
    global _database
    client, is_mock, msg = get_mongo_client()
    if client is None:
        return None
    target_db_name = db_name or MONGODB_DATABASE
    _database = client[target_db_name]
    return _database


def check_connection() -> Tuple[bool, bool, str]:
    """
    Checks database connectivity.
    Returns: (is_available, is_mock, status_message)
    """
    client, is_mock, msg = get_mongo_client()
    if client is None:
        return False, False, msg
    return True, is_mock, msg


def reset_connection():
    """Resets cached client and database instances."""
    global _client, _database, _is_mock
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
    _client = None
    _database = None
    _is_mock = False

