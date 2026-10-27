"""Strong and Weak Topic Analysis Module."""
import streamlit as st
import pandas as pd
from database.collections import get_assessments_collection, to_object_id
from utils.helpers import calculate_assessment_metrics
from utils.session_manager import get_current_student


def render_topic_analysis_page():
    st.title("🔍 Strong and Weak Topic Analysis")
    st.write("Detailed diagnostic breakdown of your technical competencies, performance rankings, and personalized learning priorities.")

    current_student = get_current_student()
    if not current_student:
        st.warning("⚠️ Please select or create a student profile to view topic analysis.")
        return

    assessments_col = get_assessments_collection()
    if assessments_col is None:
        st.error("Database unavailable.")
        return

    student_id = to_object_id(current_student.get("_id"))
    # Fetch recent assessments ordered by date desc
    history = list(assessments_col.find({"student_id": student_id}).sort("created_at", -1).limit(5))

    if not history:
        st.info("ℹ️ No assessments found for this student. Please complete a Skill Assessment first.")
        if st.button("Take Skill Assessment"):
            st.session_state.current_page = "Skill Assessment"
            st.rerun()
        return

    latest = history[0]
    scores = latest.get("topic_scores", {})
    metrics = calculate_assessment_metrics(scores)

    # Top highlight cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Top Subject", f"{metrics['highest_topic']}", f"{metrics['highest_score']}%")
    c2.metric("Critical Area", f"{metrics['lowest_topic']}", f"{metrics['lowest_score']}%", delta_color="inverse")
    c3.metric("Strong Topics", len(metrics["strong_topics"]))
    c4.metric("Weak Topics", len(metrics["weak_topics"]), delta_color="inverse")

    st.divider()

    # Topic Rankings Table
    st.subheader("🏆 Technical Competency Rankings")
    df_ranks = pd.DataFrame(metrics["rankings"])
    df_ranks.columns = ["Rank", "Topic", "Score (%)", "Classification"]
    
    # Styled badges
    def format_cat(val):
        if val == "Strong":
            return "🟢 Strong"
        elif val == "Moderate":
            return "🟡 Moderate"
        return "🔴 Weak (Priority)"
    
    df_ranks["Classification"] = df_ranks["Classification"].apply(format_cat)
    st.dataframe(df_ranks, use_container_width=True, hide_index=True)

    st.divider()

    # Immediate Improvement Needed
    st.subheader("⚠️ Topics Requiring Immediate Improvement")
    weak = metrics["weak_topics"]
    if weak:
        st.error(f"The following {len(weak)} topics scored below 50% and are primary blockers for technical interviews:")
        for w in weak:
            score_val = scores.get(w, 0)
            col_a, col_b = st.columns([3, 1])
            col_a.markdown(f"- **{w}** (Score: `{score_val}%`)")
            col_b.caption("Priority: High")
    else:
        st.success("🎉 Excellent! None of your evaluated technical topics scored below the 50% threshold.")

    # Historical Comparison (if more than 1 assessment exists)
    st.divider()
    st.subheader("📈 Assessment Comparison (Current vs. Previous)")
    if len(history) > 1:
        prev = history[1]
        prev_scores = prev.get("topic_scores", {})
        
        comp_data = []
        for t in scores.keys():
            curr_s = scores.get(t, 0)
            prev_s = prev_scores.get(t, 0)
            diff = curr_s - prev_s
            comp_data.append({
                "Topic": t,
                "Previous Score": f"{prev_s}%",
                "Latest Score": f"{curr_s}%",
                "Change": f"{'+' if diff > 0 else ''}{diff}%",
                "Progress": "🟢 Improved" if diff > 0 else ("🔴 Dropped" if diff < 0 else "⚪ Unchanged")
            })
        df_comp = pd.DataFrame(comp_data)
        st.dataframe(df_comp, use_container_width=True, hide_index=True)
    else:
        st.info("Complete another assessment in the future to view topic-by-topic progress and delta comparisons over time.")

    # Actionable Recommendations
    st.divider()
    st.subheader("💡 Strategic Recommendations")
    target_role = current_student.get("target_role", "Software Engineer")
    st.write(f"Tailored specifically for your target role as **{target_role}**:")

    recs = []
    if scores.get("Data Structures and Algorithms", 0) < 70:
        recs.append("🧠 **DSA Reinforcement:** Allocate 45 minutes daily to LeetCode Easy/Medium problems (Two Pointers, Sliding Window, Trees).")
    if scores.get("SQL and MongoDB", 0) < 70 or scores.get("Database Management Systems", 0) < 70:
        recs.append("🗄️ **Database Practice:** Practice complex SQL joins, aggregation pipelines in MongoDB, and indexing strategies.")
    if scores.get("Operating Systems", 0) < 60 or scores.get("Computer Networks", 0) < 60:
        recs.append("💻 **Core CS Fundamentals:** Review OS concurrency (deadlocks, threads) and Network protocols (TCP vs UDP, TLS handshake).")
    if scores.get("Machine Learning", 0) < 70 and target_role in ("Data Scientist", "Machine Learning Engineer"):
        recs.append("🤖 **ML Foundations:** Study bias-variance tradeoff, decision tree pruning, and loss functions.")
    if not recs:
        recs.append("🚀 **Mock Interviews:** Your baseline scores are strong across all evaluated categories! Focus on full-length timed mock technical interviews.")

    for r in recs:
        st.markdown(r)

