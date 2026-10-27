"""Data validation functions with explicit error messages."""
import re
from typing import Dict, Any, Tuple, List
from config.settings import TOPICS, DIFFICULTY_LEVELS, QUESTION_TYPES

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email(email: str) -> Tuple[bool, str]:
    """Validates an email address format."""
    if not email or not isinstance(email, str):
        return False, "Email cannot be empty."
    clean_email = email.strip()
    if not EMAIL_REGEX.match(clean_email):
        return False, "Please enter a valid email address (e.g., student@university.edu)."
    return True, ""


def validate_student_profile(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates all required student profile fields.
    Returns: (is_valid, list_of_error_messages)
    """
    errors = []
    
    # Required string fields
    req_fields = {
        "name": "Full Name",
        "email": "Email Address",
        "education": "Education Level",
        "course": "Course / Degree",
        "target_role": "Target Job Role",
        "experience_level": "Experience Level",
        "preferred_language": "Preferred Programming Language",
    }
    
    for field_key, field_label in req_fields.items():
        val = data.get(field_key)
        if not val or not str(val).strip():
            errors.append(f"{field_label} is required.")

    # Email specific check
    if "email" in data and str(data["email"]).strip():
        ok, msg = validate_email(data["email"])
        if not ok:
            errors.append(msg)

    # Name length
    if "name" in data and len(str(data["name"]).strip()) < 2:
        errors.append("Full Name must be at least 2 characters long.")

    return len(errors) == 0, errors


def validate_scores(scores: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that all 10 topics are present and their scores are between 0 and 100.
    """
    errors = []
    if not isinstance(scores, dict):
        return False, ["Scores must be provided as a dictionary."]

    for topic in TOPICS:
        if topic not in scores:
            errors.append(f"Missing score for topic: '{topic}'.")
            continue
        val = scores[topic]
        try:
            num = float(val)
            if num < 0.0 or num > 100.0:
                errors.append(f"Score for '{topic}' must be between 0 and 100 (got {val}).")
        except (ValueError, TypeError):
            errors.append(f"Score for '{topic}' must be a valid number.")

    return len(errors) == 0, errors


def validate_question(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validates question schema before database insertion."""
    errors = []
    if not data.get("question") or len(str(data["question"]).strip()) < 10:
        errors.append("Question text must be at least 10 characters long.")
    if data.get("topic") not in TOPICS:
        errors.append(f"Topic must be one of: {', '.join(TOPICS)}.")
    if data.get("difficulty") not in DIFFICULTY_LEVELS:
        errors.append(f"Difficulty must be one of: {', '.join(DIFFICULTY_LEVELS)}.")
    if data.get("question_type") not in QUESTION_TYPES:
        errors.append(f"Question Type must be one of: {', '.join(QUESTION_TYPES)}.")
    if not data.get("answer") or len(str(data["answer"]).strip()) < 5:
        errors.append("Suggested answer must be at least 5 characters long.")
    if not data.get("explanation") or len(str(data["explanation"]).strip()) < 10:
        errors.append("Explanation must be at least 10 characters long.")

    return len(errors) == 0, errors

