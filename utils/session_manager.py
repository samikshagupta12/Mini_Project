"""Session state initialization and student authentication/session helpers."""
import streamlit as st
from typing import Optional, Dict, Any


def init_session_state():
    """Initializes all necessary Streamlit session state keys if not already set."""
    defaults = {
        "current_student": None,
        "active_email": "",
        "active_assessment": None,
        "latest_prediction": None,
        "practice_questions": [],
        "practice_revealed": {},
        "practice_ratings": {},
        "current_page": "Login / Register",
        "system_computation": None,
        "notification": None,
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


def clear_current_student():
    """Logs out or clears the current active student session."""
    st.session_state.current_student = None
    st.session_state.active_email = ""
    st.session_state.active_assessment = None
    st.session_state.latest_prediction = None
    st.session_state.practice_questions = []
    st.session_state.practice_revealed = {}
    st.session_state.system_computation = None
    st.session_state.current_page = "Login / Register"
