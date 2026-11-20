"""
Interview Readiness Checker using Decision Tree Machine Learning.
Features academic demonstration notices, multi-metric evaluation (Holdout + 5-Fold Cross-Validation),
per-class classification reports, statistical confidence reframing (avoiding false hiring guarantees),
and voluntary anonymized outcome collection for continuous academic research.
"""
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
from database.collections import (
    get_assessments_collection,
    get_readiness_collection,
    get_research_data_collection,
    to_object_id,
    serialize_doc,
)
from utils.session_manager import get_current_student
from ml.predict import predict_readiness, get_model_status
from config.settings import READINESS_CLASSES


def render_readiness_prediction_page():
    st.title("🤖 Interview Readiness Prediction")
    st.write("Supervised Machine Learning evaluation of your technical readiness using a Scikit-learn Decision Tree Classifier.")

    # ----------------- ACADEMIC DEMONSTRATION NOTICE -----------------
    st.info(
        "🎓 **Academic Demonstration Prototype:** This machine learning component demonstrates the practical application of a "
        "supervised CART Decision Tree Classifier trained on pedagogical skill benchmarks. It provides empirical guidance "
        "for skill gap remediation and is strictly intended for academic and coursework demonstration."
    )

    current_student = get_current_student()
    if not current_student:
        st.warning("⚠️ Please select or create a student profile to view readiness predictions.")
        return

    # Check ML Model Status
    model_loaded, metadata = get_model_status()
    if not model_loaded:
        st.error("Decision Tree model is currently unavailable.")
        if st.button("Train Model Now"):
            from ml.train_model import train_decision_tree_model
            with st.spinner("Training Decision Tree Classifier..."):
                train_decision_tree_model(save=True)
            st.success("Model trained successfully!")
            st.rerun()
        return

    assessments_col = get_assessments_collection()
    readiness_col = get_readiness_collection()

    if assessments_col is None:
        st.error("Database connection unavailable.")
        return

    student_id = to_object_id(current_student.get("_id"))
    latest_assessment = assessments_col.find_one({"student_id": student_id}, sort=[("created_at", -1)])

    if not latest_assessment:
        st.info("ℹ️ No assessment found. Please complete the Skill Assessment first to evaluate your interview readiness.")
        if st.button("Take Skill Assessment"):
            st.session_state.current_page = "Skill Assessment"
            st.rerun()
        return

    topic_scores = latest_assessment.get("topic_scores", {})
    
    # Run Prediction
    try:
        prediction_result = predict_readiness(topic_scores)
    except Exception as e:
        st.error(f"Error executing ML model: {e}")
        return

    pred_class = prediction_result["prediction"]
    confidence = prediction_result["confidence"]
    probs = prediction_result["probabilities"]
    overall_avg = prediction_result["overall_average"]

    # Save to MongoDB readiness_predictions collection if not recorded for this assessment
    if readiness_col is not None:
        existing = readiness_col.find_one({
            "student_id": student_id,
            "assessment_id": latest_assessment["_id"]
        })
        if not existing:
            readiness_doc = {
                "student_id": student_id,
                "assessment_id": latest_assessment["_id"],
                "predicted_readiness": pred_class,
                "confidence": confidence,
                "probabilities": probs,
                "overall_average": overall_avg,
                "model_version": "DecisionTree-v1.0",
                "created_at": datetime.now(timezone.utc),
            }
            readiness_col.insert_one(readiness_doc)

    # ----------------- PREDICTED STATUS BANNER -----------------
    st.divider()
    if pred_class == "Interview Ready":
        st.success(f"### 🎉 Predicted Status: **{pred_class}** (Archetype Alignment: {confidence:.1f}%)")
    elif pred_class == "Intermediate / Partially Ready":
        st.warning(f"### ⚡ Predicted Status: **{pred_class}** (Archetype Alignment: {confidence:.1f}%)")
    else:
        st.error(f"### ⚠️ Predicted Status: **{pred_class}** (Archetype Alignment: {confidence:.1f}%)")

    # Important Non-Guarantee Callout
    st.warning(
        "⚠️ **Important Academic Distinction: Model Confidence vs. Hiring Guarantee**\n\n"
        f"The **{confidence:.1f}% confidence** represents the Decision Tree's internal mathematical alignment with the "
        f"**{pred_class}** pedagogical archetype. **It is NOT a guaranteed probability of being hired or clearing a corporate interview.** "
        "Real interview outcomes depend heavily on behavioral communication, live problem decomposition, interviewer subjectivity, "
        "and company-specific bar variances."
    )

    # Metrics Row
    m1, m2, m3 = st.columns(3)
    m1.metric("Overall Average Score", f"{overall_avg}%")
    m2.metric("Archetype Alignment Confidence", f"{confidence:.1f}%")
    m3.metric("Model Architecture", "DecisionTreeClassifier (CART)")

    # Model Class Alignment Distribution
    st.subheader("📊 Archetype Alignment Distribution")
    st.caption("Distribution across the three standardized readiness tiers:")
    prob_df = pd.DataFrame([
        {"Readiness Category": k, "Archetype Alignment (%)": f"{v:.1f}%"}
        for k, v in probs.items()
    ])
    st.dataframe(prob_df, use_container_width=True, hide_index=True)

    # Explanation and Key Factors
    st.subheader("🧠 Model Decision Factors & Feature Influence")
    st.info(f"**Interpretation:** {prediction_result['explanation']}")

    st.markdown("##### Key Topic Influences (Highest Tree Gini Importance):")
    for item in prediction_result.get("top_influencing_features", []):
        st.markdown(
            f"- **{item['feature']}** — Student Score: `{item['score']}%` | Feature Importance Weight: `{item['importance']:.3f}`"
        )

    st.markdown("##### Pedagogical Recommendation:")
    st.write(prediction_result["recommendation"])

    # ----------------- RIGOROUS MODEL PERFORMANCE & CLASSIFICATION REPORT -----------------
    with st.expander("📈 Comprehensive Model Evaluation: Cross-Validation & Classification Report", expanded=False):
        st.markdown("#### 1. 5-Fold Stratified Cross-Validation")
        st.write(
            "To ensure evaluation integrity beyond a single holdout partition, the Decision Tree is validated across "
            "5 stratified folds across the entire dataset:"
        )

        cv_info = metadata.get("cross_validation", {})
        if cv_info:
            c1, c2, c3 = st.columns(3)
            c1.metric("Mean CV Accuracy", f"{cv_info.get('mean_accuracy', 0)*100:.2f}%", f"± {cv_info.get('std_accuracy', 0)*100:.2f}%")
            c2.metric("Mean CV Weighted F1", f"{cv_info.get('mean_f1_weighted', 0)*100:.2f}%", f"± {cv_info.get('std_f1_weighted', 0)*100:.2f}%")
            c3.metric("Cross-Validation Folds", f"{cv_info.get('n_splits', 5)} Folds")

            fold_df = pd.DataFrame({
                "Fold #": [f"Fold {i+1}" for i in range(len(cv_info.get("fold_accuracies", [])))],
                "Fold Accuracy": [f"{v*100:.2f}%" for v in cv_info.get("fold_accuracies", [])],
                "Fold Weighted F1": [f"{v*100:.2f}%" for v in cv_info.get("fold_f1_scores", [])],
            })
            st.dataframe(fold_df, use_container_width=True, hide_index=True)

        st.markdown("#### 2. Per-Class Performance (Holdout Test Set)")
        per_class = metadata.get("per_class_performance", {})
        if per_class:
            class_rows = []
            for cls_name, p_data in per_class.items():
                class_rows.append({
                    "Readiness Class": cls_name,
                    "Precision": f"{p_data.get('precision', 0):.4f}",
                    "Recall": f"{p_data.get('recall', 0):.4f}",
                    "F1-Score": f"{p_data.get('f1_score', 0):.4f}",
                    "Test Support": p_data.get("support", 0),
                })
            class_df = pd.DataFrame(class_rows)
            st.dataframe(class_df, use_container_width=True, hide_index=True)

        st.markdown("#### 3. Test Set Confusion Matrix")
        cm_data = metadata.get("confusion_matrix", {})
        if cm_data and "matrix" in cm_data:
            cm_labels = [c.split(" / ")[0] for c in cm_data.get("labels", READINESS_CLASSES)]
            matrix_df = pd.DataFrame(
                cm_data["matrix"],
                index=[f"Actual: {l}" for l in cm_labels],
                columns=[f"Pred: {l}" for l in cm_labels],
            )
            st.dataframe(matrix_df, use_container_width=True)

        st.caption(f"💾 **Training Data Isolation:** {metadata.get('synthetic_data_isolation', 'Stored in isolated models/ directory.')}")

    # ----------------- INPUT FEATURES EXPANDER -----------------
    with st.expander("🔍 View Technical Skill Features Supplied to the Model"):
        feat_df = pd.DataFrame([
            {"Feature / Topic": k, "Score Value": f"{v}%"}
            for k, v in topic_scores.items()
        ])
        st.dataframe(feat_df, use_container_width=True, hide_index=True)

    # ----------------- VOLUNTARY OUTCOME REPORTING (ACADEMIC FEEDBACK LOOP) -----------------
    with st.expander("🎓 Voluntary Interview Outcome Reporting (Academic Feedback Loop)"):
        st.markdown(
            "Did you recently participate in a technical interview? You can voluntarily report your outcome below. "
            "Your report is stored in a **strictly anonymized** research collection to help validate and improve future model iterations."
        )

        with st.form("outcome_reporting_form"):
            reported_outcome = st.selectbox(
                "Actual Interview Outcome / Experience:",
                [
                    "Cleared Technical Round / Advanced to Next Stage",
                    "Received Job Offer",
                    "Interview Currently in Progress",
                    "Did Not Clear / Identified Specific Skill Gaps",
                    "Practice Assessment Only (No Commercial Interview Taken)",
                ]
            )
            feedback_notes = st.text_area(
                "Optional Reflections (e.g. Which technical questions were asked? What surprised you?):",
                placeholder="e.g. The interviewer focused heavily on indexing in MongoDB and Big-O recursion..."
            )
            submit_outcome = st.form_submit_button("📨 Submit Anonymized Feedback", use_container_width=True)

            if submit_outcome:
                research_col = get_research_data_collection()
                if research_col is not None:
                    try:
                        research_col.insert_one({
                            "topic_scores": topic_scores,
                            "overall_average": overall_avg,
                            "target_role": current_student.get("target_role"),
                            "model_predicted_readiness": pred_class,
                            "actual_outcome": reported_outcome,
                            "feedback_notes": feedback_notes.strip() if feedback_notes else None,
                            "anonymization_method": "PII-stripped (No name, email, student_id, or IP address)",
                            "created_at": datetime.now(timezone.utc),
                        })
                        st.success("✅ Thank you! Your anonymized outcome has been added to the academic research dataset.")
                    except Exception as e:
                        st.error(f"Error saving feedback: {e}")

    # Retake Assessment Button
    st.write("")
    if st.button("🔄 Retake Skill Assessment"):
        st.session_state.current_page = "Skill Assessment"
        st.rerun()

    # Mandatory Academic Disclaimer
    st.divider()
    st.caption(
        "⚖️ **Academic Integrity Disclaimer:** " + prediction_result.get(
            "notice",
            "This readiness prediction is an algorithmic estimate based on assessment data, not a guarantee of employment or interview outcome."
        )
    )
