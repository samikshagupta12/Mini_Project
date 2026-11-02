"""Admin and Interview Question Management Module with Live API Streaming."""
from datetime import datetime, timezone
import uuid
import streamlit as st
import pandas as pd
from config.settings import TOPICS, DIFFICULTY_LEVELS, QUESTION_TYPES, JOB_ROLES
from database.collections import get_questions_collection
from database.seed_questions import seed_database
from database.api_fetcher import sync_dynamic_questions_to_db
from utils.validators import validate_question


def render_admin_questions_page():
    st.title("⚙️ Admin & Question Management")
    st.write("Manage the technical interview question repository in MongoDB, inspect existing records, or stream dynamic questions from online APIs.")

    questions_col = get_questions_collection()
    if questions_col is None:
        st.error("Database connection unavailable.")
        return

    # Database Summary Metrics
    total_q = questions_col.count_documents({})
    api_count = questions_col.count_documents({"source": {"$regex": "API", "$options": "i"}})
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total in MongoDB", total_q)
    col2.metric("Online API Fetched", api_count)
    col3.metric("Supported Topics", len(TOPICS))
    col4.metric("Difficulty Tiers", len(DIFFICULTY_LEVELS))

    st.divider()

    # Maintenance & Live Online Streaming
    st.subheader("🛠️ Database Maintenance & Live API Ingestion")
    act_col1, act_col2 = st.columns(2)
    
    with act_col1:
        st.markdown("##### 🌱 Static Seed Repository")
        st.caption("Populate baseline curated technical questions across all 10 topics.")
        if st.button("Seed / Reset Default Curated Bank", use_container_width=True):
            with st.spinner("Seeding default curated questions into MongoDB..."):
                cnt, msg = seed_database(force=True)
            st.success(msg)
            st.rerun()

    with act_col2:
        st.markdown("##### 🌐 Live Online API Streamer")
        st.caption("Pull real-time computer science interview questions from OpenTDB API.")
        c_amt, c_btn = st.columns([1, 2])
        with c_amt:
            api_batch = st.selectbox("Batch Size", [5, 10, 15, 20], index=1)
        with c_btn:
            st.write("")
            if st.button("🚀 Fetch from API", use_container_width=True):
                with st.spinner(f"Querying online API for {api_batch} questions..."):
                    _, inserted, msg = sync_dynamic_questions_to_db(amount=api_batch)
                st.success(msg)
                st.rerun()

    st.divider()

    # Add New Question Form
    with st.expander("➕ Author New Custom Interview Question"):
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
                generated_id = q_id.strip() if q_id.strip() else f"CUSTOM-{str(uuid.uuid4())[:8].upper()}"
                
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
                    "source": "Admin Manual Entry",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }

                is_valid, errors = validate_question(doc)
                if not is_valid:
                    for err in errors:
                        st.error(err)
                else:
                    if questions_col.find_one({"question_id": generated_id}):
                        st.error(f"A question with ID '{generated_id}' already exists.")
                    else:
                        questions_col.insert_one(doc)
                        st.success(f"Question '{generated_id}' saved successfully to MongoDB!")
                        st.rerun()

    st.divider()

    # Search & Table View of Questions in MongoDB
    st.subheader("📚 Browse Questions Repository")
    search_query = st.text_input("🔍 Search by keyword, question text, or tags", "")
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        filter_topic = st.selectbox("Filter by Topic", ["All"] + TOPICS)
    with c_f2:
        filter_source = st.selectbox("Filter by Source", ["All Sources", "Live Online Computer Science API", "Standard Curated Bank", "Admin Manual Entry"])

    query = {}
    if filter_topic != "All":
        query["topic"] = filter_topic
    if filter_source != "All Sources":
        query["source"] = filter_source
    if search_query.strip():
        query["$or"] = [
            {"question": {"$regex": search_query.strip(), "$options": "i"}},
            {"tags": {"$in": [search_query.strip().lower()]}},
            {"question_id": {"$regex": search_query.strip(), "$options": "i"}}
        ]

    docs = list(questions_col.find(query).sort("created_at", -1).limit(60))
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
                "Source": d.get("source", "Standard Seed Bank"),
                "Question": d.get("question", "")[:80] + ("..." if len(d.get("question", "")) > 80 else ""),
            })
        st.dataframe(pd.DataFrame(q_table), use_container_width=True, hide_index=True)
