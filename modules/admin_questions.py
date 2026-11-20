"""Admin and Interview Question Management Module with Live API Streaming and Role-Based Access Control."""
from datetime import datetime, timezone
import uuid
import streamlit as st
import pandas as pd
from config.settings import TOPICS, DIFFICULTY_LEVELS, QUESTION_TYPES, JOB_ROLES
from database.collections import get_questions_collection, get_research_data_collection
from database.seed_questions import seed_database
from database.api_fetcher import sync_dynamic_questions_to_db
from utils.validators import validate_question
from utils.session_manager import is_admin_logged_in, get_current_admin, set_current_admin, clear_admin_session, get_current_student
from utils.auth import authenticate_admin
from ml.predict import get_model_status, ensure_model_initialized


def render_admin_questions_page():
    st.title("⚙️ Admin & Question Management")
    st.write("Manage the technical interview question repository in MongoDB, inspect existing records, or stream dynamic questions from online APIs.")

    # ----------------- ADMINISTRATOR ROLE ACCESS CONTROL GATE -----------------
    if not is_admin_logged_in():
        st.divider()
        st.error("🛡️ **Administrator Privileges Required**")
        st.write(
            "This administrative section is strictly restricted to system administrators. "
            "Regular students and unauthenticated users cannot view or modify the core question repository, "
            "trigger database re-seeding, or execute model maintenance."
        )

        current_student = get_current_student()
        if current_student:
            st.warning(
                f"⚠️ You are currently signed in under student account: **{current_student.get('name')}** (`{current_student.get('email')}`). "
                "Students do not have administrative authorization."
            )

        with st.container():
            st.markdown("#### 🔐 Administrator Sign In")
            with st.form("admin_gate_login_form"):
                admin_email = st.text_input("Administrator Email", value="admin@interviewprep.com")
                admin_password = st.text_input("Administrator Password", type="password")
                submit_admin = st.form_submit_button("🛡️ Authenticate Administrator", use_container_width=True)

                if submit_admin:
                    with st.spinner("Verifying administrative credentials..."):
                        ok, admin_doc, msg = authenticate_admin(admin_email, admin_password)
                    if ok and admin_doc:
                        set_current_admin(admin_doc)
                        st.success(f"🎉 {msg}")
                        st.rerun()
                    else:
                        st.error(f"Authentication failed: {msg}")

        st.info("💡 Default system credentials: `admin@interviewprep.com` / `admin123` (configured in `.env`).")
        return

    # ----------------- AUTHENTICATED ADMINISTRATOR WORKSPACE -----------------
    current_admin = get_current_admin()
    admin_bar1, admin_bar2 = st.columns([4, 1])
    with admin_bar1:
        st.success(f"🛡️ Active Session: **{current_admin.get('name', 'Administrator')}** (`{current_admin.get('email')}`) | Role: `ADMINISTRATOR`")
    with admin_bar2:
        if st.button("🚪 Exit Admin", use_container_width=True):
            clear_admin_session()
            st.rerun()

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

    # Machine Learning Model Operations
    st.subheader("🤖 Machine Learning Model Operations")
    model_loaded, model_meta = get_model_status()
    
    ml_c1, ml_c2 = st.columns([3, 1])
    with ml_c1:
        if model_loaded and model_meta:
            acc = model_meta.get("evaluation_metrics", {}).get("accuracy", 0.0)
            trained_at = model_meta.get("trained_at", "Unknown")
            st.info(f"✅ **Decision Tree Classifier:** Loaded & Ready | **Accuracy:** `{acc:.1%}` | **Last Trained:** `{trained_at}`")
        else:
            st.warning("⚠️ Decision Tree model artifact is currently missing or not loaded.")

    with ml_c2:
        if st.button("⚡ Force Re-train Model", use_container_width=True):
            with st.spinner("Re-training Decision Tree model and updating artifacts..."):
                ok, new_meta, retrain_msg = ensure_model_initialized(force_retrain=True)
            if ok:
                st.success(retrain_msg)
                st.rerun()
            else:
                st.error(retrain_msg)

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

    # ----------------- ANONYMIZED RESEARCH DATASET SECTION -----------------
    st.divider()
    st.subheader("📊 Anonymized Research Dataset (Continuous Model Improvement)")
    research_col = get_research_data_collection()
    if research_col is not None:
        research_count = research_col.count_documents({})
        st.write(
            f"**Voluntary Anonymized Records Collected:** `{research_count}` observations. "
            "All records are strictly de-identified (no names, emails, IP addresses, or student IDs)."
        )
        if research_count > 0:
            records = list(research_col.find({}, {"_id": 0}).sort("created_at", -1).limit(50))
            flat_records = []
            for r in records:
                created_val = r.get("created_at")
                time_str = created_val.strftime("%Y-%m-%d %H:%M") if hasattr(created_val, "strftime") else str(created_val)
                flat_records.append({
                    "Overall Average": f"{r.get('overall_average', 0)}%",
                    "Target Role": r.get("target_role", "N/A"),
                    "Reported Outcome": r.get("actual_outcome", "Self-Assessment"),
                    "Predicted Class": r.get("model_predicted_readiness", "N/A"),
                    "Consent Status": "Granted (PII-stripped)",
                    "Logged At": time_str,
                })
            st.dataframe(pd.DataFrame(flat_records), use_container_width=True, hide_index=True)
        else:
            st.caption("No voluntary research records submitted yet. As students take assessments or report outcomes with consent enabled, de-identified records will populate here.")
