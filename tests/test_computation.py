"""Unit tests for system-wide mathematical computation engine."""
import pytest
from modules.computation_engine import (
    calculate_role_weighted_score,
    calculate_composite_readiness_index,
    ROLE_TOPIC_WEIGHTS,
)
from config.settings import TOPICS


def test_role_weighted_score_software_engineer():
    # Software Engineer prioritizes DSA, Problem Solving, OOP
    scores = {topic: 50.0 for topic in TOPICS}
    scores["Data Structures and Algorithms"] = 90.0  # weight: 0.20
    scores["Problem-Solving Skills"] = 90.0         # weight: 0.20
    scores["Object-Oriented Programming"] = 90.0    # weight: 0.15

    raw_avg = sum(scores.values()) / 10.0  # 62.0
    role_score = calculate_role_weighted_score(scores, "Software Engineer")

    # Since the 3 highest weighted topics (sum weight 0.55) are 90, role_score should exceed raw_avg
    assert role_score > raw_avg
    assert role_score == pytest.approx(72.0, rel=1e-1)


def test_role_weighted_score_data_scientist():
    # Data Scientist prioritizes ML, Python, Data Analysis
    scores = {topic: 40.0 for topic in TOPICS}
    scores["Machine Learning"] = 95.0     # weight: 0.25
    scores["Python Programming"] = 90.0   # weight: 0.20
    scores["Data Analysis"] = 90.0        # weight: 0.20

    raw_avg = sum(scores.values()) / 10.0
    role_score = calculate_role_weighted_score(scores, "Data Scientist")

    assert role_score > raw_avg
    assert role_score > 70.0


def test_composite_readiness_index():
    # High score, high roadmap completion, high practice
    res_elite = calculate_composite_readiness_index(
        role_weighted_score=92.0,
        roadmap_completion_pct=100.0,
        practice_mastery_pct=90.0,
        has_practice=True
    )
    assert res_elite["index_score"] >= 90.0
    assert res_elite["grade"] == "A+"
    assert "Elite" in res_elite["tier"]

    # Developing score
    res_dev = calculate_composite_readiness_index(
        role_weighted_score=45.0,
        roadmap_completion_pct=10.0,
        practice_mastery_pct=0.0,
        has_practice=False
    )
    assert res_dev["index_score"] < 50.0
    assert res_dev["grade"] == "D"

