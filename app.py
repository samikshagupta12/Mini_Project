"""
AI-POWERED INTERVIEW PREPARATION SYSTEM
Main Streamlit Application Entrypoint with Simpler Navigation,
Role-Based Access Control, Clear Database Status, and Automated Model Initialization.
"""
import streamlit as st
from config.settings import MONGODB_DATABASE, MONGODB_URI
from database.connection import check_connection, get_database, get_connection_details
from database.collections import init_db_indexes
from utils.session_manager import (
    init_session_state,
    get_current_student,
    get_current_admin,
    is_admin_logged_in,
    clear_current_student,
    clear_admin_session,
    clear_all_sessions,
)
from ml.predict import ensure_model_initialized

# Page configuration
st.set_page_config(
    page_title="AI-Powered Interview Preparation System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 1. Initialize Session State
init_session_state()

# 2. Database Connection Initialization & Indexing
is_db_connected, is_db_mock, db_status_msg = check_connection()
if is_db_connected:
    db = get_database()
    init_db_indexes(db)

# 3. Model Initialization (Automatically trains if artifacts are missing)
model_ready, model_meta, model_msg = ensure_model_initialized()

# ----------------- SIDEBAR HEADER & DB STATUS -----------------
st.sidebar.title("🎓 AI Interview Prep")

# Clear Database Connection Status Indicator
db_details = get_connection_details()
if db_details["is_connected"] and not db_details["is_mock"]:
    st.sidebar.success(f"{db_details['badge_text']}\n\nHost: `{db_details['host']}`")
elif db_details["is_mock"]:
    st.sidebar.warning(f"{db_details['badge_text']}")
    with st.sidebar.expander("ℹ️ Connection Details"):
        st.caption(db_details["instructions"])
else:
    st.sidebar.error(f"{db_details['badge_text']}")
    with st.sidebar.expander("⚠️ Database Offline"):
        st.caption(db_details["instructions"])

st.sidebar.divider()

# ----------------- AUTHENTICATION STATE & ROLE BADGE -----------------
current_student = get_current_student()
admin_active = is_admin_logged_in()
current_admin = get_current_admin()

if admin_active and current_admin:
    st.sidebar.markdown(f"**🛡️ Role:** `Administrator`")
    st.sidebar.markdown(f"**👤 Admin:** `{current_admin.get('name', 'Admin')}`")
    st.sidebar.caption(f"Email: {current_admin.get('email')}")
    if st.sidebar.button("🚪 Sign Out (Admin)", use_container_width=True):
        clear_admin_session()
        st.session_state.current_page = "Login / Register"
        st.rerun()

elif current_student:
    st.sidebar.markdown(f"**👤 Student:** `{current_student.get('name')}`")
    st.sidebar.caption(f"Role: {current_student.get('target_role')}")
    
    comp = st.session_state.get("system_computation")
    if comp and comp.get("composite_grade"):
        st.sidebar.markdown(f"**Readiness:** `{comp.get('composite_grade')} ({comp.get('composite_index')}%)`")

    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        clear_current_student()
        st.session_state.current_page = "Login / Register"
        st.rerun()
else:
    st.sidebar.info("🔒 **Status:** Unauthenticated")
    st.sidebar.caption("Sign in to access personalized student preparation and analytics.")

st.sidebar.divider()

# ----------------- SIMPLER, ROLE-AWARE NAVIGATION STRUCTURE -----------------

# Case 1: Unauthenticated Guest -> Strictly require login before viewing student info
if not current_student and not admin_active:
    st.sidebar.markdown("### 🧭 Navigation")
    guest_pages = ["Login / Register", "Admin Access Portal"]
    
    # Map selection
    current_idx = 1 if st.session_state.current_page == "Admin and Question Management" else 0
    guest_choice = st.sidebar.radio(
        "Select Portal",
        guest_pages,
        index=current_idx,
    )
    if guest_choice == "Login / Register":
        st.session_state.current_page = "Login / Register"
    else:
        st.session_state.current_page = "Admin and Question Management"

# Case 2: Administrator Session -> Streamlined Admin Controls
elif admin_active:
    st.sidebar.markdown("### 🛡️ Administrator Hub")
    admin_pages = [
        "Admin and Question Management",
        "Home Dashboard (Preview)",
    ]
    current_idx = 1 if st.session_state.current_page == "Home Dashboard" else 0
    admin_choice = st.sidebar.radio("Admin Options", admin_pages, index=current_idx)
    if admin_choice == "Admin and Question Management":
        st.session_state.current_page = "Admin and Question Management"
    else:
        st.session_state.current_page = "Home Dashboard"

# Case 3: Authenticated Student -> Streamlined Category-Filtered Navigation
else:
    st.sidebar.markdown("### 🧭 Student Workspace")
    
    # Simplified Category Switcher for uncluttered navigation
    CATEGORY_MAP = {
        "📋 All Modules": [
            "Home Dashboard",
            "Student Profile",
            "Skill Assessment",
            "Strong and Weak Topic Analysis",
            "Interview Question Generator",
            "Personalized Learning Roadmap",
            "Interview Readiness Prediction",
            "Performance Analytics",
            "Assessment History",
        ],
        "🏠 Core Hub": [
            "Home Dashboard",
            "Student Profile",
        ],
        "📝 Assessments & Diagnostics": [
            "Skill Assessment",
            "Strong and Weak Topic Analysis",
            "Assessment History",
        ],
        "🎯 Practice & Roadmap": [
            "Interview Question Generator",
            "Personalized Learning Roadmap",
        ],
        "🤖 ML & Analytics": [
            "Interview Readiness Prediction",
            "Performance Analytics",
        ],
    }

    selected_cat = st.sidebar.selectbox(
        "View Section",
        list(CATEGORY_MAP.keys()),
        index=0,
        key="nav_category_selector"
    )

    available_pages = CATEGORY_MAP[selected_cat]

    # Ensure current page is in available list or reset to first
    if st.session_state.current_page not in available_pages:
        st.session_state.current_page = available_pages[0]

    current_page_idx = available_pages.index(st.session_state.current_page)
    selected_page = st.sidebar.radio(
        "Modules",
        available_pages,
        index=current_page_idx,
    )
    st.session_state.current_page = selected_page

st.sidebar.divider()

# Display Model Status Pill in Sidebar
if model_ready and model_meta:
    acc = model_meta.get("evaluation_metrics", {}).get("accuracy", 0.0)
    st.sidebar.caption(f"🤖 **Decision Tree ML:** Active (`{acc:.1%}` Accuracy)")
else:
    st.sidebar.caption("🤖 **Decision Tree ML:** Offline")

st.sidebar.caption("Database: MongoDB / PyMongo")

# ----------------- PAGE ROUTING & ACCESS PROTECTION -----------------
target_page = st.session_state.current_page

# Enforce login protection for student-specific pages
STUDENT_ONLY_PAGES = (
    "Home Dashboard",
    "Student Profile",
    "Skill Assessment",
    "Strong and Weak Topic Analysis",
    "Interview Question Generator",
    "Personalized Learning Roadmap",
    "Interview Readiness Prediction",
    "Performance Analytics",
    "Assessment History",
)

if target_page in STUDENT_ONLY_PAGES and not current_student and not admin_active:
    # Force Login page for unauthenticated access attempts
    from modules.login import render_login_page
    render_login_page()

elif target_page == "Login / Register":
    from modules.login import render_login_page
    render_login_page()

elif target_page in ("Home Dashboard", "Home Dashboard (Preview)"):
    from modules.home_dashboard import render_home_dashboard
    render_home_dashboard()

elif target_page == "Student Profile":
    from modules.student_profile import render_student_profile_page
    render_student_profile_page()

elif target_page == "Skill Assessment":
    from modules.skill_assessment import render_skill_assessment_page
    render_skill_assessment_page()

elif target_page == "Strong and Weak Topic Analysis":
    from modules.topic_analysis import render_topic_analysis_page
    render_topic_analysis_page()

elif target_page == "Interview Question Generator":
    from modules.question_generator import render_question_generator_page
    render_question_generator_page()

elif target_page == "Personalized Learning Roadmap":
    from modules.learning_roadmap import render_learning_roadmap_page
    render_learning_roadmap_page()

elif target_page == "Interview Readiness Prediction":
    from modules.readiness_prediction import render_readiness_prediction_page
    render_readiness_prediction_page()

elif target_page == "Performance Analytics":
    from modules.analytics import render_performance_analytics_page
    render_performance_analytics_page()

elif target_page == "Assessment History":
    from modules.assessment_history import render_assessment_history_page
    render_assessment_history_page()

elif target_page in ("Admin and Question Management", "Admin Access Portal"):
    from modules.admin_questions import render_admin_questions_page
    render_admin_questions_page()
