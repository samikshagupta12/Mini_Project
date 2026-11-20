"""Application configuration settings."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

# MongoDB & Storage Mode Configuration
# Defaults to In-Memory Demo Mode (true) for zero-setup execution without local MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "ai_interview_system")
USE_MOCK_DB = os.getenv("USE_MOCK_DB", "true").lower() in ("true", "1", "yes")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")

# Administrator Credentials (Separate Administrative Role)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@interviewprep.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Technical Assessment Topics (10 standard topics)
TOPICS = [
    "Python Programming",
    "Data Structures and Algorithms",
    "Object-Oriented Programming",
    "Database Management Systems",
    "SQL and MongoDB",
    "Operating Systems",
    "Computer Networks",
    "Machine Learning",
    "Data Analysis",
    "Problem-Solving Skills",
]

# Classification Thresholds
STRONG_THRESHOLD = 80.0
MODERATE_THRESHOLD = 50.0

# Supported Options
DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]
QUESTION_TYPES = ["Conceptual", "Programming", "Scenario-Based"]
JOB_ROLES = [
    "Software Engineer",
    "Backend Developer",
    "Full Stack Developer",
    "Data Scientist",
    "Machine Learning Engineer",
    "Data Analyst",
]
EXPERIENCE_LEVELS = [
    "Student / College Fresher",
    "Entry-Level (0-1 years)",
    "Junior Developer (1-2 years)",
    "Mid-Level Developer (2+ years)",
]
EDUCATION_LEVELS = [
    "B.Tech / B.E. (Computer Science / IT)",
    "B.Tech / B.E. (Other Engineering)",
    "BCA / MCA",
    "B.Sc / M.Sc (Computer Science / Data Science)",
    "Other Technical Degree",
]

PROGRAMMING_LANGUAGES = [
    "Python",
    "Java",
    "C++",
    "JavaScript / TypeScript",
    "Go",
    "SQL",
]

# Readiness Target Classes
READINESS_CLASSES = [
    "Beginner / Needs Improvement",
    "Intermediate / Partially Ready",
    "Interview Ready",
]

# Grouped Technical Subject Categories
TOPIC_CATEGORIES = {
    "💻 Software Development & Core Fundamentals": [
        "Python Programming",
        "Data Structures and Algorithms",
        "Object-Oriented Programming",
        "Problem-Solving Skills",
    ],
    "⚙️ Systems & Infrastructure Engineering": [
        "Operating Systems",
        "Computer Networks",
        "Database Management Systems",
        "SQL and MongoDB",
    ],
    "🧠 Data Science & Applied Intelligence": [
        "Machine Learning",
        "Data Analysis",
    ],
}

# Detailed Descriptions for each Technical Subject
TOPIC_DESCRIPTIONS = {
    "Python Programming": "Syntax, built-in data types, functions, OOP, decorators, generators, and standard library best practices.",
    "Data Structures and Algorithms": "Linear/non-linear structures (arrays, trees, graphs, heaps), algorithm paradigms, and Big-O computational complexity.",
    "Object-Oriented Programming": "Core principles (encapsulation, abstraction, inheritance, polymorphism), design patterns, and SOLID architecture.",
    "Database Management Systems": "Relational theory, schema normalization (1NF-BCNF), ACID properties, indexing, and transaction management.",
    "SQL and MongoDB": "Structured relational querying (JOINs, aggregations) paired with NoSQL document schemas, indexing, and CRUD pipelines.",
    "Operating Systems": "Process scheduling, thread concurrency, memory management, virtual memory/paging, deadlocks, and system calls.",
    "Computer Networks": "Network models (OSI / TCP-IP), protocol mechanics (TCP, UDP, HTTP/S, DNS), socket communication, and routing.",
    "Machine Learning": "Supervised/unsupervised techniques, model evaluation (precision, recall, ROC-AUC), decision trees, and regularized learning.",
    "Data Analysis": "Data wrangling, statistical analysis (variance, distributions, hypothesis testing), and exploratory visualization.",
    "Problem-Solving Skills": "Algorithmic thinking, translating ambiguous technical specifications into efficient, modular, and resilient code.",
}

# Structured Scoring Meaning & Concrete Examples
SCORE_LEVEL_GUIDE = [
    {
        "range": "0 – 25",
        "tier": "Beginner",
        "meaning": "Conceptual or surface-level exposure only.",
        "example": "Recognizes terminology but cannot write working solutions or debug without step-by-step assistance.",
        "badge_color": "🔴",
    },
    {
        "range": "26 – 50",
        "tier": "Basic understanding",
        "meaning": "Understands fundamental syntax and standard patterns.",
        "example": "Can implement straightforward logic; struggles with edge cases, optimizations, or non-trivial problems.",
        "badge_color": "🟡",
    },
    {
        "range": "51 – 75",
        "tier": "Good understanding",
        "meaning": "Independent problem solver with practical competence.",
        "example": "Comfortably writes modular code, explains trade-offs, and solves typical medium interview problems.",
        "badge_color": "🔵",
    },
    {
        "range": "76 – 100",
        "tier": "Advanced understanding",
        "meaning": "Deep architectural mastery and optimization expertise.",
        "example": "Analyzes complex edge cases, understands runtime internals/memory models, and delivers highly optimized solutions.",
        "badge_color": "🟢",
    },
]

# Machine Learning Artifact Paths
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "readiness_model.joblib"
MODEL_METADATA_PATH = MODELS_DIR / "model_metadata.json"
SYNTHETIC_DATASET_PATH = MODELS_DIR / "synthetic_training_dataset.csv"

