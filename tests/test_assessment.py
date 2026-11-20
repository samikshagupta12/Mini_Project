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


def test_topic_categories_and_descriptions_coverage():
    from config.settings import TOPIC_CATEGORIES, TOPIC_DESCRIPTIONS
    all_cat_topics = []
    for cat, t_list in TOPIC_CATEGORIES.items():
        assert len(t_list) > 0
        all_cat_topics.extend(t_list)

    assert set(all_cat_topics) == set(TOPICS)
    for topic in TOPICS:
        assert topic in TOPIC_DESCRIPTIONS
        assert len(TOPIC_DESCRIPTIONS[topic]) > 20


def test_score_tier_details_boundaries():
    from modules.skill_assessment import get_score_tier_details
    # 0 to 25 -> Beginner
    t0 = get_score_tier_details(0)
    t25 = get_score_tier_details(25)
    assert t0["tier"] == "Beginner"
    assert t25["tier"] == "Beginner"

    # 26 to 50 -> Basic understanding
    t26 = get_score_tier_details(26)
    t50 = get_score_tier_details(50)
    assert t26["tier"] == "Basic understanding"
    assert t50["tier"] == "Basic understanding"

    # 51 to 75 -> Good understanding
    t51 = get_score_tier_details(51)
    t75 = get_score_tier_details(75)
    assert t51["tier"] == "Good understanding"
    assert t75["tier"] == "Good understanding"

    # 76 to 100 -> Advanced understanding
    t76 = get_score_tier_details(76)
    t100 = get_score_tier_details(100)
    assert t76["tier"] == "Advanced understanding"
    assert t100["tier"] == "Advanced understanding"


def test_score_level_guide():
    from config.settings import SCORE_LEVEL_GUIDE
    assert len(SCORE_LEVEL_GUIDE) == 4
    tiers = [item["tier"] for item in SCORE_LEVEL_GUIDE]
    assert "Beginner" in tiers
    assert "Basic understanding" in tiers
    assert "Good understanding" in tiers
    assert "Advanced understanding" in tiers


def test_research_data_collection():
    from database.collections import get_research_data_collection
    col = get_research_data_collection()
    # Should return either a Collection or None (if DB offline), no exceptions
    assert col is None or hasattr(col, "insert_one")

