"""Performance Analytics and Matplotlib Visualizations Module."""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from database.collections import get_assessments_collection, to_object_id
from utils.session_manager import get_current_student
from ml.model_evaluation import get_evaluation_metrics
from utils.helpers import get_status_color

# Professional Matplotlib plot configuration
plt.style.use("default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 10


def render_performance_analytics_page():
    st.title("📊 Performance Analytics & Visualizations")
    st.write("Comprehensive data visualizations evaluating topic proficiencies, longitudinal progress, and machine learning diagnostics.")

    current_student = get_current_student()
    if not current_student:
        st.warning("⚠️ Please select or create a student profile to view performance analytics.")
        return

    assessments_col = get_assessments_collection()
    if assessments_col is None:
        st.error("Database connection unavailable.")
        return

    student_id = to_object_id(current_student.get("_id"))
    history = list(assessments_col.find({"student_id": student_id}).sort("created_at", 1))

    if not history:
        st.info("ℹ️ No assessment data available to visualize. Please complete an assessment first.")
        if st.button("Take Skill Assessment"):
            st.session_state.current_page = "Skill Assessment"
            st.rerun()
        return

    latest = history[-1]
    topic_scores = latest.get("topic_scores", {})
    topics = list(topic_scores.keys())
    scores = list(topic_scores.values())

    # --- Chart 1 & Chart 2 ---
    st.subheader("1. Topic-wise Performance & Competency Rankings")
    c1, c2 = st.columns(2)

    with c1:
        # Chart 1: Bar chart for topic-wise skill scores
        fig1, ax1 = plt.subplots(figsize=(7, 4.5))
        colors = ["#2ECC71" if s >= 80 else ("#F39C12" if s >= 50 else "#E74C3C") for s in scores]
        bars = ax1.bar(range(len(topics)), scores, color=colors, edgecolor="#2C3E50", linewidth=0.8)
        
        ax1.set_title("Topic-wise Skill Scores (%)", fontsize=12, fontweight="bold", pad=12)
        ax1.set_ylabel("Score (%)", fontsize=10)
        ax1.set_xticks(range(len(topics)))
        # Short labels for x-axis
        short_labels = [t.replace(" and ", "/").replace("Programming", "Prog.").replace("Management Systems", "Mgt.") for t in topics]
        ax1.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=8)
        ax1.set_ylim(0, 105)
        ax1.axhline(80, color="#2ECC71", linestyle="--", alpha=0.6, label="Strong Threshold (80%)")
        ax1.axhline(50, color="#E74C3C", linestyle="--", alpha=0.6, label="Weak Threshold (50%)")
        ax1.legend(loc="upper right", fontsize=8)
        ax1.grid(axis="y", linestyle=":", alpha=0.6)
        
        # Add score labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(f"{int(height)}",
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 2), textcoords="offset points",
                         ha="center", va="bottom", fontsize=8, fontweight="bold")
        
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

    with c2:
        # Chart 2: Horizontal bar chart ranking strong and weak topics
        sorted_pairs = sorted(zip(topics, scores), key=lambda x: x[1])
        s_topics = [p[0] for p in sorted_pairs]
        s_scores = [p[1] for p in sorted_pairs]
        s_colors = ["#2ECC71" if s >= 80 else ("#F39C12" if s >= 50 else "#E74C3C") for s in s_scores]

        fig2, ax2 = plt.subplots(figsize=(7, 4.5))
        bars2 = ax2.barh(range(len(s_topics)), s_scores, color=s_colors, edgecolor="#2C3E50", linewidth=0.8)
        ax2.set_title("Topics Ranked from Lowest to Highest", fontsize=12, fontweight="bold", pad=12)
        ax2.set_xlabel("Score (%)", fontsize=10)
        ax2.set_yticks(range(len(s_topics)))
        ax2.set_yticklabels(s_topics, fontsize=8)
        ax2.set_xlim(0, 105)
        ax2.grid(axis="x", linestyle=":", alpha=0.6)

        for bar in bars2:
            width = bar.get_width()
            ax2.annotate(f"{int(width)}%",
                         xy=(width, bar.get_y() + bar.get_height() / 2),
                         xytext=(3, 0), textcoords="offset points",
                         ha="left", va="center", fontsize=8, fontweight="bold")

        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    st.divider()

    # --- Chart 3 & Chart 4 ---
    st.subheader("2. Distribution & Longitudinal Progress")
    c3, c4 = st.columns(2)

    with c3:
        # Chart 3: Doughnut chart showing distribution of strong, moderate, and weak topics
        strong_count = sum(1 for s in scores if s >= 80)
        moderate_count = sum(1 for s in scores if 50 <= s < 80)
        weak_count = sum(1 for s in scores if s < 50)
        
        counts = [strong_count, moderate_count, weak_count]
        labels = [f"Strong ({strong_count})", f"Moderate ({moderate_count})", f"Weak ({weak_count})"]
        colors_doughnut = ["#2ECC71", "#F39C12", "#E74C3C"]

        # Filter out 0 counts to prevent matplotlib errors
        valid_indices = [i for i, c in enumerate(counts) if c > 0]
        f_counts = [counts[i] for i in valid_indices]
        f_labels = [labels[i] for i in valid_indices]
        f_colors = [colors_doughnut[i] for i in valid_indices]

        fig3, ax3 = plt.subplots(figsize=(6, 4.5))
        if f_counts:
            wedges, texts, autotexts = ax3.pie(
                f_counts,
                labels=f_labels,
                autopct="%1.1f%%",
                startangle=140,
                colors=f_colors,
                wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
                textprops=dict(fontsize=9)
            )
            for at in autotexts:
                at.set_fontweight("bold")
            ax3.set_title("Topic Category Distribution", fontsize=12, fontweight="bold", pad=12)
        else:
            ax3.text(0.5, 0.5, "No Score Data", ha="center", va="center")
            
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)

    with c4:
        # Chart 4: Line chart showing progress over time
        fig4, ax4 = plt.subplots(figsize=(6, 4.5))
        dates = [f"Assmt {i+1}" for i in range(len(history))]
        avg_scores = [h.get("average_score", 0) for h in history]

        ax4.plot(dates, avg_scores, marker="o", color="#3498DB", linewidth=2.5, markersize=7, label="Overall Average")
        ax4.set_title("Assessment Score Progression Over Time", fontsize=12, fontweight="bold", pad=12)
        ax4.set_ylabel("Average Score (%)", fontsize=10)
        ax4.set_xlabel("Assessment Sequence", fontsize=10)
        ax4.set_ylim(0, 105)
        ax4.grid(True, linestyle=":", alpha=0.6)

        for x, y in zip(dates, avg_scores):
            ax4.annotate(f"{y}%", xy=(x, y), xytext=(0, 7), textcoords="offset points",
                         ha="center", fontsize=9, fontweight="bold", color="#2980B9")

        plt.tight_layout()
        st.pyplot(fig4)
        plt.close(fig4)

    st.divider()

    # --- Chart 5 & Chart 6 ---
    st.subheader("3. Assessment Comparison & Machine Learning Diagnostics")
    c5, c6 = st.columns(2)

    with c5:
        # Chart 5: Comparison of previous vs current assessment
        fig5, ax5 = plt.subplots(figsize=(7, 4.5))
        if len(history) >= 2:
            prev_scores_dict = history[-2].get("topic_scores", {})
            prev_scores = [prev_scores_dict.get(t, 0) for t in topics]
            curr_scores = [topic_scores.get(t, 0) for t in topics]

            x_indices = np.arange(len(topics))
            width = 0.38

            ax5.bar(x_indices - width/2, prev_scores, width=width, label="Previous Assmt", color="#95A5A6", edgecolor="#2C3E50")
            ax5.bar(x_indices + width/2, curr_scores, width=width, label="Latest Assmt", color="#3498DB", edgecolor="#2C3E50")

            ax5.set_title("Comparison: Previous vs. Latest Assessment", fontsize=12, fontweight="bold", pad=12)
            ax5.set_ylabel("Score (%)", fontsize=10)
            ax5.set_xticks(x_indices)
            ax5.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=8)
            ax5.set_ylim(0, 105)
            ax5.legend(loc="upper right", fontsize=8)
            ax5.grid(axis="y", linestyle=":", alpha=0.6)
        else:
            ax5.text(0.5, 0.5, "Complete at least 2 assessments\nto unlock comparative chart", ha="center", va="center", fontsize=11, color="#7F8C8D")
            ax5.set_title("Assessment Comparison", fontsize=12, fontweight="bold", pad=12)
            ax5.set_xticks([])
            ax5.set_yticks([])

        plt.tight_layout()
        st.pyplot(fig5)
        plt.close(fig5)

    with c6:
        # Chart 6: Confusion Matrix visualization for the Decision Tree model
        ml_meta = get_evaluation_metrics()
        fig6, ax6 = plt.subplots(figsize=(6, 4.5))

        if ml_meta and "confusion_matrix" in ml_meta:
            cm = np.array(ml_meta["confusion_matrix"]["matrix"])
            labels = ["Needs Impr.", "Partially Ready", "Interview Ready"]
            
            im = ax6.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
            ax6.set_title("Decision Tree Confusion Matrix (Test Set)", fontsize=12, fontweight="bold", pad=12)
            
            # Colorbar
            fig6.colorbar(im, ax=ax6, fraction=0.046, pad=0.04)
            tick_marks = np.arange(len(labels))
            ax6.set_xticks(tick_marks)
            ax6.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
            ax6.set_yticks(tick_marks)
            ax6.set_yticklabels(labels, fontsize=8)
            ax6.set_ylabel("True Category", fontsize=9)
            ax6.set_xlabel("Predicted Category", fontsize=9)

            # Annotate cells
            thresh = cm.max() / 2.0
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    ax6.text(j, i, format(cm[i, j], "d"),
                             ha="center", va="center",
                             color="white" if cm[i, j] > thresh else "black",
                             fontweight="bold")

            # Display accuracy badge below chart
            metrics_dict = ml_meta.get("evaluation_metrics", {})
            acc = metrics_dict.get("accuracy", 0) * 100
            f1 = metrics_dict.get("f1_weighted", 0)
            st.caption(f"🎯 Model Accuracy on Test Set: **{acc:.1f}%** | Weighted F1: **{f1:.3f}**")
        else:
            ax6.text(0.5, 0.5, "ML Model Metrics Not Available", ha="center", va="center")
            ax6.set_xticks([])
            ax6.set_yticks([])

        plt.tight_layout()
        st.pyplot(fig6)
        plt.close(fig6)

