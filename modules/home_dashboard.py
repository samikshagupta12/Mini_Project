"""Home Dashboard Module displaying system metrics, computation analytics, and quick actions."""
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
from modules.computation_engine import compute_entire_program


def render_home_dashboard():
    st.title("🎓 AI-Powered Interview Preparation System")
    st.markdown("##### Real-Time Skill Assessment, Empirical Diagnosis, & Machine Learning Readiness Analytics")

    students_col = get_students_collection()
    assessments_col = get_assessments_collection()
    readiness_col = get_readiness_collection()

    current_student = get_current_student()

    # Guest Warning / Sign-In Prompt
    st.divider()
    if not current_student:
        st.warning("👋 **You are currently viewing as a Guest.**")
        st.write("Sign in or create a student account to evaluate your skill profile, predict interview readiness, and generate your custom learning roadmap.")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔐 Go to Sign In / Register Portal", use_container_width=True):
                st.session_state.current_page = "Login / Register"
                st.rerun()
        with c2:
            if st.button("⚡ Quick Demo Evaluation", use_container_width=True):
                st.session_state.current_page = "Login / Register"
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
        f"👋 Welcome, **{current_student.get('name')}**! | "
        f"Target Role: **{current_student.get('target_role')}** | "
        f"Degree: **{current_student.get('course')}** | "
        f"Email: `{current_student.get('email')}`"
    )

    # Compute & Retrieve live system-wide computation
    student_id = to_object_id(current_student.get("_id"))
    comp = compute_entire_program(student_id)
    st.session_state.system_computation = comp

    # Handle Empty State for brand new students with 0 assessments
    if not comp.get("has_data", False):
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

    # ----------------- SYSTEM-WIDE COMPUTED KPI METRICS -----------------
    st.subheader("🧮 Comprehensive Computed Metrics")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Overall Score", f"{comp['overall_average']}%")
    
    role_score = comp.get("role_weighted_score", comp["overall_average"])
    role_delta = f"{round(role_score - comp['overall_average'], 1):+0.1f}% vs. raw"
    m2.metric(f"Role-Weighted ({comp['target_role'][:10]}..)", f"{role_score}%", delta=role_delta)
    
    comp_index = comp.get("composite_index", 0.0)
    grade = comp.get("composite_grade", "N/A")
    m3.metric("Composite Readiness", f"{comp_index}% (Grade: {grade})")

    strong_cnt = len(comp.get("strong_topics", []))
    weak_cnt = len(comp.get("weak_topics", []))
    m4.metric("Competency Split", f"🟢 {strong_cnt} | 🔴 {weak_cnt}")

    ml_status = comp.get("ml_prediction", "Evaluating...")
    conf = comp.get("ml_confidence", 0)
    m5.metric("ML Readiness Tier", ml_status, f"{conf}% Conf.")

    st.divider()

    # Visualizations row: Topic-wise performance chart & Weak area summary
    col_v1, col_v2 = st.columns([3, 2])

    with col_v1:
        st.subheader("📊 Latest Topic Performance")
        scores_dict = comp.get("topic_scores", {})
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
        ax.axhline(80, color="#2ECC71", linestyle="--", alpha=0.5, label="Strong (80%)")
        ax.axhline(50, color="#E74C3C", linestyle="--", alpha=0.5, label="Weak (50%)")
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
        weak_topics = comp.get("weak_topics", [])
        if weak_topics:
            st.error(f"**Identified Weak Areas (< 50%):**\n\n" + "\n".join([f"- **{w}** (`{scores_dict.get(w, 0)}%`)" for w in weak_topics]))
        else:
            st.success("🎉 No topics currently below 50%! Focus on moderate topics and mock interview practice.")

        st.markdown("##### Quick Links:")
        st.write("1. 🛣️ **Personalized Roadmap:** Review targeted tasks and project exercises.")
        st.write("2. 🎯 **Interview Questions:** Practice curated technical questions.")
        st.write("3. 🤖 **ML Prediction:** Inspect Decision Tree feature weights.")

    st.divider()

    # Recomputation & Mathematical Formula Engine
    with st.expander("⚡ System Computation & Mathematical Engine (Click to inspect or recompute)"):
        st.markdown("#### Mathematical Formulations Applied Across the Program")
        st.latex(r"\text{Overall Average: } \bar{s} = \frac{1}{10} \sum_{i=1}^{10} s_i")
        st.latex(r"\text{Role-Weighted Score: } S_{\text{role}} = \sum_{i=1}^{10} w_i \cdot s_i \quad (\text{Target Role: } " + current_student.get("target_role", "Software Engineer") + r")")
        st.latex(r"\text{Composite Readiness: } I = 0.75 \cdot S_{\text{role}} + 0.25 \cdot \text{Roadmap \%}")
        st.caption("Note: Practice questions run in an interactive sandbox without saving answers to MongoDB. Readiness is derived from validated skill assessments (75%) and structured roadmap milestones (25%).")
        st.write(f"- **Roadmap Progress:** `{comp.get('roadmap_completion_pct', 0)}%` completed across `{comp.get('roadmap_tasks_count', 0)}` targeted topics.")
        
        if st.button("🔄 Recompute Entire Program State Now", use_container_width=True):
            with st.spinner("Recomputing metrics, ML predictions, and roadmap synchronization..."):
                new_comp = compute_entire_program(student_id, force_roadmap_refresh=True)
                st.session_state.system_computation = new_comp
            st.success("✅ Program state recomputed and synchronized with MongoDB!")
            st.rerun()

    st.divider()

    # Recent assessment history table
    st.subheader("🕒 Recent Assessment Activity")
    history = list(assessments_col.find({"student_id": student_id}).sort("created_at", -1))
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
