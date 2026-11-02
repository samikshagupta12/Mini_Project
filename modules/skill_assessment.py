"""Skill Assessment Input and Scoring Module."""
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
from config.settings import TOPICS
from database.collections import (
    get_assessments_collection,
    get_readiness_collection,
    get_roadmaps_collection,
    to_object_id,
    serialize_doc,
)
from utils.validators import validate_scores
from utils.helpers import calculate_assessment_metrics, get_status_color
from utils.session_manager import get_current_student
from ml.predict import predict_readiness


def render_skill_assessment_page():
    st.title("📝 Technical Skill Assessment")
    st.write("Rate your current knowledge level across the 10 core computer science and software engineering topics (0 to 100).")

    current_student = get_current_student()
    if not current_student:
        st.warning("⚠️ No active student profile selected. Please create or select a profile first.")
        if st.button("Go to Student Profile"):
            st.session_state.current_page = "Student Profile"
            st.rerun()
        return

    st.info(f"Submitting assessment for: **{current_student.get('name')}** ({current_student.get('email')}) — Target Role: **{current_student.get('target_role')}**")

    # Preset Quick Fill Buttons for easy academic demonstration & testing
    st.markdown("##### ⚡ Quick Fill Presets (For Demonstration)")
    p1, p2, p3, p4 = st.columns(4)
    if "temp_scores" not in st.session_state:
        st.session_state.temp_scores = {topic: 65 for topic in TOPICS}

    if p1.button("🟢 Advanced Ready (85+)", use_container_width=True):
        st.session_state.temp_scores = {
            "Python Programming": 88,
            "Data Structures and Algorithms": 85,
            "Object-Oriented Programming": 90,
            "Database Management Systems": 82,
            "SQL and MongoDB": 84,
            "Operating Systems": 80,
            "Computer Networks": 78,
            "Machine Learning": 86,
            "Data Analysis": 88,
            "Problem-Solving Skills": 90,
        }
        st.rerun()

    if p2.button("🟡 Balanced Intermediate (~65)", use_container_width=True):
        st.session_state.temp_scores = {
            "Python Programming": 72,
            "Data Structures and Algorithms": 62,
            "Object-Oriented Programming": 75,
            "Database Management Systems": 68,
            "SQL and MongoDB": 70,
            "Operating Systems": 58,
            "Computer Networks": 54,
            "Machine Learning": 60,
            "Data Analysis": 66,
            "Problem-Solving Skills": 64,
        }
        st.rerun()

    if p3.button("🔴 Beginner Needs Work (~38)", use_container_width=True):
        st.session_state.temp_scores = {
            "Python Programming": 50,
            "Data Structures and Algorithms": 35,
            "Object-Oriented Programming": 42,
            "Database Management Systems": 38,
            "SQL and MongoDB": 40,
            "Operating Systems": 32,
            "Computer Networks": 30,
            "Machine Learning": 25,
            "Data Analysis": 45,
            "Problem-Solving Skills": 36,
        }
        st.rerun()

    if p4.button("🔄 Reset to 50", use_container_width=True):
        st.session_state.temp_scores = {topic: 50 for topic in TOPICS}
        st.rerun()

    st.divider()

    with st.form("skill_assessment_form"):
        st.subheader("📊 Rate Your Knowledge (0 - 100)")
        entered_scores = {}
        
        col_left, col_right = st.columns(2)
        half = len(TOPICS) // 2

        with col_left:
            for topic in TOPICS[:half]:
                current_val = st.session_state.temp_scores.get(topic, 50)
                score = st.slider(
                    f"**{topic}**",
                    min_value=0,
                    max_value=100,
                    value=int(current_val),
                    step=1,
                    help=f"Score from 0 (beginner) to 100 (expert) for {topic}"
                )
                entered_scores[topic] = float(score)

        with col_right:
            for topic in TOPICS[half:]:
                current_val = st.session_state.temp_scores.get(topic, 50)
                score = st.slider(
                    f"**{topic}**",
                    min_value=0,
                    max_value=100,
                    value=int(current_val),
                    step=1,
                    help=f"Score from 0 (beginner) to 100 (expert) for {topic}"
                )
                entered_scores[topic] = float(score)

        st.caption("Thresholds: 🟢 Strong (80 - 100) | 🟡 Moderate (50 - 79) | 🔴 Weak (Below 50)")
        submitted = st.form_submit_button("🚀 Submit Assessment & Analyze", use_container_width=True)

        if submitted:
            is_valid, error_msgs = validate_scores(entered_scores)
            if not is_valid:
                for err in error_msgs:
                    st.error(err)
            else:
                # Calculate metrics
                metrics = calculate_assessment_metrics(entered_scores)
                
                assessments_col = get_assessments_collection()
                readiness_col = get_readiness_collection()
                roadmaps_col = get_roadmaps_collection()

                if assessments_col is None:
                    st.error("Database connection unavailable. Cannot save assessment.")
                    return

                student_id = to_object_id(current_student.get("_id"))
                now = datetime.now(timezone.utc)

                assessment_doc = {
                    "student_id": student_id,
                    "student_email": current_student.get("email"),
                    "topic_scores": entered_scores,
                    "average_score": metrics["overall_average"],
                    "strong_topics": metrics["strong_topics"],
                    "moderate_topics": metrics["moderate_topics"],
                    "weak_topics": metrics["weak_topics"],
                    "created_at": now,
                }

                # Save assessment to MongoDB
                res = assessments_col.insert_one(assessment_doc)
                assessment_id = res.inserted_id
                assessment_doc["_id"] = assessment_id

                # Run Entire Program Computation Pipeline
                try:
                    from modules.computation_engine import compute_entire_program
                    comp_results = compute_entire_program(student_id, force_roadmap_refresh=True)
                    st.session_state.system_computation = comp_results
                    if "ml_prediction" in comp_results:
                        st.session_state.latest_prediction = {
                            "predicted_readiness": comp_results["ml_prediction"],
                            "confidence": comp_results["ml_confidence"],
                            "probabilities": comp_results["ml_probabilities"],
                            "overall_average": comp_results["overall_average"],
                            "role_weighted_score": comp_results["role_weighted_score"],
                            "explanation": comp_results["ml_explanation"],
                            "recommendation": comp_results["ml_recommendation"],
                        }
                except Exception as e:
                    st.warning(f"Program computation note: {e}")

                # Update session state
                st.session_state.active_assessment = serialize_doc(assessment_doc)
                st.session_state.temp_scores = entered_scores

                st.success("🎉 Assessment submitted! Entire program metrics, roadmap, and ML predictions computed successfully.")

    # Display results if latest assessment is present
    latest = st.session_state.get("active_assessment")
    if latest:
        st.divider()
        st.subheader("🎯 Assessment Results Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Score", f"{latest.get('average_score', 0)}%")
        m2.metric("🟢 Strong Topics", len(latest.get("strong_topics", [])))
        m3.metric("🟡 Moderate Topics", len(latest.get("moderate_topics", [])))
        m4.metric("🔴 Weak Topics", len(latest.get("weak_topics", [])))

        # Score Breakdown Table
        st.markdown("##### Topic Breakdown")
        scores = latest.get("topic_scores", {})
        table_rows = []
        for t, s in scores.items():
            status = "🟢 Strong" if s >= 80 else ("🟡 Moderate" if s >= 50 else "🔴 Weak")
            table_rows.append({"Topic": t, "Score (%)": s, "Category": status})
        
        df_display = pd.DataFrame(table_rows).sort_values(by="Score (%)", ascending=False)
        st.dataframe(df_display, use_container_width=True, hide_index=True)

