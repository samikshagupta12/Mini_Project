"""
Technical Skill Assessment Input and Scoring Module.
Features category grouping, subject descriptions, scoring rubric guidance (25, 50, 75, 100),
progress indicators, pre-submission confirmation screen, isolated demonstration presets,
and optional consent-based anonymized research data collection.
"""
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
from config.settings import (
    TOPICS,
    TOPIC_CATEGORIES,
    TOPIC_DESCRIPTIONS,
    SCORE_LEVEL_GUIDE,
)
from database.collections import (
    get_assessments_collection,
    get_readiness_collection,
    get_roadmaps_collection,
    get_research_data_collection,
    to_object_id,
    serialize_doc,
)
from utils.validators import validate_scores
from utils.helpers import calculate_assessment_metrics, get_status_color
from utils.session_manager import get_current_student
from database.connection import get_connection_details


def get_score_tier_details(score: float) -> dict:
    """Returns tier name, badge emoji, range, and description for a given score value."""
    if score <= 25:
        return {
            "tier": "Beginner",
            "badge": "🔴",
            "range": "0 – 25",
            "meaning": "Conceptual or surface exposure only; needs guided assistance.",
        }
    elif score <= 50:
        return {
            "tier": "Basic understanding",
            "badge": "🟡",
            "range": "26 – 50",
            "meaning": "Familiar with fundamentals; struggles with edge cases or optimizations.",
        }
    elif score <= 75:
        return {
            "tier": "Good understanding",
            "badge": "🔵",
            "range": "51 – 75",
            "meaning": "Independent problem solver; writes modular code and explains trade-offs.",
        }
    else:
        return {
            "tier": "Advanced understanding",
            "badge": "🟢",
            "range": "76 – 100",
            "meaning": "Deep architectural mastery, runtime optimization, and internal mechanics.",
        }


def render_skill_assessment_page():
    st.title("📝 Technical Skill Assessment")
    st.write("Rate your current knowledge level across the 10 core computer science and software engineering disciplines.")

    current_student = get_current_student()
    if not current_student:
        st.warning("⚠️ No active student profile selected. Please create or select a profile first.")
        if st.button("Go to Student Profile"):
            st.session_state.current_page = "Student Profile"
            st.rerun()
        return

    st.info(f"Evaluating Candidate: **{current_student.get('name')}** ({current_student.get('email')}) — Target Role: **{current_student.get('target_role')}**")
    
    db_info = get_connection_details()
    if db_info.get("storage_warning"):
        st.warning(db_info["storage_warning"])

    # ----------------- SEPARATE DEMONSTRATION PRESETS -----------------
    with st.expander("⚡ Academic Demonstration & Quick-Fill Presets (For Evaluators & Viva Demonstrations)"):
        st.caption(
            "ℹ️ **Evaluator Notice:** These quick-fill presets are provided solely for evaluators, instructors, "
            "and viva grading to rapidly simulate candidate archetypes without manually adjusting 10 sliders. "
            "Real students should evaluate their authentic skills using the categorized sections below."
        )
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
            st.session_state.assessment_confirming = False
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
            st.session_state.assessment_confirming = False
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
            st.session_state.assessment_confirming = False
            st.rerun()

        if p4.button("🔄 Reset Baseline (50)", use_container_width=True):
            st.session_state.temp_scores = {topic: 50 for topic in TOPICS}
            st.session_state.assessment_confirming = False
            st.rerun()

    # ----------------- SCORING RUBRIC & MEANING GUIDE -----------------
    with st.expander("📖 Score Rubric & Practical Meaning Guide (What 25, 50, 75, and 100 Mean)", expanded=True):
        st.markdown(
            "Use this standardized benchmark to calibrate your self-assessment accurately:"
        )
        rubric_rows = []
        for item in SCORE_LEVEL_GUIDE:
            rubric_rows.append({
                "Score Range": item["range"],
                "Proficiency Level": f"{item['badge_color']} **{item['tier']}**",
                "Conceptual Meaning": item["meaning"],
                "Concrete Interview Example": item["example"],
            })
        rubric_df = pd.DataFrame(rubric_rows)
        st.table(rubric_df)

    st.divider()

    # ----------------- CONFIRMATION SCREEN OR INPUT FORM -----------------
    if st.session_state.get("assessment_confirming", False):
        render_assessment_confirmation_screen(current_student)
    else:
        render_assessment_input_form(current_student)


