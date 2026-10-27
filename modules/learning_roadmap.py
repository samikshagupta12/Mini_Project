"""Personalized Learning Roadmap Module with MongoDB task tracking."""
from datetime import datetime, timezone
import streamlit as st
from database.collections import (
    get_roadmaps_collection,
    get_assessments_collection,
    to_object_id,
    serialize_doc,
)
from utils.session_manager import get_current_student

# Knowledge base of targeted study actions per topic
TOPIC_ROADMAP_PLANS = {
    "Python Programming": {
        "concepts": ["Data Model & Mutability", "List Comprehensions & Generators", "Decorators & Context Managers", "Threading, Asyncio & GIL"],
        "exercises": ["Implement custom iterators and generators", "Build a rate-limiting decorator", "Refactor scripts to use multiprocessing"],
        "project": "Async Web Scraper or CLI Task Automation Tool",
        "interview_task": "Explain memory management, garbage collection, and GIL under high concurrency",
        "duration": "10 - 14 Days"
    },
    "Data Structures and Algorithms": {
        "concepts": ["Two Pointers & Sliding Window", "Hash Maps & Sets", "Binary Trees & BST Traversals", "Dynamic Programming & Graphs (BFS/DFS)"],
        "exercises": ["Solve 20 LeetCode Mediums on Two Pointers & Trees", "Implement LRU Cache from scratch", "Solve Knapsack and Graph traversal problems"],
        "project": "Maze Solver / Route Finder using BFS/Dijkstra",
        "interview_task": "Live code a balanced BST search and cycle detection in a linked list",
        "duration": "2 - 3 Weeks"
    },
    "Object-Oriented Programming": {
        "concepts": ["Pillars of OOP (Encapsulation, Abstraction, Inheritance, Polymorphism)", "SOLID Principles", "Common Design Patterns (Factory, Singleton, Observer)"],
        "exercises": ["Refactor monolithic script into modular classes following SRP", "Implement a thread-safe Singleton and Factory pattern"],
        "project": "Object-Oriented Parking Lot or Library Management System",
        "interview_task": "Whiteboard a system design applying Liskov Substitution and Open/Closed Principles",
        "duration": "1 - 2 Weeks"
    },
    "Database Management Systems": {
        "concepts": ["ACID Properties & Transaction Isolation", "Database Normalization (1NF to BCNF)", "B+ Tree Indexing & Disk I/O Bottlenecks"],
        "exercises": ["Analyze slow query execution plans (EXPLAIN)", "Design an optimal relational schema eliminating update anomalies"],
        "project": "E-Commerce Database Schema with normalized tables and indexes",
        "interview_task": "Explain how indexing speeds up lookups and discuss write amplification",
        "duration": "10 Days"
    },
    "SQL and MongoDB": {
        "concepts": ["Advanced SQL Joins & Window Functions (ROW_NUMBER, DENSE_RANK)", "Subqueries & CTEs", "MongoDB Aggregation Pipelines & Document Modeling"],
        "exercises": ["Write queries to compute month-over-month revenue growth", "Build a 4-stage MongoDB aggregation pipeline"],
        "project": "Hybrid Data Store combining relational transactions with document analytics",
        "interview_task": "Compare SQL vs NoSQL trade-offs and explain sharding strategies",
        "duration": "10 - 14 Days"
    },
    "Operating Systems": {
        "concepts": ["Process vs Thread Concurrency", "Deadlock Conditions & Banker's Algorithm", "Virtual Memory, Paging, and Page Faults"],
        "exercises": ["Simulate Producer-Consumer with mutex locks and condition variables", "Analyze thread starvation scenarios"],
        "project": "Multi-threaded Web Server with a thread pool",
        "interview_task": "Explain context switching overhead and how OS avoids thrashing",
        "duration": "1 - 2 Weeks"
    },
    "Computer Networks": {
        "concepts": ["OSI & TCP/IP Model Layers", "TCP Handshake, Flow Control vs UDP", "DNS, HTTP/2, HTTP/3, and TLS 1.3 Cryptography"],
        "exercises": ["Capture and analyze packet traces using Wireshark", "Trace HTTP request lifecycle from DNS query to DOM render"],
        "project": "Custom HTTP/1.1 client socket implementation",
        "interview_task": "Walk through step-by-step what happens when typing a URL in a browser",
        "duration": "10 Days"
    },
    "Machine Learning": {
        "concepts": ["Bias-Variance Tradeoff", "Decision Trees & Ensemble Methods (Random Forest)", "Cross-Validation & Metric Selection (F1, ROC-AUC)"],
        "exercises": ["Train and prune a Decision Tree using Scikit-learn", "Address severe class imbalance using SMOTE and class weights"],
        "project": "End-to-End Prediction API with model persistence via Joblib",
        "interview_task": "Explain why Accuracy is misleading for imbalanced datasets and define Precision/Recall",
        "duration": "2 - 3 Weeks"
    },
    "Data Analysis": {
        "concepts": ["Data Wrangling with Pandas & NumPy", "Outlier Detection (IQR & Z-Score)", "Exploratory Data Analysis (EDA) & Matplotlib Visuals"],
        "exercises": ["Clean raw survey data and impute missing values with median/mode", "Build multi-variable pivot tables"],
        "project": "Interactive Sales Analytics Dashboard",
        "interview_task": "Explain how to detect correlation vs causation and demonstrate groupby operations",
        "duration": "1 - 2 Weeks"
    },
    "Problem-Solving Skills": {
        "concepts": ["Structured Decomposition", "Edge Case Identification", "Brute-Force to Optimal Big-O Optimization"],
        "exercises": ["Solve 15 diverse algorithmic challenges under timed 25-minute constraints", "Conduct manual code walk-throughs before running tests"],
        "project": "Daily algorithmic problem diary with runtime complexity analyses",
        "interview_task": "Communicate thought process clearly out loud while solving an unseen scenario",
        "duration": "Ongoing / 2 Weeks"
    }
}


