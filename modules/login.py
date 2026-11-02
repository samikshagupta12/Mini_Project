"""
Beautiful, Modern Student Login, Registration, and Demo Portal.
Features salted PBKDF2 authentication, input validation, and 1-click evaluation.
"""
import streamlit as st
from config.settings import (
    JOB_ROLES,
    EXPERIENCE_LEVELS,
    EDUCATION_LEVELS,
    PROGRAMMING_LANGUAGES,
)
from utils.auth import authenticate_student, register_student, get_or_create_demo_student
from utils.session_manager import set_current_student


def render_login_page():
    """Renders a modern, visually stunning authentication & registration portal."""
    
    # Modern Custom CSS for the Authentication Portal
    st.markdown(
        """
        <style>
        .login-hero-container {
            text-align: center;
            padding: 1.5rem 1rem 1rem 1rem;
            margin-bottom: 1rem;
        }
        .login-title {
            font-size: 2.3rem;
            font-weight: 800;
            background: linear-gradient(120deg, #3498DB, #9B59B6, #2ECC71);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.3rem;
        }
        .login-subtitle {
            font-size: 1.05rem;
            color: #8892b0;
            margin-bottom: 1.2rem;
        }
        .pill-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            margin: 0.2rem 0.3rem;
            font-size: 0.8rem;
            font-weight: 600;
            border-radius: 9999px;
            background: rgba(52, 152, 219, 0.12);
            color: #3498db;
            border: 1px solid rgba(52, 152, 219, 0.25);
        }
        .auth-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Hero Branding Header
    st.markdown(
        """
        <div class="login-hero-container">
            <div class="login-title">🎓 AI-Powered Interview Preparation</div>
            <div class="login-subtitle">
                Master technical interviews with empirical skill gap analysis, personalized roadmaps, and Decision Tree readiness prediction.
            </div>
            <div>
                <span class="pill-badge">🤖 Scikit-Learn Decision Tree</span>
                <span class="pill-badge">🗄️ MongoDB Cloud & Local</span>
                <span class="pill-badge">📊 10 Core CS Topics</span>
                <span class="pill-badge">🛣️ Dynamic Roadmaps</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_center = st.columns([1, 6, 1])[1]

    with col_center:
        auth_tabs = st.tabs(["🔐 Sign In", "✨ Create Student Account", "⚡ Instant Demo Evaluation"])

        # ----------------- TAB 1: LOGIN -----------------
        with auth_tabs[0]:
            st.markdown("#### Welcome Back")
            st.caption("Sign in with your student email and password to access your personalized dashboard.")

            with st.form("login_form", clear_on_submit=False):
                login_email = st.text_input(
                    "Email Address",
                    placeholder="student@university.edu",
                    key="login_email_input"
                )
                login_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password_input"
                )
                
                remember_me = st.checkbox("Remember this session", value=True)
                login_submitted = st.form_submit_button("🚀 Sign In to Dashboard", use_container_width=True)

                if login_submitted:
                    if not login_email.strip() or not login_password:
                        st.error("Please enter both email address and password.")
                    else:
                        with st.spinner("Authenticating credentials..."):
                            success, student_doc, msg = authenticate_student(login_email, login_password)
                        
                        if success and student_doc:
                            set_current_student(student_doc)
                            st.session_state.current_page = "Home Dashboard"
                            
                            # Run initial system-wide computation for the logged in student
                            try:
                                from modules.computation_engine import compute_entire_program
                                compute_entire_program(student_doc["_id"])
                            except Exception:
                                pass

                            st.success(f"🎉 {msg} Welcome, {student_doc.get('name')}!")
                            st.rerun()
                        else:
                            st.error(f"Authentication failed: {msg}")

        # ----------------- TAB 2: REGISTER -----------------
        with auth_tabs[1]:
            st.markdown("#### Create Student Profile")
            st.caption("Register to receive tailored skill diagnostics, custom roadmaps, and predictive analytics.")

            with st.form("register_form", clear_on_submit=False):
                r_c1, r_c2 = st.columns(2)
                with r_c1:
                    reg_name = st.text_input("Full Name *", placeholder="Jane Doe")
                    reg_email = st.text_input("Student Email *", placeholder="jane@university.edu")
                    reg_password = st.text_input("Create Password *", type="password", placeholder="Min. 6 characters")
                    reg_education = st.selectbox("Education Level *", EDUCATION_LEVELS)
                    reg_course = st.text_input("Course / Degree Major *", value="Computer Science and Engineering")

                with r_c2:
                    reg_confirm_password = st.text_input("Confirm Password *", type="password", placeholder="Confirm your password")
                    reg_role = st.selectbox("Target Job Role *", JOB_ROLES)
                    reg_exp = st.selectbox("Experience Level *", EXPERIENCE_LEVELS)
                    reg_lang = st.selectbox("Preferred Programming Language *", PROGRAMMING_LANGUAGES)

                register_submitted = st.form_submit_button("✨ Register & Launch Preparation", use_container_width=True)

                if register_submitted:
                    if reg_password != reg_confirm_password:
                        st.error("Passwords do not match. Please re-enter your password.")
                    else:
                        profile_dict = {
                            "name": reg_name.strip(),
                            "email": reg_email.strip(),
                            "education": reg_education,
                            "course": reg_course.strip(),
                            "target_role": reg_role,
                            "experience_level": reg_exp,
                            "preferred_language": reg_lang,
                        }

                        with st.spinner("Creating student profile in MongoDB..."):
                            success, student_doc, errors = register_student(profile_dict, reg_password)

                        if success and student_doc:
                            set_current_student(student_doc)
                            st.session_state.current_page = "Skill Assessment"
                            st.success(f"🎉 Registration successful! Welcome to the platform, {student_doc.get('name')}.")
                            st.rerun()
                        else:
                            for err in errors:
                                st.error(err)

        # ----------------- TAB 3: QUICK DEMO EVALUATION -----------------
        with auth_tabs[2]:
            st.markdown("#### ⚡ 1-Click Evaluation Mode")
            st.info(
                "Evaluators, professors, and reviewers can instantly log in with pre-configured student archetypes to test all 10 modules, "
                "analytics visualizations, and Decision Tree predictions without manually filling out forms."
            )

            demo_col1, demo_col2 = st.columns(2)

            with demo_col1:
                st.markdown("##### 🟢 Prepared Candidate Profile")
                st.caption("**Candidate:** Alice Johnson (Software Engineer)\n\n**Status:** High DSA, OOP & Problem Solving scores. Predicts *Interview Ready*.")
                if st.button("🚀 Sign In as Alice (Ready)", use_container_width=True):
                    with st.spinner("Loading demo profile & computing state..."):
                        demo_student = get_or_create_demo_student("ready")
                        set_current_student(demo_student)
                        from modules.computation_engine import compute_entire_program
                        compute_entire_program(demo_student["_id"])
                        st.session_state.current_page = "Home Dashboard"
                        st.success("Signed in as Alice Johnson!")
                        st.rerun()

            with demo_col2:
                st.markdown("##### 🟡 Improving Candidate Profile")
                st.caption("**Candidate:** Bob Smith (Data Scientist)\n\n**Status:** Strong ML/Python, but weak core CS. Demonstrates roadmap triggers.")
                if st.button("🌱 Sign In as Bob (Developing)", use_container_width=True):
                    with st.spinner("Loading demo profile & computing state..."):
                        demo_student = get_or_create_demo_student("improving")
                        set_current_student(demo_student)
                        from modules.computation_engine import compute_entire_program
                        compute_entire_program(demo_student["_id"])
                        st.session_state.current_page = "Home Dashboard"
                        st.success("Signed in as Bob Smith!")
                        st.rerun()

            st.write("---")
            if st.button("👁️ Explore as Guest / Read-Only", use_container_width=True):
                st.session_state.current_page = "Home Dashboard"
                st.rerun()

