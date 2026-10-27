"""Performance metrics calculation, score classification, and UI formatting helpers."""
from typing import Dict, Any, List, Tuple
import numpy as np
from config.settings import TOPICS, STRONG_THRESHOLD, MODERATE_THRESHOLD


def classify_topic_score(score: float) -> str:
    """
    Classifies a numerical score into performance categories:
    - 80 to 100: Strong Topic
    - 50 to 79: Moderate Topic
    - Below 50: Weak Topic
    """
    if score >= STRONG_THRESHOLD:
        return "Strong"
    elif score >= MODERATE_THRESHOLD:
        return "Moderate"
    else:
        return "Weak"


def calculate_assessment_metrics(scores: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculates overall average, category distributions, topic rankings,
    and identifies highest and lowest scoring areas.
    """
    topic_scores = {t: float(scores.get(t, 0.0)) for t in TOPICS}
    values = list(topic_scores.values())
    
    overall_avg = round(float(np.mean(values)), 1)
    
    strong_topics = []
    moderate_topics = []
    weak_topics = []
    topic_classifications = {}

    for t, s in topic_scores.items():
        cat = classify_topic_score(s)
        topic_classifications[t] = cat
        if cat == "Strong":
            strong_topics.append(t)
        elif cat == "Moderate":
            moderate_topics.append(t)
        else:
            weak_topics.append(t)

    # Rank topics descending
    ranked_tuples = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
    rankings = [
        {"rank": idx + 1, "topic": t, "score": s, "classification": topic_classifications[t]}
        for idx, (t, s) in enumerate(ranked_tuples)
    ]

    highest_topic = ranked_tuples[0] if ranked_tuples else ("N/A", 0.0)
    lowest_topic = ranked_tuples[-1] if ranked_tuples else ("N/A", 0.0)

    return {
        "overall_average": overall_avg,
        "strong_topics": strong_topics,
        "moderate_topics": moderate_topics,
        "weak_topics": weak_topics,
        "topic_classifications": topic_classifications,
        "highest_topic": highest_topic[0],
        "highest_score": highest_topic[1],
        "lowest_topic": lowest_topic[0],
        "lowest_score": lowest_topic[1],
        "rankings": rankings,
        "topic_scores": topic_scores,
    }


def get_status_color(category: str) -> str:
    """Returns hexadecimal colors for status categories."""
    if category in ("Strong", "Interview Ready"):
        return "#2ECC71"  # Emerald Green
    elif category in ("Moderate", "Intermediate / Partially Ready"):
        return "#F39C12"  # Amber Orange
    else:
        return "#E74C3C"  # Crimson Red