def build_roadmap_for_assessment(assessment_doc, target_role="Software Engineer"):
    """Constructs a personalized roadmap based on assessment score priorities."""
    topic_scores = assessment_doc.get("topic_scores", {})
    tasks = []

    # Sort topics by score ascending (lowest score = highest priority)
    sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1])

    for topic, score in sorted_topics:
        if score < 80:  # Weak or Moderate topics need roadmap actions
            plan = TOPIC_ROADMAP_PLANS.get(topic, {})
            if not plan:
                continue

            priority = "High (Critical Weakness)" if score < 50 else "Medium (Reinforcement)"
            
            task_item = {
                "topic": topic,
                "current_score": score,
                "priority": priority,
                "duration": plan.get("duration", "1 - 2 Weeks"),
                "concepts": plan.get("concepts", []),
                "exercises": plan.get("exercises", []),
                "project": plan.get("project", ""),
                "interview_task": plan.get("interview_task", ""),
                "completed": False,
            }
            tasks.append(task_item)

    return tasks


def render_learning_roadmap_page():
    st.title("🛣️ Personalized Learning Roadmap")
    st.write("Actionable, prioritized learning plan tailored to your technical assessment results and target job role.")

    current_student = get_current_student()
    if not current_student:
        st.warning("⚠️ Please select or create a student profile to view your roadmap.")
        return

    assessments_col = get_assessments_collection()
    roadmaps_col = get_roadmaps_collection()

    if assessments_col is None or roadmaps_col is None:
        st.error("Database connection unavailable.")
        return

    student_id = to_object_id(current_student.get("_id"))
    latest_assessment = assessments_col.find_one({"student_id": student_id}, sort=[("created_at", -1)])

    if not latest_assessment:
        st.info("ℹ️ No assessment found. Complete your technical skill assessment to generate your customized roadmap.")
        if st.button("Go to Skill Assessment"):
            st.session_state.current_page = "Skill Assessment"
            st.rerun()
        return

    assessment_id = latest_assessment["_id"]
    
    # Check if a roadmap already exists for this assessment
    existing_roadmap = roadmaps_col.find_one({
        "student_id": student_id,
        "assessment_id": assessment_id
    })

    if not existing_roadmap:
        # Generate new roadmap
        target_role = current_student.get("target_role", "Software Engineer")
        tasks = build_roadmap_for_assessment(latest_assessment, target_role)
        now = datetime.now(timezone.utc)
        roadmap_doc = {
            "student_id": student_id,
            "assessment_id": assessment_id,
            "target_role": target_role,
            "tasks": tasks,
            "completion_percentage": 0.0,
            "created_at": now,
            "updated_at": now,
        }
        res = roadmaps_col.insert_one(roadmap_doc)
        existing_roadmap = roadmaps_col.find_one({"_id": res.inserted_id})

    tasks = existing_roadmap.get("tasks", [])
    
    # Calculate progress
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get("completed", False))
    progress_pct = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 100.0

    # Header summary
    c1, c2, c3 = st.columns(3)
    c1.metric("Target Role", existing_roadmap.get("target_role", "Software Engineer"))
    c2.metric("Topics to Master", total_tasks)
    c3.metric("Roadmap Progress", f"{progress_pct}%")

    st.progress(progress_pct / 100.0)
    st.divider()

    if not tasks:
        st.success("🎉 Outstanding achievement! All your technical topics scored 80% or higher. No remediation required.")
        return

    st.subheader("📚 Targeted Study Tracks")
    st.caption("Check the box when you have completed a topic's study plan to save your progress in MongoDB.")

    updated = False
    for idx, t in enumerate(tasks):
        topic_name = t.get("topic")
        score = t.get("current_score")
        priority = t.get("priority")
        duration = t.get("duration")
        is_done = t.get("completed", False)

        with st.container():
            col_check, col_info = st.columns([1, 10])
            with col_check:
                st.write("")
                st.write("")
                new_done = st.checkbox(
                    "Done",
                    value=is_done,
                    key=f"task_done_{idx}_{topic_name}",
                    label_visibility="collapsed"
                )
                if new_done != is_done:
                    tasks[idx]["completed"] = new_done
                    updated = True

            with col_info:
                badge = "🔴 High Priority" if "High" in priority else "🟡 Medium Priority"
                score_badge = f"Current Score: `{score}%`"
                time_badge = f"⏱️ Est: `{duration}`"
                status_icon = "✅" if is_done else "📖"
                
                st.markdown(f"#### {status_icon} {topic_name} — {badge} | {score_badge} | {time_badge}")
                
                with st.expander(f"View Study Details for {topic_name}"):
                    st.markdown("**Key Concepts to Study:**")
                    for c in t.get("concepts", []):
                        st.markdown(f"- {c}")

                    st.markdown("**Hands-on Coding Exercises:**")
                    for ex in t.get("exercises", []):
                        st.markdown(f"- {ex}")

                    st.markdown(f"**Recommended Mini-Project:** `{t.get('project')}`")
                    st.markdown(f"**Mock Interview Task:** {t.get('interview_task')}")

            st.write("---")

    if updated:
        # Recompute percentage and persist
        comp_count = sum(1 for t in tasks if t.get("completed", False))
        new_pct = round((comp_count / total_tasks * 100), 1) if total_tasks > 0 else 100.0
        roadmaps_col.update_one(
            {"_id": existing_roadmap["_id"]},
            {
                "$set": {
                    "tasks": tasks,
                    "completion_percentage": new_pct,
                    "updated_at": datetime.now(timezone.utc),
                }
            }
        )
        st.toast(f"Progress updated: {new_pct}% complete!")
        st.rerun()

