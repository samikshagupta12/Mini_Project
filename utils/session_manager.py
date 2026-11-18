"""Session state initialization and role-based authentication/session helpers."""
import streamlit as st
from typing import Optional, Dict, Any


def init_session_state():
    """Initializes all necessary Streamlit session state keys if not already set."""
    defaults = {
        "current_student": None,
        "current_admin": None,
        "is_admin": False,
        "user_role": "guest",  # 'guest', 'student', or 'admin'
        "active_email": "",
        "active_assessment": None,
        "latest_prediction": None,
        "practice_questions": [],
        "practice_revealed": {},
        "practice_ratings": {},
        "current_page": "Login / Register",
        "system_computation": None,
        "notification": None,
        "nav_category": "All Modules",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_current_student() -> Optional[Dict[str, Any]]:
    """Returns the currently active student document."""
    return st.session_state.get("current_student")


def set_current_student(student: Dict[str, Any]):
    """Sets the active student in session state."""
    st.session_state.current_student = student
    st.session_state.active_email = student.get("email", "")
    st.session_state.user_role = "student"
    st.session_state.is_admin = False
    st.session_state.current_admin = None


def get_current_admin() -> Optional[Dict[str, Any]]:
    """Returns the currently active administrator document."""
    return st.session_state.get("current_admin")


def is_admin_logged_in() -> bool:
    """Checks whether an administrator session is currently active."""
    return bool(st.session_state.get("is_admin", False) and st.session_state.get("current_admin"))


def set_current_admin(admin_doc: Dict[str, Any]):
    """Sets the active administrator in session state."""
    st.session_state.current_admin = admin_doc
    st.session_state.is_admin = True
    st.session_state.user_role = "admin"
    st.session_state.current_student = None
    st.session_state.active_email = admin_doc.get("email", "")


def get_user_role() -> str:
    """Returns the active user role ('guest', 'student', or 'admin')."""
    if is_admin_logged_in():
        return "admin"
    if get_current_student() is not None:
        return "student"
    return "guest"


def clear_current_student():
    """Logs out or clears the current active student session."""
    st.session_state.current_student = None
    st.session_state.active_email = ""
    st.session_state.active_assessment = None
    st.session_state.latest_prediction = None
    st.session_state.practice_questions = []
    st.session_state.practice_revealed = {}
    st.session_state.system_computation = None
    st.session_state.user_role = "guest"
    st.session_state.current_page = "Login / Register"


def clear_admin_session():
    """Logs out the administrator session."""
    st.session_state.current_admin = None
    st.session_state.is_admin = False
    st.session_state.user_role = "guest"
    st.session_state.current_page = "Login / Register"


def clear_all_sessions():
    """Clears all session states and resets to default login view."""
    clear_current_student()
    clear_admin_session()
