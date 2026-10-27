"""Student Profile Management Module."""
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
from utils.session_manager import get_current_student, set_current_student, clear_current_student


def render_student_profile_page():
    st.title("👤 Student Profile Management")
    st.write("Create or update your technical profile to receive tailored assessments, interview questions, and personalized roadmaps.")

    students_col = get_students_collection()
    if students_col is None:
        st.error("Database connection unavailable. Please check your MongoDB setup.")
        return

    # Fetch existing students for profile switching
    existing_students = list(students_col.find().sort("name", 1))
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Select Active Student Profile")
        options = ["-- Create New Student Profile --"] + [
            f"{s.get('name', 'Unknown')} ({s.get('email', '')})" for s in existing_students
        ]
        
        # Calculate default index based on current session
        current = get_current_student()
        current_email = current.get("email") if current else None
        default_idx = 0
        if current_email:
            for idx, s in enumerate(existing_students):
                if s.get("email") == current_email:
                    default_idx = idx + 1
                    break

        selected_opt = st.selectbox("Active Profile", options, index=default_idx)

    with col2:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh Profiles", use_container_width=True):
            st.rerun()

    # Determine mode: Create new or Edit existing
    editing_doc = None
    if selected_opt != "-- Create New Student Profile --":
        selected_email = selected_opt.split("(")[-1].rstrip(")")
        for s in existing_students:
            if s.get("email") == selected_email:
                editing_doc = s
                set_current_student(serialize_doc(s))
                break

    st.divider()

    # Form
    is_edit = editing_doc is not None
    st.subheader("✏️ " + ("Edit Profile" if is_edit else "Create New Student Profile"))

    with st.form("student_profile_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name *", value=editing_doc.get("name", "") if is_edit else "")
            email = st.text_input(
                "Email Address (Unique Identifier) *",
                value=editing_doc.get("email", "") if is_edit else "",
                disabled=is_edit,  # Email is immutable in edit mode
                help="Your email serves as your unique student ID."
            )
            education = st.selectbox(
                "Education Level *",
                EDUCATION_LEVELS,
                index=EDUCATION_LEVELS.index(editing_doc.get("education")) if is_edit and editing_doc.get("education") in EDUCATION_LEVELS else 0
            )
            course = st.text_input("Course / Degree Major *", value=editing_doc.get("course", "Computer Science") if is_edit else "Computer Science")

        with c2:
            target_role = st.selectbox(
                "Target Job Role *",
                JOB_ROLES,
                index=JOB_ROLES.index(editing_doc.get("target_role")) if is_edit and editing_doc.get("target_role") in JOB_ROLES else 0
            )
            experience_level = st.selectbox(
                "Experience Level *",
                EXPERIENCE_LEVELS,
                index=EXPERIENCE_LEVELS.index(editing_doc.get("experience_level")) if is_edit and editing_doc.get("experience_level") in EXPERIENCE_LEVELS else 0
            )
            preferred_language = st.selectbox(
                "Preferred Programming Language *",
                PROGRAMMING_LANGUAGES,
                index=PROGRAMMING_LANGUAGES.index(editing_doc.get("preferred_language")) if is_edit and editing_doc.get("preferred_language") in PROGRAMMING_LANGUAGES else 0
            )

        submit_label = "💾 Update Profile" if is_edit else "✨ Create Profile"
        submitted = st.form_submit_button(submit_label, use_container_width=True)

        if submitted:
            profile_data = {
                "name": name.strip(),
                "email": editing_doc.get("email") if is_edit else email.strip().lower(),
                "education": education,
                "course": course.strip(),
                "target_role": target_role,
                "experience_level": experience_level,
                "preferred_language": preferred_language,
            }

            is_valid, error_msgs = validate_student_profile(profile_data)
            if not is_valid:
                for err in error_msgs:
                    st.error(err)
            else:
                now = datetime.now(timezone.utc)
                if is_edit:
                    profile_data["updated_at"] = now
                    students_col.update_one(
                        {"_id": editing_doc["_id"]},
                        {"$set": profile_data}
                    )
                    updated_doc = students_col.find_one({"_id": editing_doc["_id"]})
                    set_current_student(serialize_doc(updated_doc))
                    st.success("Profile updated successfully!")
                    st.rerun()
                else:
                    # Check unique email
                    if students_col.find_one({"email": profile_data["email"]}):
                        st.error("A student with this email address already exists. Please choose a different email or select your profile above.")
                    else:
                        profile_data["created_at"] = now
                        profile_data["updated_at"] = now
                        res = students_col.insert_one(profile_data)
                        profile_data["_id"] = str(res.inserted_id)
                        set_current_student(serialize_doc(profile_data))
                        st.success(f"Profile created successfully for {profile_data['name']}!")
                        st.rerun()

    # Active profile summary card
    current = get_current_student()
    if current:
        st.divider()
        st.info(
            f"**Active Student Session:** {current.get('name')} | **Email:** {current.get('email')} | "
            f"**Target Role:** {current.get('target_role')} | **Degree:** {current.get('course')}"
        )

