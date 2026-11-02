"""Secure Authentication & User Credential Management Utility."""
import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from database.collections import get_students_collection, serialize_doc, to_object_id
from utils.validators import validate_student_profile, validate_email

# PBKDF2 Constants
HASH_ALGORITHM = "sha256"
ITERATIONS = 100000


def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with a cryptographically secure salt.
    Returns: salt$hex_digest
    """
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        ITERATIONS,
    )
    return f"{salt}${key.hex()}"


def verify_password(password: str, hashed_value: str) -> bool:
    """
    Verifies a plain password against the stored salt$hex_digest string
    using constant-time comparison to prevent timing attacks.
    """
    if not hashed_value or "$" not in hashed_value:
        return False
    try:
        salt, expected_hex = hashed_value.split("$", 1)
        key = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode("utf-8"),
            salt.encode("utf-8"),
            ITERATIONS,
        )
        return hmac.compare_digest(key.hex(), expected_hex)
    except Exception:
        return False


def register_student(profile_data: Dict[str, Any], password: str) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
    """
    Validates profile data and password, hashes password, and persists new student into MongoDB.
    Returns: (is_success, student_doc, list_of_errors)
    """
    errors = []
    
    # Validate profile fields
    is_valid, val_errors = validate_student_profile(profile_data)
    if not is_valid:
        errors.extend(val_errors)

    # Validate password length
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters long.")

    if errors:
        return False, None, errors

    students_col = get_students_collection()
    if students_col is None:
        return False, None, ["Database connection unavailable. Cannot register student."]

    email = profile_data["email"].strip().lower()

    # Check for duplicate email
    if students_col.find_one({"email": email}):
        return False, None, [f"A student with email '{email}' is already registered. Please log in."]

    now = datetime.now(timezone.utc)
    new_student = {
        "name": profile_data["name"].strip(),
        "email": email,
        "password_hash": hash_password(password),
        "education": profile_data["education"],
        "course": profile_data["course"].strip(),
        "target_role": profile_data["target_role"],
        "experience_level": profile_data["experience_level"],
        "preferred_language": profile_data["preferred_language"],
        "created_at": now,
        "updated_at": now,
    }

    res = students_col.insert_one(new_student)
    new_student["_id"] = res.inserted_id
    return True, serialize_doc(new_student), []


def authenticate_student(email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Authenticates a student by email and password.
    Returns: (is_authenticated, student_doc, status_message)
    """
    clean_email = email.strip().lower()
    if not clean_email or not password:
        return False, None, "Please enter both email and password."

    students_col = get_students_collection()
    if students_col is None:
        return False, None, "Database connection unavailable."

    student = students_col.find_one({"email": clean_email})
    if not student:
        return False, None, "No registered student found with this email."

    stored_hash = student.get("password_hash")
    
    # Handle legacy accounts created prior to authentication
    if not stored_hash:
        # Update with new password hash automatically
        new_hash = hash_password(password)
        students_col.update_one({"_id": student["_id"]}, {"$set": {"password_hash": new_hash}})
        return True, serialize_doc(student), "Password set successfully. Welcome back!"

    if verify_password(password, stored_hash):
        return True, serialize_doc(student), "Login successful!"
    else:
        return False, None, "Incorrect password. Please verify and try again."


def get_or_create_demo_student(archetype: str = "ready") -> Dict[str, Any]:
    """
    Creates or retrieves a pre-configured demo student profile for 1-click evaluation.
    Archetypes:
      - 'ready': High-performing candidate (Alice Johnson)
      - 'improving': Moderate / Beginner candidate (Bob Smith)
    """
    students_col = get_students_collection()
    if students_col is None:
        raise RuntimeError("Database unavailable.")

    if archetype == "ready":
        demo_email = "alice.demo@university.edu"
        demo_name = "Alice Johnson"
        demo_role = "Software Engineer"
        demo_course = "Computer Science and Engineering"
    else:
        demo_email = "bob.demo@university.edu"
        demo_name = "Bob Smith"
        demo_role = "Data Scientist"
        demo_course = "Information Technology"

    existing = students_col.find_one({"email": demo_email})
    if existing:
        return serialize_doc(existing)

    now = datetime.now(timezone.utc)
    demo_doc = {
        "name": demo_name,
        "email": demo_email,
        "password_hash": hash_password("demo123"),
        "education": "B.Tech / B.E. (Computer Science / IT)",
        "course": demo_course,
        "target_role": demo_role,
        "experience_level": "Student / College Fresher",
        "preferred_language": "Python",
        "is_demo_account": True,
        "created_at": now,
        "updated_at": now,
    }

    res = students_col.insert_one(demo_doc)
    demo_doc["_id"] = res.inserted_id

    # Seed an initial assessment for the demo candidate
    from database.collections import get_assessments_collection
    assessments_col = get_assessments_collection()
    if assessments_col is not None:
        if archetype == "ready":
            scores = {
                "Python Programming": 90.0,
                "Data Structures and Algorithms": 86.0,
                "Object-Oriented Programming": 88.0,
                "Database Management Systems": 82.0,
                "SQL and MongoDB": 84.0,
                "Operating Systems": 80.0,
                "Computer Networks": 78.0,
                "Machine Learning": 85.0,
                "Data Analysis": 86.0,
                "Problem-Solving Skills": 90.0,
            }
        else:
            scores = {
                "Python Programming": 55.0,
                "Data Structures and Algorithms": 40.0,
                "Object-Oriented Programming": 45.0,
                "Database Management Systems": 42.0,
                "SQL and MongoDB": 48.0,
                "Operating Systems": 35.0,
                "Computer Networks": 32.0,
                "Machine Learning": 60.0,
                "Data Analysis": 58.0,
                "Problem-Solving Skills": 38.0,
            }
        from utils.helpers import calculate_assessment_metrics
        m = calculate_assessment_metrics(scores)
        assmt = {
            "student_id": demo_doc["_id"],
            "student_email": demo_email,
            "topic_scores": scores,
            "average_score": m["overall_average"],
            "strong_topics": m["strong_topics"],
            "moderate_topics": m["moderate_topics"],
            "weak_topics": m["weak_topics"],
            "created_at": now,
        }
        res_assmt = assessments_col.insert_one(assmt)
        
        # Trigger ML and Roadmap computation
        try:
            from modules.computation_engine import compute_entire_program
            compute_entire_program(demo_doc["_id"])
        except Exception:
            pass

    return serialize_doc(demo_doc)

