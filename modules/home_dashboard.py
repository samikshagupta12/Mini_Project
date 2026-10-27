"""Home Dashboard Module displaying system metrics, student summary, and quick actions."""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from database.collections import (
    get_assessments_collection,
    get_readiness_collection,
    get_students_collection,
    to_object_id,
)
from utils.session_manager import get_current_student, set_current_student


def render_home_dashboard():
    st.title("🎓 AI-Powered Interview Preparation System")
    st.markdown("##### Real-Time Skill Assessment, Weak Area Diagnosis, & Machine Learning Readiness Analytics")

    students_col = get_students_collection()
    assessments_col = get_assessments_collection()
    readiness_col = get_readiness_collection()

    current_student = get_current_student()

    # Student Profile Selector / Welcome Bar
    st.divider()
    if not current_student:
        # Prompt to select or create a profile
        st.warning("👋 **Welcome! You are currently browsing as a Guest.**")
        st.write("To track your skill assessment history, receive a customized study roadmap, and predict your interview readiness, please create or select your student profile.")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("👤 Go to Student Profile Setup", use_container_width=True):
                st.session_state.current_page = "Student Profile"
                st.rerun()
        with c2:
            if st.button("📝 Quick Skill Assessment", use_container_width=True):
                st.session_state.current_page = "Skill Assessment"
                st.rerun()

        # Display platform overview
        st.divider()
        st.subheader("🎯 System Capabilities")
        g1, g2, g3 = st.columns(3)
        g1.info("📊 **Skill Diagnostics**\n\nRate 10 core CS topics and detect technical blind spots.")
        g2.info("🤖 **ML Readiness Prediction**\n\nScikit-learn Decision Tree trained to predict interview outcome readiness.")
        g3.info("🛣️ **Tailored Roadmaps**\n\nPrioritized learning roadmaps and curated technical questions.")
        return

    # Student Profile Summary Header
    st.success(
        f"👋 Welcome back, **{current_student.get('name')}**! | "
        f"Target Role: **{current_student.get('target_role')}** | "
        f"Language: **{current_student.get('preferred_language')}** | "
        f"Email: `{current_student.get('email')}`"
    )

    # Fetch student's real data from MongoDB
    student_id = to_object_id(current_student.get("_id"))
    history = list(assessments_col.find({"student_id": student_id}).sort("created_at", -1))
    latest_pred = readiness_col.find_one({"student_id": student_id}, sort=[("created_at", -1)]) if readiness_col is not None else None

    # Handle Empty State for brand new students
    if not history:
        st.info("ℹ️ You have not completed any skill assessments yet! Complete your first assessment to unlock comprehensive analytics and readiness predictions.")
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("🚀 Take Your First Skill Assessment", use_container_width=True):
                st.session_state.current_page = "Skill Assessment"
                st.rerun()
        with col_act2:
            if st.button("🎯 Practice Technical Interview Questions", use_container_width=True):
                st.session_state.current_page = "Interview Question Generator"
                st.rerun()
        return

    latest = history[0]
    avg_score = latest.get("average_score", 0)
    strong_topics = latest.get("strong_topics", [])
    weak_topics = latest.get("weak_topics", [])
    pred_status = latest_pred.get("predicted_readiness", "Not Evaluated") if latest_pred else "Not Evaluated"
    pred_conf = latest_pred.get("confidence", 0) if latest_pred else 0

    # Metric Cards
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Assessments Taken", len(history))
    m2.metric("Overall Average", f"{avg_score}%")
    m3.metric("🟢 Strong Topics", len(strong_topics))
    m4.metric("🔴 Weak Topics", len(weak_topics), delta_color="inverse")
    m5.metric("ML Readiness", pred_status)

    st.divider()

    # Visualizations row: Topic-wise performance chart & Weak area summary
    col_v1, col_v2 = st.columns([3, 2])

    with col_v1:
        st.subheader("📊 Latest Topic Performance")
        scores_dict = latest.get("topic_scores", {})
        topics = list(scores_dict.keys())
        scores = list(scores_dict.values())

        fig, ax = plt.subplots(figsize=(7, 3.8))
        colors = ["#2ECC71" if s >= 80 else ("#F39C12" if s >= 50 else "#E74C3C") for s in scores]
        bars = ax.bar(range(len(topics)), scores, color=colors, edgecolor="#2C3E50", linewidth=0.7)
        ax.set_ylim(0, 105)
        ax.set_ylabel("Score (%)", fontsize=9)
        ax.set_xticks(range(len(topics)))
        short_labels = [t.replace(" and ", "/").replace("Programming", "Prog.").replace("Management Systems", "Mgt.") for t in topics]
        ax.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=8)
        ax.axhline(80, color="#2ECC71", linestyle="--", alpha=0.5)
        ax.axhline(50, color="#E74C3C", linestyle="--", alpha=0.5)
        ax.grid(axis="y", linestyle=":", alpha=0.5)

        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{int(h)}", xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 2), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7.5, fontweight="bold")

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col_v2:
        st.subheader("🎯 Critical Action Areas")
        if weak_topics:
            st.error(f"**Identified Weak Areas (< 50%):**\n\n" + "\n".join([f"- **{w}** (`{scores_dict.get(w, 0)}%`)" for w in weak_topics]))
        else:
            st.success("🎉 No topics currently below 50%! Keep refining moderate topics.")

        st.markdown("##### Recommended Next Steps:")
        st.write("1. 🛣️ Review your **Personalized Learning Roadmap** to tackle priority topics.")
        st.write("2. 🎯 Practice questions in **Interview Question Generator** for your weak areas.")
        st.write("3. 🔄 Retake the assessment after completing study modules.")

    st.divider()

    # Recent assessment history table
    st.subheader("🕒 Recent Assessment Activity")
    recent_rows = []
    for idx, h in enumerate(history[:5]):
        created = h.get("created_at")
        date_str = created.strftime("%Y-%m-%d %H:%M") if hasattr(created, "strftime") else str(created)
        recent_rows.append({
            "Attempt": len(history) - idx,
            "Date": date_str,
            "Average Score": f"{h.get('average_score', 0)}%",
            "Strong Topics": len(h.get("strong_topics", [])),
            "Weak Topics": len(h.get("weak_topics", [])),
        })
    st.dataframe(pd.DataFrame(recent_rows), use_container_width=True, hide_index=True)

