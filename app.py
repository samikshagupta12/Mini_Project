"""
AI-POWERED INTERVIEW PREPARATION SYSTEM
Main Streamlit Application Entrypoint
"""
import streamlit as st
from config.settings import MONGODB_DATABASE, MONGODB_URI
from database.connection import check_connection, get_database
from database.collections import init_db_indexes
from utils.session_manager import init_session_state, get_current_student, set_current_student
from database.seed_questions import seed_database
from ml.predict import get_model_status

# Page configuration
st.set_page_config(
    page_title="AI-Powered Interview Preparation System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
init_session_state()

# Verify Database and Model State
is_db_connected, is_db_mock, db_status_msg = check_connection()
if is_db_connected:
    db = get_database()
    init_db_indexes(db)

# Auto-train ML Model if missing on first launch
model_ready, _ = get_model_status()

# ----------------- SIDEBAR NAVIGATION -----------------
st.sidebar.title("🎓 AI Interview Prep")


# Student Session Status in sidebar
current_student = get_current_student()
if current_student:
    st.sidebar.markdown(f"**Student:** `{current_student.get('name')}`")
    st.sidebar.caption(f"Role: {current_student.get('target_role')}")
    if st.sidebar.button("Switch / Logout", use_container_width=True):
        st.session_state.current_student = None
        st.session_state.active_email = ""
        st.session_state.active_assessment = None
        st.session_state.latest_prediction = None
        st.rerun()
else:
    st.sidebar.info("👤 No active student profile.")

st.sidebar.divider()

# Navigation menu
PAGES = [
    "Home Dashboard",
    "Student Profile",
    "Skill Assessment",
    "Strong and Weak Topic Analysis",
    "Interview Question Generator",
    "Personalized Learning Roadmap",
    "Interview Readiness Prediction",
    "Performance Analytics",
    "Assessment History",
    "Admin and Question Management",
]

# Sync navigation with session state
current_page_idx = 0
if st.session_state.current_page in PAGES:
    current_page_idx = PAGES.index(st.session_state.current_page)

selected_page = st.sidebar.radio(
    "Navigation",
    PAGES,
    index=current_page_idx,
)
st.session_state.current_page = selected_page

st.sidebar.divider()
st.sidebar.caption("Machine Learning: Decision Tree Classifier (Scikit-learn)\nDatabase: MongoDB / PyMongo")

# ----------------- PAGE ROUTING -----------------

if selected_page == "Home Dashboard":
    from modules.home_dashboard import render_home_dashboard
    render_home_dashboard()

elif selected_page == "Student Profile":
    from modules.student_profile import render_student_profile_page
    render_student_profile_page()

elif selected_page == "Skill Assessment":
    from modules.skill_assessment import render_skill_assessment_page
    render_skill_assessment_page()

elif selected_page == "Strong and Weak Topic Analysis":
    from modules.topic_analysis import render_topic_analysis_page
    render_topic_analysis_page()

elif selected_page == "Interview Question Generator":
    from modules.question_generator import render_question_generator_page
    render_question_generator_page()

elif selected_page == "Personalized Learning Roadmap":
    from modules.learning_roadmap import render_learning_roadmap_page
    render_learning_roadmap_page()

elif selected_page == "Interview Readiness Prediction":
    from modules.readiness_prediction import render_readiness_prediction_page
    render_readiness_prediction_page()

elif selected_page == "Performance Analytics":
    from modules.analytics import render_performance_analytics_page
    render_performance_analytics_page()

elif selected_page == "Assessment History":
    from modules.assessment_history import render_assessment_history_page
    render_assessment_history_page()

elif selected_page == "Admin and Question Management":
    from modules.admin_questions import render_admin_questions_page
    render_admin_questions_page()
