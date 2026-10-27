"""Unit tests for personalized learning roadmap generation."""
import pytest
from modules.learning_roadmap import build_roadmap_for_assessment
from config.settings import TOPICS


def test_build_roadmap_weak_topics():
    assessment = {
        "topic_scores": {
            "Python Programming": 90.0,
            "Data Structures and Algorithms": 35.0,  # Weak -> High priority
            "Database Management Systems": 65.0,    # Moderate -> Medium priority
            "Operating Systems": 40.0,              # Weak -> High priority
            "Computer Networks": 85.0,              # Strong -> excluded
            "SQL and MongoDB": 75.0,                # Moderate
            "Object-Oriented Programming": 82.0,    # Strong -> excluded
            "Machine Learning": 45.0,               # Weak -> High priority
            "Data Analysis": 88.0,                  # Strong -> excluded
            "Problem-Solving Skills": 30.0,         # Weak -> High priority
        }
    }

    tasks = build_roadmap_for_assessment(assessment, target_role="Software Engineer")

    # Only topics with score < 80 should be included: DSA (35), OS (40), ML (45), Problem-Solving (30), DBMS (65), SQL (75) = 6 topics
    assert len(tasks) == 6
    
    # Verify lowest score is ordered first
    assert tasks[0]["topic"] == "Problem-Solving Skills"
    assert tasks[0]["current_score"] == 30.0
    assert "High" in tasks[0]["priority"]

    # Verify task fields
    for t in tasks:
        assert "concepts" in t
        assert "exercises" in t
        assert "project" in t
        assert "duration" in t
        assert t["completed"] is False

