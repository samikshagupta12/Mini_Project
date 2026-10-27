"""Admin and Interview Question Management Module."""
from datetime import datetime, timezone
import uuid
import streamlit as st
import pandas as pd
from config.settings import TOPICS, DIFFICULTY_LEVELS, QUESTION_TYPES, JOB_ROLES
from database.collections import get_questions_collection
from database.seed_questions import seed_database
from utils.validators import validate_question


def render_admin_questions_page():
    st.title("⚙️ Admin & Question Management")
    st.write("Manage the technical interview question repository in MongoDB, inspect existing records, or seed standard questions.")

    questions_col = get_questions_collection()
    if questions_col is None:
        st.error("Database connection unavailable.")
        return

    # Database Summary Metrics
    total_q = questions_col.count_documents({})
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Questions in MongoDB", total_q)
    col2.metric("Supported Technical Topics", len(TOPICS))
    col3.metric("Difficulty Tiers", len(DIFFICULTY_LEVELS))

    st.divider()

    # Seeding & Management Actions
    st.subheader("🛠️ Database Maintenance")
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        if st.button("🌱 Seed / Refresh Default Questions", use_container_width=True):
            with st.spinner("Populating MongoDB with questions..."):
                cnt, msg = seed_database(force=True)
            st.success(msg)
            st.rerun()

    with act_col2:
        if st.button("🔄 Refresh View", use_container_width=True):
            st.rerun()

    st.divider()

    # Add New Question Form
    with st.expander("➕ Add New Technical Interview Question"):
        with st.form("add_question_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                topic = st.selectbox("Technical Topic *", TOPICS)
                difficulty = st.selectbox("Difficulty Level *", DIFFICULTY_LEVELS)
                q_type = st.selectbox("Question Type *", QUESTION_TYPES)
                job_role = st.selectbox("Target Job Role", JOB_ROLES)

            with f_col2:
                q_id = st.text_input("Custom Question ID (Optional)", placeholder="e.g., PY-010")
                tags_str = st.text_input("Tags (Comma-separated)", placeholder="e.g., python, decorators, memory")

            question_text = st.text_area("Question Text *", placeholder="Type the complete interview question here...")
            answer_text = st.text_area("Suggested Answer *", placeholder="Provide the canonical answer or code solution...")
            explanation_text = st.text_area("Technical Explanation *", placeholder="Provide an in-depth technical explanation...")

            submitted = st.form_submit_button("💾 Save Question to MongoDB", use_container_width=True)

            if submitted:
                tags = [t.strip().lower() for t in tags_str.split(",") if t.strip()]
                generated_id = q_id.strip() if q_id.strip() else f"Q-{str(uuid.uuid4())[:8].upper()}"
                
                doc = {
                    "question_id": generated_id,
                    "topic": topic,
                    "difficulty": difficulty,
                    "question_type": q_type,
                    "job_role": job_role,
                    "question": question_text.strip(),
                    "answer": answer_text.strip(),
                    "explanation": explanation_text.strip(),
                    "tags": tags,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }

                is_valid, errors = validate_question(doc)
                if not is_valid:
                    for err in errors:
                        st.error(err)
                else:
                    # Check unique question_id
                    if questions_col.find_one({"question_id": generated_id}):
                        st.error(f"A question with ID '{generated_id}' already exists.")
                    else:
                        questions_col.insert_one(doc)
                        st.success(f"Question '{generated_id}' saved successfully to MongoDB!")
                        st.rerun()

    st.divider()

    # Search & Table View of Questions in MongoDB
    st.subheader("📚 Browse Questions Repository")
    search_query = st.text_input("🔍 Search by keyword or question text", "")
    filter_topic = st.selectbox("Filter by Topic", ["All"] + TOPICS)

    query = {}
    if filter_topic != "All":
        query["topic"] = filter_topic
    if search_query.strip():
        query["$or"] = [
            {"question": {"$regex": search_query.strip(), "$options": "i"}},
            {"tags": {"$in": [search_query.strip().lower()]}},
            {"question_id": {"$regex": search_query.strip(), "$options": "i"}}
        ]

    docs = list(questions_col.find(query).sort("topic", 1).limit(50))
    if not docs:
        st.info("No questions matching the search criteria.")
    else:
        q_table = []
        for d in docs:
            q_table.append({
                "ID": d.get("question_id", "N/A"),
                "Topic": d.get("topic"),
                "Difficulty": d.get("difficulty"),
                "Type": d.get("question_type"),
                "Question": d.get("question", "")[:90] + ("..." if len(d.get("question", "")) > 90 else ""),
            })
        st.dataframe(pd.DataFrame(q_table), use_container_width=True, hide_index=True)

