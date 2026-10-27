"""Unit tests for data validation logic."""
import pytest
from utils.validators import (
    validate_email,
    validate_student_profile,
    validate_scores,
    validate_question,
)
from config.settings import TOPICS


def test_validate_email_valid():
    valid_emails = [
        "student@college.edu",
        "john.doe@company.com",
        "dev_user+test@sub.domain.org",
    ]
    for email in valid_emails:
        ok, msg = validate_email(email)
        assert ok is True
        assert msg == ""


def test_validate_email_invalid():
    invalid_emails = [
        "",
        "plainaddress",
        "@missingusername.com",
        "missingatsign.com",
        "student@.com",
    ]
    for email in invalid_emails:
        ok, msg = validate_email(email)
        assert ok is False
        assert len(msg) > 0


def test_validate_student_profile_success():
    data = {
        "name": "Jane Doe",
        "email": "jane@university.edu",
        "education": "B.Tech / B.E. (Computer Science / IT)",
        "course": "Computer Science and Engineering",
        "target_role": "Software Engineer",
        "experience_level": "Student / College Fresher",
        "preferred_language": "Python",
    }
    ok, errors = validate_student_profile(data)
    assert ok is True
    assert len(errors) == 0


def test_validate_student_profile_missing_fields():
    data = {
        "name": "",
        "email": "invalid-email",
    }
    ok, errors = validate_student_profile(data)
    assert ok is False
    assert len(errors) > 0


def test_validate_scores_valid():
    scores = {topic: 75.0 for topic in TOPICS}
    ok, errors = validate_scores(scores)
    assert ok is True
    assert len(errors) == 0


def test_validate_scores_out_of_bounds():
    scores = {topic: 70.0 for topic in TOPICS}
    scores["Python Programming"] = 105.0  # > 100
    scores["Operating Systems"] = -5.0   # < 0
    ok, errors = validate_scores(scores)
    assert ok is False
    assert any("105" in e for e in errors)
    assert any("-5" in e for e in errors)


def test_validate_scores_missing_topic():
    scores = {topic: 60.0 for topic in TOPICS}
    del scores["Python Programming"]
    ok, errors = validate_scores(scores)
    assert ok is False
    assert any("Python Programming" in e for e in errors)


def test_validate_question_valid():
    q_data = {
        "question": "What is the difference between a process and a thread in OS?",
        "topic": "Operating Systems",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "answer": "A process has isolated memory; threads share memory.",
        "explanation": "Threads share process address space, making context switching cheaper.",
    }
    ok, errors = validate_question(q_data)
    assert ok is True
    assert len(errors) == 0


def test_validate_question_invalid():
    q_data = {
        "question": "Short",
        "topic": "Nonexistent Topic",
        "difficulty": "SuperHard",
        "question_type": "InvalidType",
        "answer": "",
        "explanation": "",
    }
    ok, errors = validate_question(q_data)
    assert ok is False
    assert len(errors) >= 4

