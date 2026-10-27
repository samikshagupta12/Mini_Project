"""Assessment History and Longitudinal Tracking Module."""
import streamlit as st
import pandas as pd
from database.collections import get_assessments_collection, to_object_id
from utils.session_manager import get_current_student


def render_assessment_history_page():
    st.title("📜 Assessment History")
    st.write("Review your historical assessment records, track score trajectories, and inspect previous performance snapshots.")

    current_student = get_current_student()
    if not current_student:
        st.warning("⚠️ Please select or create a student profile to view assessment history.")
        return

    assessments_col = get_assessments_collection()
    if assessments_col is None:
        st.error("Database connection unavailable.")
        return

    student_id = to_object_id(current_student.get("_id"))
    history = list(assessments_col.find({"student_id": student_id}).sort("created_at", -1))

    if not history:
        st.info("ℹ️ No assessment records found for this student. Complete an assessment to start building your history.")
        if st.button("Take First Skill Assessment"):
            st.session_state.current_page = "Skill Assessment"
            st.rerun()
        return

    st.subheader(f"Total Assessments Completed: {len(history)}")

    # Summary table
    table_data = []
    for idx, item in enumerate(history):
        created = item.get("created_at")
        date_str = created.strftime("%Y-%m-%d %H:%M UTC") if hasattr(created, "strftime") else str(created)
        table_data.append({
            "Attempt #": len(history) - idx,
            "Date Submitted": date_str,
            "Average Score (%)": item.get("average_score", 0),
            "Strong Topics (>=80)": len(item.get("strong_topics", [])),
            "Weak Topics (<50)": len(item.get("weak_topics", [])),
            "Assessment ID": str(item.get("_id")),
        })

    df_hist = pd.DataFrame(table_data)
    st.dataframe(df_hist, use_container_width=True, hide_index=True)

    st.divider()

    # Detailed Inspection of a Specific Attempt
    st.subheader("🔍 Inspect Past Assessment Details")
    attempt_options = [f"Attempt #{row['Attempt #']} ({row['Date Submitted']})" for row in table_data]
    selected_attempt = st.selectbox("Select Assessment Attempt to Inspect", attempt_options)

    if selected_attempt:
        selected_idx = attempt_options.index(selected_attempt)
        selected_record = history[selected_idx]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Average Score", f"{selected_record.get('average_score', 0)}%")
        c2.metric("Strong Topics", len(selected_record.get("strong_topics", [])))
        c3.metric("Weak Topics", len(selected_record.get("weak_topics", [])))

        st.markdown("##### Topic Breakdown")
        scores = selected_record.get("topic_scores", {})
        detail_rows = [
            {
                "Topic": t,
                "Score (%)": s,
                "Status": "🟢 Strong" if s >= 80 else ("🟡 Moderate" if s >= 50 else "🔴 Weak")
            }
            for t, s in scores.items()
        ]
        df_detail = pd.DataFrame(detail_rows).sort_values(by="Score (%)", ascending=False)
        st.dataframe(df_detail, use_container_width=True, hide_index=True)

    st.write("")
    if st.button("🔄 Take New Assessment"):
        st.session_state.current_page = "Skill Assessment"
        st.rerun()

