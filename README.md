# 🎓 AI-Powered Interview Preparation System

A full-stack, machine learning-driven web application designed to help computer science students and software engineering candidates systematically assess their technical skills, diagnose knowledge gaps, receive personalized study roadmaps, practice curated interview questions, and predict their technical interview readiness using a **Scikit-learn Decision Tree Classifier**.

---

## 📑 Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. System Architecture](#2-system-architecture)
- [3. Key Features](#3-key-features)
- [4. Technology Stack](#4-technology-stack)
- [5. Project Folder Structure](#5-project-folder-structure)
- [6. Database Architecture (MongoDB)](#6-database-architecture-mongodb)
- [7. Machine Learning Methodology](#7-machine-learning-methodology)
- [8. Installation & Setup Guide](#8-installation--setup-guide)
- [9. Running the Application](#9-running-the-application)
- [10. Running the Test Suite](#10-running-the-test-suite)
- [11. Troubleshooting & FAQs](#11-troubleshooting--faqs)

---

## 1. Project Overview

Preparing for technical interviews requires mastering multiple computer science disciplines simultaneously. This platform replaces fragmented interview prep by providing an integrated, data-driven cycle:

1. **Self-Assessment:** Students self-rate proficiency across 10 core technical domains.
2. **Diagnostic Analytics:** The system automatically identifies highest and lowest scoring areas, flags weak topics (< 50%), and compares performance against previous attempts.
3. **Machine Learning Readiness Prediction:** A trained Scikit-learn Decision Tree assesses whether the student is *"Interview Ready"*, *"Intermediate / Partially Ready"*, or *"Beginner / Needs Improvement"*, detailing the exact feature importances influencing the prediction.
4. **Targeted Question Practice:** Curated questions are dynamically retrieved from MongoDB based on domain, difficulty, and question type with self-rating tracking.
5. **Personalized Study Roadmap:** A prioritized learning plan is generated targeting the student's weakest subjects with concrete concepts, exercises, and mini-project recommendations.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Streamlit Web UI / Dashboard                │
│  (Home | Profile | Assessment | Analysis | Questions | ML)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌───────────────────────────┐         ┌───────────────────────────┐
│     Business Modules      │         │   Machine Learning (ML)   │
│  - Profile Management     │         │  - Decision Tree Classifier│
│  - Metric Calculations    │         │  - Inference & Explainers │
│  - Roadmap Generator      │         │  - Evaluation & Metrics   │
└─────────────┬─────────────┘         └─────────────┬─────────────┘
              │                                     │
              ▼                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer & Persistence                  │
│       MongoDB / PyMongo (Fallback: In-Memory Mock)          │
│ Collections: students, assessments, questions, predictions  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Key Features

- **🏠 Home Dashboard:** Student profile summary, total assessments count, average competency score, metric cards, topic performance bar chart, and critical action areas.
- **👤 Student Profile Management:** Create and edit technical profiles with field validation (unique email, degree, target job role, experience level, preferred programming language).
- **📝 Technical Skill Assessment:** Evaluation across 10 topics (0–100) with quick-fill presets and instant classification into Strong (80–100), Moderate (50–79), and Weak (<50).
- **🔍 Strong & Weak Topic Analysis:** Identifies highest/lowest topics, complete competency rankings, and historical delta comparisons (improvement/regression).
- **🎯 Interview Question Generator:** Dynamic retrieval from MongoDB filtered by Topic, Difficulty (Beginner, Intermediate, Advanced), and Type (Conceptual, Programming, Scenario-Based), featuring expandable answers and self-rating tracking.
- **🛣️ Personalized Learning Roadmap:** Automatically prioritizes weak subjects, detailing concepts to study, coding exercises, mini-projects, estimated completion times, and interactive progress check-off saved to MongoDB.
- **🤖 Interview Readiness Prediction:** Genuine Scikit-learn Decision Tree model predicting readiness tier with class probabilities, top feature importances, and strategic advice.
- **📊 Performance Analytics:** 6 comprehensive Matplotlib visualizations:
  1. Topic-wise skill score bar chart with threshold benchmarks.
  2. Horizontal ranked bar chart (lowest to highest).
  3. Topic distribution doughnut chart (Strong vs Moderate vs Weak).
  4. Historical score progression line chart across attempts.
  5. Current vs. previous assessment grouped bar chart.
  6. Decision Tree Confusion Matrix heatmap and test set evaluation metrics.
- **📜 Assessment History:** Detailed records of all past attempts with drill-down capability.
- **⚙️ Admin & Question Management:** Question repository browser, custom question authoring form with schema validation, and seed utility.

---

## 4. Technology Stack

| Layer | Component | Version / Description |
| :--- | :--- | :--- |
| **Language** | Python | 3.10+ / 3.13 |
| **Frontend UI** | Streamlit | 1.30+ |
| **Machine Learning** | Scikit-learn | 1.3+ (DecisionTreeClassifier) |
| **Data Processing** | Pandas, NumPy | Data manipulation and numerical operations |
| **Visualizations** | Matplotlib | Multi-panel analytical charts |
| **Database** | MongoDB / PyMongo | Document-based persistence |
| **Database Mock** | mongomock | In-memory fallback simulation for offline testing |
| **Model Persistence**| Joblib | Serialization of trained ML artifacts |
| **Config** | python-dotenv | Environment variable configuration via `.env` |
| **Unit Testing** | Pytest | Test suite with 17 automated tests |

---

## 5. Project Folder Structure

```
AI_Interview/
├── app.py                      # Main Streamlit application entrypoint
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation
├── .env.example                # Environment variables template
├── .env                        # Local environment variables
├── .gitignore                  # Git ignore rules
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Global constants, thresholds, and paths
│
├── database/
│   ├── __init__.py
│   ├── connection.py           # MongoDB connection manager with timeout & mock fallback
│   ├── collections.py          # Collection getters, index creation, ObjectId helpers
│   └── seed_questions.py       # Seed script populating initial question database
│
├── modules/
│   ├── __init__.py
│   ├── home_dashboard.py       # Home dashboard view & metrics
│   ├── student_profile.py      # Profile creation and editing
│   ├── skill_assessment.py     # Assessment scoring and submission
│   ├── topic_analysis.py       # Diagnostic analysis and historical comparison
│   ├── question_generator.py   # Question retrieval and interactive practice
│   ├── learning_roadmap.py     # Priority-based study tracks & task tracking
│   ├── readiness_prediction.py # ML prediction page with feature explainers
│   ├── analytics.py            # Matplotlib data visualization suite
│   ├── assessment_history.py   # Past assessment attempts & inspection
│   └── admin_questions.py      # Question management and seeding
│
├── ml/
│   ├── __init__.py
│   ├── train_model.py          # Decision Tree training script & synthetic generator
│   ├── predict.py              # ML inference pipeline & explainers
│   └── model_evaluation.py     # Model metadata and confusion matrix loader
│
├── utils/
│   ├── __init__.py
│   ├── validators.py           # Validation for emails, profiles, scores, questions
│   ├── helpers.py              # Score categorization & metric aggregations
│   └── session_manager.py      # Streamlit session state management
│
├── models/
│   ├── readiness_model.joblib  # Serialized Scikit-learn Decision Tree
│   └── model_metadata.json     # Evaluation metrics, confusion matrix, feature weights
│
└── tests/
    ├── __init__.py
    ├── test_validators.py      # Tests for validation functions
    ├── test_assessment.py      # Tests for scoring and classification
    ├── test_topic_analysis.py  # Tests for rankings and deltas
    ├── test_readiness_prediction.py # Tests for ML model inference
    └── test_roadmap.py         # Tests for roadmap task prioritization
```

---

## 6. Database Architecture (MongoDB)

The system utilizes MongoDB as its primary store. Database connection parameters are read from `.env` via `MONGODB_URI` and `MONGODB_DATABASE`.

### Collections

1. **`students`**: Stores student profiles.
   - Fields: `name`, `email` *(unique index)*, `education`, `course`, `target_role`, `experience_level`, `preferred_language`, `created_at`, `updated_at`.
2. **`assessments`**: Stores historical assessment attempts.
   - Fields: `student_id`, `student_email`, `topic_scores`, `average_score`, `strong_topics`, `moderate_topics`, `weak_topics`, `created_at`.
3. **`interview_questions`**: Technical question repository.
   - Fields: `question_id` *(unique)*, `topic`, `difficulty`, `question_type`, `job_role`, `question`, `answer`, `explanation`, `tags`, `created_at`.
4. **`readiness_predictions`**: Persists ML prediction logs.
   - Fields: `student_id`, `assessment_id`, `predicted_readiness`, `confidence`, `probabilities`, `overall_average`, `model_version`, `created_at`.
5. **`learning_roadmaps`**: Stores prioritized roadmaps with interactive task completion.
   - Fields: `student_id`, `assessment_id`, `target_role`, `tasks` (array of concepts, exercises, projects, status), `completion_percentage`, `created_at`, `updated_at`.
6. **`practice_sessions`**: Logs student self-ratings during practice.
   - Fields: `student_id`, `question_id`, `topic`, `difficulty`, `self_rating`, `created_at`.

> **Note on Offline / Academic Demonstration:**
> If a local MongoDB instance is offline or unreachable, the system automatically logs a diagnostic warning and activates an in-memory database simulation (`mongomock`) so that reviewers can fully test the entire application workflow without crashing.

---

## 7. Machine Learning Methodology

### Algorithm & Features
The interview readiness predictor uses a **Decision Tree Classifier (CART)** from Scikit-learn with:
- **Input Features (11):** 10 topic scores (Python, DSA, OOP, DBMS, SQL/Mongo, OS, Networks, ML, Data Analysis, Problem-Solving) + Overall Average Score.
- **Target Classes (3):**
  - `Interview Ready`
  - `Intermediate / Partially Ready`
  - `Beginner / Needs Improvement`

### Dataset Assumptions & Academic Integrity
- **Synthetic Labeled Dataset:** Generated using educational heuristics with realistic variance and label noise to reflect human interviewer evaluation standards.
- **Academic Disclaimer:** Clearly stated in the UI that predictions are instructional estimates and require real-world interview validation.
- **Hyperparameters:** `criterion='gini'`, `max_depth=6`, `min_samples_split=12`, `min_samples_leaf=6`, `random_state=42`.
- **Evaluation Performance:** Tested on a stratified 20% holdout test set with **>95% accuracy** and balanced F1-scores.

---

## 8. Installation & Setup Guide

### 1. Clone or Open the Workspace
```powershell
cd C:\Users\samik\Desktop\AI_Interview
```

### 2. Configure Environment Variables
Copy the example `.env` file:
```powershell
cp .env.example .env
```
Edit `.env` to configure your MongoDB connection:
```ini
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=ai_interview_system
USE_MOCK_DB=false
```
*(For MongoDB Atlas, paste your cluster connection string into `MONGODB_URI`)*.

### 3. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 4. Train the Machine Learning Model
```powershell
python -m ml.train_model
```
*Output: Generates `models/readiness_model.joblib` and `models/model_metadata.json`.*

### 5. Seed Interview Questions into MongoDB
```powershell
python -m database.seed_questions
```
*Output: Inserts curated technical questions across all 10 topics and difficulty tiers.*

---

## 9. Running the Application

Launch the Streamlit web application:

```powershell
python -m streamlit run app.py
```

Streamlit will start the local server and open your default web browser to:
```
http://localhost:8501
```

---

## 10. Running the Test Suite

Execute the automated test suite using Pytest:

```powershell
python -m pytest tests/ -v
```

All 17 test cases test score validation, metric calculations, topic rankings, ML inference, and roadmap generation.

---

## 11. Troubleshooting & FAQs

### Q1: `Program 'streamlit.exe' failed to run: An Application Control policy has blocked this file`
- **Cause:** Windows Defender Application Control (WDAC) or Smart App Control blocks newly generated unsigned `.exe` stubs inside `venv\Scripts\`.
- **Fix:** Run Streamlit directly through the signed Python interpreter:
  ```powershell
  python -m streamlit run app.py
  ```

### Q2: MongoDB connection timed out
- Ensure your local MongoDB service is started (`net start MongoDB` or run `mongod`).
- If you don't have MongoDB installed locally, you can use a free cloud cluster from [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) by updating `MONGODB_URI` in `.env`, or the app will automatically run in fallback in-memory demonstration mode.

### Q3: How to test different student scenarios quickly?
- Navigate to the **Skill Assessment** page and use the **⚡ Quick Fill Presets** at the top (`Advanced Ready`, `Balanced Intermediate`, `Beginner Needs Work`) to immediately populate realistic score profiles.

