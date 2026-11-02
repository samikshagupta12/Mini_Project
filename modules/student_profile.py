"""Student Profile Management Module with Password Update & Role Synchronization."""
from datetime import datetime, timezone
import streamlit as st
from config.settings import (
    JOB_ROLES,
    EXPERIENCE_LEVELS,
    EDUCATION_LEVELS,
    PROGRAMMING_LANGUAGES,
)
from database.collections import (
    get_students_collection,
    to_object_id,
    serialize_doc,
)
from utils.validators import validate_student_profile
from utils.auth import hash_password
from utils.session_manager import get_current_student, set_current_student, clear_current_student


def render_student_profile_page():
    st.title("👤 Student Profile Management")
    st.write("Manage your academic credentials, target career trajectory, and account preferences.")

    students_col = get_students_collection()
    if students_col is None:
        st.error("Database connection unavailable. Please check your MongoDB setup.")
        return

    current = get_current_student()

    if not current:
        st.warning("⚠️ No active student profile logged in.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔐 Go to Sign In / Register", use_container_width=True):
                st.session_state.current_page = "Login / Register"
                st.rerun()
        return

    # Fetch latest student record from database
    student_id = to_object_id(current.get("_id"))
    fresh_doc = students_col.find_one({"_id": student_id}) if student_id else None
    if fresh_doc:
        current = serialize_doc(fresh_doc)
        set_current_student(current)

    # Active Profile Banner
    st.info(
        f"**Logged In As:** {current.get('name')} | **Email:** `{current.get('email')}` | "
        f"**Target Role:** {current.get('target_role')} | **Degree:** {current.get('course')}"
    )

    tab_profile, tab_security, tab_switch = st.tabs(["📋 Edit Profile Details", "🔒 Change Password", "🔄 Switch Profile (Evaluator Mode)"])

    # --- TAB 1: EDIT PROFILE ---
    with tab_profile:
        with st.form("edit_profile_form"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Full Name *", value=current.get("name", ""))
                email = st.text_input(
                    "Email Address (Unique Identifier)",
                    value=current.get("email", ""),
                    disabled=True,
                    help="Your email is your permanent unique student identifier."
                )
                curr_edu = current.get("education", EDUCATION_LEVELS[0])
                edu_idx = EDUCATION_LEVELS.index(curr_edu) if curr_edu in EDUCATION_LEVELS else 0
                education = st.selectbox("Education Level *", EDUCATION_LEVELS, index=edu_idx)

                course = st.text_input("Course / Degree Major *", value=current.get("course", "Computer Science"))

            with c2:
                curr_role = current.get("target_role", JOB_ROLES[0])
                role_idx = JOB_ROLES.index(curr_role) if curr_role in JOB_ROLES else 0
                target_role = st.selectbox("Target Job Role *", JOB_ROLES, index=role_idx)

                curr_exp = current.get("experience_level", EXPERIENCE_LEVELS[0])
                exp_idx = EXPERIENCE_LEVELS.index(curr_exp) if curr_exp in EXPERIENCE_LEVELS else 0
                experience_level = st.selectbox("Experience Level *", EXPERIENCE_LEVELS, index=exp_idx)

                curr_lang = current.get("preferred_language", PROGRAMMING_LANGUAGES[0])
                lang_idx = PROGRAMMING_LANGUAGES.index(curr_lang) if curr_lang in PROGRAMMING_LANGUAGES else 0
                preferred_language = st.selectbox("Preferred Programming Language *", PROGRAMMING_LANGUAGES, index=lang_idx)

            submitted = st.form_submit_button("💾 Save Profile Changes", use_container_width=True)

            if submitted:
                updated_data = {
                    "name": name.strip(),
                    "email": current.get("email"),
                    "education": education,
                    "course": course.strip(),
                    "target_role": target_role,
                    "experience_level": experience_level,
                    "preferred_language": preferred_language,
                }

                is_valid, error_msgs = validate_student_profile(updated_data)
                if not is_valid:
                    for err in error_msgs:
                        st.error(err)
                else:
                    now = datetime.now(timezone.utc)
                    updated_data["updated_at"] = now
                    students_col.update_one({"_id": student_id}, {"$set": updated_data})
                    
                    fresh = students_col.find_one({"_id": student_id})
                    set_current_student(serialize_doc(fresh))

                    # Trigger re-computation of role-weighted score and roadmap with new role
                    try:
                        from modules.computation_engine import compute_entire_program
                        compute_entire_program(student_id, force_roadmap_refresh=(target_role != curr_role))
                    except Exception:
                        pass

                    st.success("✅ Profile updated successfully! System computations synchronized.")
                    st.rerun()

    # --- TAB 2: CHANGE PASSWORD ---
    with tab_security:
        st.markdown("#### Update Account Password")
        with st.form("change_password_form"):
            new_pw = st.text_input("New Password", type="password", placeholder="Min. 6 characters")
            confirm_pw = st.text_input("Confirm New Password", type="password", placeholder="Repeat new password")
            pw_submitted = st.form_submit_button("🔒 Update Password", use_container_width=True)

            if pw_submitted:
                if not new_pw or len(new_pw) < 6:
                    st.error("Password must be at least 6 characters long.")
                elif new_pw != confirm_pw:
                    st.error("Passwords do not match. Please verify and retry.")
                else:
                    new_hash = hash_password(new_pw)
                    students_col.update_one(
                        {"_id": student_id},
                        {"$set": {"password_hash": new_hash, "updated_at": datetime.now(timezone.utc)}}
                    )
                    st.success("🎉 Password updated successfully! Your account is secured with salted PBKDF2 hashing.")

    # --- TAB 3: SWITCH PROFILE (EVALUATOR MODE) ---
    with tab_switch:
        st.markdown("#### Quick Profile Switcher (Academic Evaluation)")
        st.caption("Instructors and evaluators can switch between existing student records stored in MongoDB:")
        
        existing_students = list(students_col.find().sort("name", 1))
        options = [f"{s.get('name', 'Unknown')} ({s.get('email', '')})" for s in existing_students]
        
        current_email = current.get("email")
        default_idx = 0
        for idx, s in enumerate(existing_students):
            if s.get("email") == current_email:
                default_idx = idx
                break

        selected_opt = st.selectbox("Select Account", options, index=default_idx)
        
        c_sw1, c_sw2 = st.columns(2)
        with c_sw1:
            if st.button("🔄 Switch to Selected Account", use_container_width=True):
                selected_email = selected_opt.split("(")[-1].rstrip(")")
                target_doc = students_col.find_one({"email": selected_email})
                if target_doc:
                    set_current_student(serialize_doc(target_doc))
                    try:
                        from modules.computation_engine import compute_entire_program
                        compute_entire_program(target_doc["_id"])
                    except Exception:
                        pass
                    st.success(f"Switched to {target_doc.get('name')}!")
                    st.rerun()

        with c_sw2:
            if st.button("🚪 Sign Out to Login Portal", use_container_width=True):
                clear_current_student()
                st.rerun()
