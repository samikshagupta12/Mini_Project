"""Unit tests for online question API fetcher and topic classifier."""
import pytest
from database.api_fetcher import classify_question_topic, map_api_difficulty


def test_classify_question_topic_rules():
    assert classify_question_topic("How do decorators work in Python?") == "Python Programming"
    assert classify_question_topic("Explain Floyd's cycle detection in a linked list.") == "Data Structures and Algorithms"
    assert classify_question_topic("What are ACID transaction guarantees?") in ("Database Management Systems", "SQL and MongoDB")
    assert classify_question_topic("Explain the difference between TCP and UDP.") == "Computer Networks"
    assert classify_question_topic("What causes deadlock and thrashing in an operating system?") == "Operating Systems"
    assert classify_question_topic("Explain bias and variance in machine learning.") == "Machine Learning"
    assert classify_question_topic("How do you detect outliers using IQR in pandas?") == "Data Analysis"
    assert classify_question_topic("Explain polymorphism and inheritance in OOP.") == "Object-Oriented Programming"


def test_map_api_difficulty():
    assert map_api_difficulty("easy") == "Beginner"
    assert map_api_difficulty("medium") == "Intermediate"
    assert map_api_difficulty("hard") == "Advanced"
    assert map_api_difficulty("EASY") == "Beginner"
    assert map_api_difficulty("unknown") == "Beginner"