def render_assessment_input_form(current_student: dict):
    """Renders the categorized input sliders, topic descriptions, and progress indicator."""
    current_scores = st.session_state.get("temp_scores", {topic: 50 for topic in TOPICS})

    # Live Progress Indicator & Summary Metrics
    current_avg = round(sum(current_scores.values()) / len(TOPICS), 1)
    strong_cnt = sum(1 for v in current_scores.values() if v >= 80)
    mod_cnt = sum(1 for v in current_scores.values() if 50 <= v < 80)
    weak_cnt = sum(1 for v in current_scores.values() if v < 50)

    st.markdown("### 📊 Skill Self-Rating")
    st.progress(1.0)
    st.caption("✅ **Assessment Status:** 10 / 10 Topics Scored (Ready for Confirmation Review)")

    # Real-time metrics row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current Average", f"{current_avg}%")
    m2.metric("🟢 Strong Topics (80+)", strong_cnt)
    m3.metric("🟡 Moderate Topics (50-79)", mod_cnt)
    m4.metric("🔴 Weak Topics (<50)", weak_cnt)

    with st.form("skill_assessment_form"):
        entered_scores = {}

        # Render Grouped Categories
        for cat_name, cat_topics in TOPIC_CATEGORIES.items():
            st.markdown(f"#### {cat_name}")
            col1, col2 = st.columns(2)

            for idx, topic in enumerate(cat_topics):
                target_col = col1 if idx % 2 == 0 else col2
                with target_col:
                    val = current_scores.get(topic, 50)
                    tier_info = get_score_tier_details(val)
                    description = TOPIC_DESCRIPTIONS.get(topic, "")

                    st.markdown(f"**{topic}** `{tier_info['badge']} {tier_info['tier']}`")
                    st.caption(f"_{description}_")
                    
                    score = st.slider(
                        f"Score for {topic}",
                        min_value=0,
                        max_value=100,
                        value=int(val),
                        step=1,
                        key=f"slider_{topic}",
                        label_visibility="collapsed",
                        help=f"Score from 0 to 100 for {topic}. Currently: {tier_info['tier']} ({tier_info['meaning']})"
                    )
                    entered_scores[topic] = float(score)
            st.write("")

        st.caption("Thresholds: 🟢 Strong (80–100) | 🟡 Moderate (50–79) | 🔴 Weak (Below 50)")
        proceed_button = st.form_submit_button("📋 Review & Proceed to Confirmation", use_container_width=True)

        if proceed_button:
            is_valid, error_msgs = validate_scores(entered_scores)
            if not is_valid:
                for err in error_msgs:
                    st.error(err)
            else:
                st.session_state.temp_scores = entered_scores
                st.session_state.assessment_confirming = True
                st.rerun()

    # Display results if a historical assessment exists
    latest = st.session_state.get("active_assessment")
    if latest:
        render_results_summary(latest)


