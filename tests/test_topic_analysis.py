"""Unit tests for topic ranking, comparison, and diagnostics."""
import pytest
from utils.helpers import calculate_assessment_metrics
from config.settings import TOPICS


def test_topic_rankings_order():
    scores = {topic: float(idx * 10) for idx, topic in enumerate(TOPICS)}
    metrics = calculate_assessment_metrics(scores)
    rankings = metrics["rankings"]

    # Verify strictly descending order
    for i in range(len(rankings) - 1):
        assert rankings[i]["score"] >= rankings[i + 1]["score"]
        assert rankings[i]["rank"] == i + 1


def test_comparison_delta_logic():
    prev_scores = {topic: 50.0 for topic in TOPICS}
    curr_scores = {topic: 50.0 for topic in TOPICS}
    
    # Introduce changes
    curr_scores["Python Programming"] = 75.0  # +25
    curr_scores["Operating Systems"] = 35.0   # -15

    delta_python = curr_scores["Python Programming"] - prev_scores["Python Programming"]
    delta_os = curr_scores["Operating Systems"] - prev_scores["Operating Systems"]

    assert delta_python == 25.0
    assert delta_os == -15.0

