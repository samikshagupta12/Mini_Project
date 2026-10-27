"""Interview Question Generator and Interactive Practice Module."""
from datetime import datetime, timezone
import random
import streamlit as st
from config.settings import TOPICS, DIFFICULTY_LEVELS, QUESTION_TYPES, JOB_ROLES
from database.collections import (
    get_questions_collection,
    get_practice_sessions_collection,
    to_object_id,
)
from utils.session_manager import get_current_student


def render_question_generator_page():
    st.title("🎯 Interview Question Generator")
    st.write("Generate curated technical interview questions matching your target domain, difficulty, and problem-solving focus.")

    questions_col = get_questions_collection()
    if questions_col is None:
        st.error("Database connection unavailable.")
        return

    total_q_count = questions_col.count_documents({})
    if total_q_count == 0:
        st.warning("⚠️ No interview questions found in MongoDB. Please seed the database first.")
        if st.button("🌱 Seed Interview Questions Now"):
            from database.seed_questions import seed_database
            cnt, msg = seed_database(force=True)
            st.success(msg)
            st.rerun()
        return

    # Filter Controls
    st.subheader("⚙️ Generator Settings")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        sel_topic = st.selectbox("Topic", ["All Topics"] + TOPICS)
    with c2:
        sel_diff = st.selectbox("Difficulty", ["All Difficulties"] + DIFFICULTY_LEVELS)
    with c3:
        sel_type = st.selectbox("Question Type", ["All Types"] + QUESTION_TYPES)
    with c4:
        num_questions = st.select_slider("Number of Questions", options=[3, 5, 8, 10], value=5)

    current_student = get_current_student()

    # Query builder
    query = {}
    if sel_topic != "All Topics":
        query["topic"] = sel_topic
    if sel_diff != "All Difficulties":
        query["difficulty"] = sel_diff
    if sel_type != "All Types":
        query["question_type"] = sel_type

    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        generate_clicked = st.button("🎲 Generate Question Set", use_container_width=True)

    with col_btn2:
        if st.button("🔄 Clear Active Questions", use_container_width=True):
            st.session_state.practice_questions = []
            st.session_state.practice_revealed = {}
            st.rerun()

    if generate_clicked:
        matching = list(questions_col.find(query))
        if not matching:
            st.warning("No questions found matching your specific filter criteria. Try broader filters.")
            st.session_state.practice_questions = []
        else:
            # Sample without replacement
            sample_size = min(num_questions, len(matching))
            selected = random.sample(matching, sample_size)
            st.session_state.practice_questions = selected
            st.session_state.practice_revealed = {q.get("question_id", str(i)): False for i, q in enumerate(selected)}
            st.session_state.practice_ratings = {}

    # Display Active Questions
    active_qs = st.session_state.get("practice_questions", [])
    if active_qs:
        st.divider()
        st.subheader(f"📝 Practice Session ({len(active_qs)} Questions)")

        practice_col = get_practice_sessions_collection()
        student_id = to_object_id(current_student.get("_id")) if current_student else None

        for idx, q in enumerate(active_qs):
            q_id = q.get("question_id", f"Q-{idx+1}")
            
            with st.container():
                st.markdown(
                    f"#### Question {idx + 1}: {q.get('question')} "
                )
                
                # Badges
                b1, b2, b3 = st.columns([1, 1, 2])
                b1.caption(f"📌 **Topic:** {q.get('topic')}")
                b2.caption(f"⚡ **Level:** {q.get('difficulty')}")
                b3.caption(f"🏷️ **Type:** {q.get('question_type')} | ID: `{q_id}`")

                # Practice Answer Expander
                with st.expander("💡 Reveal Suggested Answer & Explanation"):
                    st.markdown("**Suggested Answer:**")
                    st.markdown(q.get("answer", "No answer provided."))
                    st.markdown("**Technical Explanation:**")
                    st.write(q.get("explanation", "No explanation available."))
                    
                    if q.get("tags"):
                        st.caption(f"Tags: {', '.join(q.get('tags', []))}")

                    # Self-assessment practice logger
                    if current_student and practice_col is not None:
                        st.write("---")
                        r_col1, r_col2, r_col3 = st.columns([2, 1, 1])
                        with r_col1:
                            rating = st.radio(
                                f"Self-Rating for {q_id}:",
                                ["Mastered / Answered Correctly", "Needs Review", "Difficult / Review Later"],
                                key=f"rate_{q_id}",
                                horizontal=True
                            )
                        with r_col2:
                            st.write("")
                            if st.button("💾 Record Rating", key=f"btn_rate_{q_id}"):
                                practice_doc = {
                                    "student_id": student_id,
                                    "student_email": current_student.get("email"),
                                    "question_id": q_id,
                                    "topic": q.get("topic"),
                                    "difficulty": q.get("difficulty"),
                                    "self_rating": rating,
                                    "created_at": datetime.now(timezone.utc),
                                }
                                practice_col.insert_one(practice_doc)
                                st.success("Rating recorded in MongoDB!")

                st.write("")
    else:
        st.info("Click **'🎲 Generate Question Set'** above to load technical interview questions.")