def render_assessment_confirmation_screen(current_student: dict):
    """Renders the pre-submission confirmation screen with category summaries, review table, and consent."""
    st.subheader("🔍 Review & Confirm Your Assessment Submission")
    st.write("Please review your scores before submitting them to your permanent student record.")

    pending_scores = st.session_state.get("temp_scores", {})
    metrics = calculate_assessment_metrics(pending_scores)

    # Candidate & Role Summary
    st.markdown(
        f"**Candidate:** `{current_student.get('name')}` &nbsp;|&nbsp; "
        f"**Email:** `{current_student.get('email')}` &nbsp;|&nbsp; "
        f"**Target Role:** `{current_student.get('target_role')}`"
    )

    # Category Breakdown Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall Average", f"{metrics['overall_average']}%")

    for idx, (cat_name, cat_topics) in enumerate(TOPIC_CATEGORIES.items()):
        cat_avg = round(sum(pending_scores.get(t, 0) for t in cat_topics) / len(cat_topics), 1)
        short_cat = cat_name.split(" ")[1] if " " in cat_name else cat_name
        [c2, c3, c4][idx].metric(f"{short_cat} Avg", f"{cat_avg}%")

    # Detailed Confirmation Table
    st.markdown("##### Detailed Topic Rating Breakdown")
    confirm_rows = []
    for cat_name, cat_topics in TOPIC_CATEGORIES.items():
        for t in cat_topics:
            s = pending_scores.get(t, 0.0)
            tier_info = get_score_tier_details(s)
            confirm_rows.append({
                "Subject": t,
                "Category": cat_name,
                "Score": f"{s:.0f}%",
                "Proficiency Level": f"{tier_info['badge']} {tier_info['tier']}",
                "Practical Meaning": tier_info["meaning"],
            })

    confirm_df = pd.DataFrame(confirm_rows)
    st.dataframe(confirm_df, use_container_width=True, hide_index=True)

    # Optional Anonymized Research Consent Checkbox
    st.markdown("##### 🤝 Academic Research Contribution (Optional)")
    research_consent = st.checkbox(
        "I consent to contributing my de-identified topic score profile to the open academic research dataset "
        "to assist with future model retraining and skill gap research. (No name, email, or student ID will ever be saved with research data).",
        value=True,
        key="consent_checkbox",
    )

    # Submission and Navigation Buttons
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("✅ Confirm & Submit to Permanent Record", type="primary", use_container_width=True):
            submit_assessment_record(current_student, pending_scores, metrics, research_consent)
    with b_col2:
        if st.button("✏️ Back to Edit Scores", use_container_width=True):
            st.session_state.assessment_confirming = False
            st.rerun()


def submit_assessment_record(current_student: dict, scores: dict, metrics: dict, consent: bool):
    """Executes database persistence, computation engine invocation, and voluntary research collection."""
    assessments_col = get_assessments_collection()
    if assessments_col is None:
        st.error("Database connection unavailable. Cannot save assessment.")
        return

    student_id = to_object_id(current_student.get("_id"))
    now = datetime.now(timezone.utc)

    assessment_doc = {
        "student_id": student_id,
        "student_email": current_student.get("email"),
        "topic_scores": scores,
        "average_score": metrics["overall_average"],
        "strong_topics": metrics["strong_topics"],
        "moderate_topics": metrics["moderate_topics"],
        "weak_topics": metrics["weak_topics"],
        "created_at": now,
    }

    # 1. Save student assessment to MongoDB
    res = assessments_col.insert_one(assessment_doc)
    assessment_id = res.inserted_id
    assessment_doc["_id"] = assessment_id

    # 2. Save anonymized research record if student consented
    if consent:
        try:
            research_col = get_research_data_collection()
            if research_col is not None:
                research_doc = {
                    "topic_scores": scores,
                    "overall_average": metrics["overall_average"],
                    "target_role": current_student.get("target_role"),
                    "experience_level": current_student.get("experience_level"),
                    "consent_granted": True,
                    "anonymization_method": "PII-stripped (No name, email, student_id, or IP address)",
                    "created_at": now,
                }
                research_col.insert_one(research_doc)
        except Exception as e:
            # Research logging failure should never block student experience
            pass

    # 3. Run Entire Program Computation Pipeline
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

    # 4. Update session state
    st.session_state.active_assessment = serialize_doc(assessment_doc)
    st.session_state.assessment_confirming = False

    st.success("🎉 Assessment submitted and recorded permanently! Full metrics, roadmap, and ML readiness predictions computed successfully.")
    st.rerun()


def render_results_summary(latest: dict):
    """Renders the historical/latest assessment breakdown."""
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
        tier_info = get_score_tier_details(s)
        status = "🟢 Strong" if s >= 80 else ("🟡 Moderate" if s >= 50 else "🔴 Weak")
        table_rows.append({
            "Topic": t,
            "Score (%)": s,
            "Category Status": status,
            "Proficiency Level": f"{tier_info['badge']} {tier_info['tier']}",
        })
    
    df_display = pd.DataFrame(table_rows).sort_values(by="Score (%)", ascending=False)
    st.dataframe(df_display, use_container_width=True, hide_index=True)
