"""Interview Readiness Checker using Decision Tree Machine Learning."""
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
from database.collections import (
    get_assessments_collection,
    get_readiness_collection,
    to_object_id,
    serialize_doc,
)
from utils.session_manager import get_current_student
from ml.predict import predict_readiness, get_model_status


def render_readiness_prediction_page():
    st.title("🤖 Interview Readiness Prediction")
    st.write("Machine Learning evaluation of your technical interview readiness using a Scikit-learn Decision Tree Classifier.")

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

    # UI Banner for Predicted Readiness Level
    st.divider()
    if pred_class == "Interview Ready":
        st.success(f"### 🎉 Predicted Status: **{pred_class}** (Confidence: {confidence}%)")
    elif pred_class == "Intermediate / Partially Ready":
        st.warning(f"### ⚡ Predicted Status: **{pred_class}** (Confidence: {confidence}%)")
    else:
        st.error(f"### ⚠️ Predicted Status: **{pred_class}** (Confidence: {confidence}%)")

    # Metrics Row
    m1, m2, m3 = st.columns(3)
    m1.metric("Overall Average Score", f"{overall_avg}%")
    m2.metric("ML Model Confidence", f"{confidence}%")
    m3.metric("Model Architecture", "DecisionTreeClassifier (CART)")

    # Model Class Probability Distribution
    st.subheader("📊 Class Probability Distribution")
    prob_df = pd.DataFrame([
        {"Readiness Category": k, "Estimated Probability (%)": v}
        for k, v in probs.items()
    ])
    st.dataframe(prob_df, use_container_width=True, hide_index=True)

    # Explanation and Key Factors
    st.subheader("🧠 Model Decision Factors & Explanation")
    st.info(f"**Interpretation:** {prediction_result['explanation']}")

    st.markdown("##### Key Topic Influences:")
    for item in prediction_result.get("top_influencing_features", []):
        st.markdown(
            f"- **{item['feature']}** — Student Score: `{item['score']}%` | Tree Importance Weight: `{item['importance']:.3f}`"
        )

    st.markdown("##### Strategic Action Plan:")
    st.write(prediction_result["recommendation"])

    # Input Assessment Features Used
    with st.expander("🔍 View Technical Skill Features Supplied to the Model"):
        feat_df = pd.DataFrame([
            {"Feature / Topic": k, "Score Value": v}
            for k, v in topic_scores.items()
        ])
        st.dataframe(feat_df, use_container_width=True, hide_index=True)

    # Retake Assessment Button
    st.write("")
    if st.button("🔄 Retake Skill Assessment"):
        st.session_state.current_page = "Skill Assessment"
        st.rerun()

    # Mandatory Academic / Demonstration Notice
    st.divider()
    st.caption(
        "⚖️ **Disclaimer:** " + prediction_result.get(
            "notice",
            "This readiness prediction is an algorithmic estimate based on assessment data, not a guarantee of employment or interview outcome."
        )
    )

