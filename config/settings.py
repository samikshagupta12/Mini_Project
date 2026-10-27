"""Application configuration settings."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "ai_interview_system")
USE_MOCK_DB = os.getenv("USE_MOCK_DB", "false").lower() in ("true", "1", "yes")

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

# Machine Learning Artifact Paths
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "readiness_model.joblib"
MODEL_METADATA_PATH = MODELS_DIR / "model_metadata.json"

