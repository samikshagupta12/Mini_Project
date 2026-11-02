"""
Clean, Professional Technical Interview Question Generator & Interactive Practice Sandbox.
Provides dynamic technical question generation across all 10 computer science disciplines,
continuous loading with 'Load More Questions', verified canonical solutions, and conceptual explanations.
Practice questions remain interactive and local — no student practice answers are stored in MongoDB.
Only student profile, assessments, learning roadmaps, and ML readiness predictions are saved in the database.
"""
import streamlit as st

from config.settings import TOPICS, DIFFICULTY_LEVELS
from database.collections import get_questions_collection
from database.api_fetcher import get_fresh_questions, sync_dynamic_questions_to_db


def render_question_generator_page():
    st.title("🎯 Technical Interview Question Generator")
    st.markdown("Practice genuine technical interview questions, draft your thoughts locally, and inspect canonical solutions with conceptual deep dives.")
    
    st.info(
        "💡 **Practice Sandbox**: Question practice is interactive and local. "
        "Your user profile, assessment metrics, learning roadmaps, and ML predictions are saved in MongoDB—"
        "**no practice answers are stored in the database**."
    )

    questions_col = get_questions_collection()
    if questions_col is None:
        st.error("Database connection unavailable. Please check your MongoDB configuration.")
        return

    # Ensure question repository is populated
    if questions_col.count_documents({}) == 0:
        with st.spinner("Initializing technical interview question repository..."):
            sync_dynamic_questions_to_db(amount=20)
            st.rerun()

    # Initialize session state for practice questions
    if "practice_questions" not in st.session_state:
        st.session_state.practice_questions = []

    # ----------------- GENERATOR FILTER CONTROLS -----------------
    st.subheader("⚙️ Question Generator Filters")
    
    col1, col2, col3 = st.columns([2, 1.5, 1.5])
    with col1:
        sel_topic = st.selectbox("Technical Discipline", ["All Topics"] + TOPICS, key="gen_filter_topic")
    with col2:
        sel_diff = st.selectbox("Difficulty Tier", ["All Difficulties"] + DIFFICULTY_LEVELS, key="gen_filter_diff")
    with col3:
        num_questions = st.select_slider("Questions per Batch", options=[3, 5, 8, 10], value=5, key="gen_batch_size")

    c_gen1, c_gen2 = st.columns([3, 1])
    with c_gen1:
        gen_btn = st.button("🚀 Fetch & Generate Questions", use_container_width=True)
    with c_gen2:
        if st.button("🔄 Clear Active Set", use_container_width=True):
            st.session_state.practice_questions = []
            st.rerun()

    # Initial batch generation
    if gen_btn:
        with st.spinner("Fetching technical questions matching your filters..."):
            fresh_qs = get_fresh_questions(
                topic=sel_topic,
                difficulty=sel_diff,
                count=num_questions,
                exclude_ids=[]
            )
            st.session_state.practice_questions = fresh_qs
            st.rerun()

    st.divider()

    # ----------------- ACTIVE PRACTICE QUESTIONS -----------------
    active_qs = st.session_state.get("practice_questions", [])

    if active_qs:
        st.subheader(f"📝 Interactive Practice Session ({len(active_qs)} Questions)")
        st.caption("Review each technical question, formulate your approach in the local scratchpad, and reveal the verified canonical solution.")

        for idx, q in enumerate(active_qs):
            q_id = q.get("question_id", f"Q-{idx+1}")
            topic = q.get("topic", "Computer Science")
            difficulty = q.get("difficulty", "Intermediate")
            q_type = q.get("question_type", "Conceptual")

            with st.container():
                st.markdown(f"#### Question {idx + 1}: {q.get('question')}")
                
                # Metadata Badges
                chip1, chip2, chip3 = st.columns([1.5, 1, 1])
                chip1.info(f"📌 **Topic:** {topic}")
                chip2.warning(f"⚡ **Level:** {difficulty}")
                chip3.success(f"🏷️ **Type:** {q_type}")

                # Local Scratchpad / Thought Area (Not saved to DB)
                scratch_key = f"scratch_{q_id}_{idx}"
                st.text_area(
                    "Your Thoughts / Code Scratchpad (Local notes only - not stored in DB):",
                    placeholder="Draft your pseudocode, key considerations, or notes here...",
                    key=scratch_key,
                    height=90
                )

                # Canonical Solution & Concept Breakdown Expander
                with st.expander("💡 Reveal Solution & Technical Explanation"):
                    st.markdown("##### Canonical Suggested Solution:")
                    st.markdown(q.get("answer", "No answer provided."))
                    
                    st.markdown("##### Technical Explanation & Concept Breakdown:")
                    st.write(q.get("explanation", "No explanation available."))

                    if q.get("tags"):
                        st.caption(f"Tags: {', '.join(q.get('tags', []))}")

                st.write("---")

        # ----------------- LOAD MORE QUESTIONS ACTION BAR -----------------
        c_more, c_reset = st.columns([3, 1])
        with c_more:
            if st.button("➕ Load More Questions", use_container_width=True):
                with st.spinner("Fetching additional questions for this session..."):
                    current_ids = [q.get("question_id") for q in active_qs if q.get("question_id")]
                    more_qs = get_fresh_questions(
                        topic=sel_topic,
                        difficulty=sel_diff,
                        count=num_questions,
                        exclude_ids=current_ids
                    )
                    
                    # Deduplicate and append
                    unseen_more = [q for q in more_qs if q.get("question_id") not in current_ids]
                    if unseen_more:
                        st.session_state.practice_questions.extend(unseen_more)
                        st.success(f"✅ Appended {len(unseen_more)} fresh questions! Total active: {len(st.session_state.practice_questions)}")
                        st.rerun()
                    else:
                        st.info("ℹ️ All available questions for this filter combination have already been loaded into your active session.")
        
        with c_reset:
            if st.button("🔄 Reset Session", use_container_width=True):
                st.session_state.practice_questions = []
                st.rerun()

    else:
        st.info("💡 Choose your technical discipline and difficulty filters above, then click **'🚀 Fetch & Generate Questions'** to start your practice session.")
