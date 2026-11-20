"""
AI-POWERED INTERVIEW PREPARATION SYSTEM
Main Streamlit Application Entrypoint with Dual Database Architecture:
- Mode 1: In-Memory Demo Mode (mongomock) - Default, Zero Installation Required.
- Mode 2: Real MongoDB Mode (Local mongod or MongoDB Atlas) - Permanent Disk Storage.
Ensures zero crashes, streamlined navigation, role-based access control, and complete feature coverage.
"""
import streamlit as st
from config.settings import MONGODB_DATABASE, MONGODB_URI
from database.connection import (
    check_connection,
    get_database,
    get_connection_details,
    reset_connection,
    test_and_set_mongo_uri,
)
from database.collections import init_db_indexes
from utils.session_manager import (
    init_session_state,
    get_current_student,
    get_current_admin,
    is_admin_logged_in,
    is_demo_mode,
    set_demo_mode,
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

# 2. Database Connection Initialization & Automatic Indexing
is_db_connected, is_db_mock, db_status_msg = check_connection()
if is_db_connected:
    db = get_database()
    init_db_indexes(db)

# 3. Model Initialization (Automatically trains if artifacts are missing)
model_ready, model_meta, model_msg = ensure_model_initialized()

# ----------------- SIDEBAR HEADER & EXPLICIT DB STATUS -----------------
st.sidebar.title("🎓 AI Interview Prep")

db_details = get_connection_details()

# STATUS DISPLAY 1: REAL MONGODB CONNECTED & PERSISTENT
if db_details["is_connected"] and not db_details["is_mock"]:
    st.sidebar.success(f"{db_details['badge_text']}\n\nHost: `{db_details['host']}`\n\nDatabase: `{db_details['database']}`")
    st.sidebar.caption("💾 **Permanent Storage:** Active (All data saved to disk/cloud)")
    
    with st.sidebar.expander("🎭 Switch to Demo Mode"):
        st.caption("Need an isolated in-memory environment for a presentation or grading?")
        if st.button("Enable Demo Mode (In-Memory)", key="enable_demo_btn", use_container_width=True):
            set_demo_mode(True)
            reset_connection()
            st.rerun()

# STATUS DISPLAY 2: DEMO MODE ACTIVE (IN-MEMORY MOCK)
else:
    st.sidebar.warning(f"{db_details['badge_text']}")
    st.sidebar.caption(db_details["storage_warning"])
    
    with st.sidebar.expander("🔌 Connect Real MongoDB / Atlas"):
        st.caption("Need permanent storage? Connect to a local MongoDB daemon or MongoDB Atlas cloud cluster.")
        uri_input = st.text_input(
            "MongoDB Connection URI",
            value=st.session_state.get("custom_mongo_uri", MONGODB_URI),
            key="side_uri_input",
            help="e.g. mongodb://localhost:27017 or mongodb+srv://user:pass@cluster0.mongodb.net/?retryWrites=true&w=majority"
        )
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("Connect", key="side_connect_btn", use_container_width=True):
                with st.spinner("Testing connection..."):
                    ok, conn_msg = test_and_set_mongo_uri(uri_input)
                if ok:
                    st.success(conn_msg)
                    set_demo_mode(False)
                    st.rerun()
                else:
                    st.error(conn_msg)
        with col_c2:
            if st.button("Retry Local", key="side_retry_btn", use_container_width=True):
                set_demo_mode(False)
                reset_connection()
                st.rerun()

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

# ----------------- STREAMLINED NAVIGATION -----------------

# Case 1: Unauthenticated Guest -> Direct access to Login/Register or Admin Access
if not current_student and not admin_active:
    st.sidebar.markdown("### 🧭 Navigation")
    guest_pages = ["Login / Register", "Admin Access Portal"]
    current_idx = 1 if st.session_state.current_page in ("Admin and Question Management", "Admin Access Portal") else 0
    guest_choice = st.sidebar.radio("Select Portal", guest_pages, index=current_idx)
    if guest_choice == "Login / Register":
        st.session_state.current_page = "Login / Register"
    else:
        st.session_state.current_page = "Admin and Question Management"

# Case 2: Administrator Session -> Administrator Controls
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

# Case 3: Authenticated Student -> Category-Filtered Navigation
else:
    st.sidebar.markdown("### 🧭 Student Workspace")
    
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

# Display Model Status in Sidebar
if model_ready and model_meta:
    acc = model_meta.get("evaluation_metrics", {}).get("accuracy", 0.0)
    st.sidebar.caption(f"🤖 **Decision Tree ML:** Active (`{acc:.1%}` Accuracy)")
else:
    st.sidebar.caption("🤖 **Decision Tree ML:** Offline")

st.sidebar.caption("Storage: MongoDB & In-Memory Demo")


# ----------------- NON-BLOCKING TOP NOTIFICATION BANNERS -----------------
# If Real MongoDB was attempted but offline, display a helpful notice without blocking the user
if db_details.get("real_mongo_failed", False):
    st.warning(
        f"⚠️ **Real MongoDB is Offline:** The system could not connect to `{db_details['host']}`. "
        "The application has automatically activated **Demo Mode (In-Memory)** with full functionality. "
        "All 10 modules, assessments, and ML models are active. Note that data will not persist to disk after server shutdown."
    )
    with st.expander("🛠️ How to Connect Real MongoDB or Use Cloud Atlas"):
        guide = db_details.get("beginner_guide", {})
        st.write(guide.get("what_happened", "Could not reach MongoDB daemon."))
        st.markdown("**Local Windows Command (Run in Admin PowerShell):**")
        st.code("net start MongoDB", language="powershell")
        st.markdown("**Cloud MongoDB Atlas (Free Cluster):**")
        st.caption("Paste your connection string into the sidebar expander or into your `.env` file.")
        if st.button("🚀 Dismiss Banner & Continue in Demo Mode", use_container_width=True):
            set_demo_mode(True)
            reset_connection()
            st.rerun()

# ----------------- PAGE ROUTING & ACCESS PROTECTION -----------------
target_page = st.session_state.current_page

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
