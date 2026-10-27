"""Unit tests for assessment scoring, classification, and metrics calculations."""
import pytest
from utils.helpers import classify_topic_score, calculate_assessment_metrics
from config.settings import TOPICS


def test_classify_topic_score():
    assert classify_topic_score(100.0) == "Strong"
    assert classify_topic_score(80.0) == "Strong"
    assert classify_topic_score(79.9) == "Moderate"
    assert classify_topic_score(50.0) == "Moderate"
    assert classify_topic_score(49.9) == "Weak"
    assert classify_topic_score(0.0) == "Weak"


def test_calculate_assessment_metrics():
    # Construct defined scores
    scores = {
        "Python Programming": 90.0,            # Strong
        "Data Structures and Algorithms": 85.0, # Strong
        "Object-Oriented Programming": 70.0,    # Moderate
        "Database Management Systems": 65.0,    # Moderate
        "SQL and MongoDB": 60.0,                # Moderate
        "Operating Systems": 55.0,              # Moderate
        "Computer Networks": 45.0,              # Weak
        "Machine Learning": 40.0,               # Weak
        "Data Analysis": 30.0,                  # Weak
        "Problem-Solving Skills": 20.0,         # Weak
    }
    
    metrics = calculate_assessment_metrics(scores)

    # Average: (90+85+70+65+60+55+45+40+30+20)/10 = 560/10 = 56.0
    assert metrics["overall_average"] == 56.0
    
    # Counts
    assert len(metrics["strong_topics"]) == 2
    assert len(metrics["moderate_topics"]) == 4
    assert len(metrics["weak_topics"]) == 4

    assert "Python Programming" in metrics["strong_topics"]
    assert "Problem-Solving Skills" in metrics["weak_topics"]

    # Highest and Lowest
    assert metrics["highest_topic"] == "Python Programming"
    assert metrics["highest_score"] == 90.0
    assert metrics["lowest_topic"] == "Problem-Solving Skills"
    assert metrics["lowest_score"] == 20.0

    # Rankings structure
    assert len(metrics["rankings"]) == len(TOPICS)
    assert metrics["rankings"][0]["topic"] == "Python Programming"
    assert metrics["rankings"][-1]["topic"] == "Problem-Solving Skills"

