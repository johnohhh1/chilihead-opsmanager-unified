def score_priority(features: dict) -> float:
    """Very simple heuristic priority score in [0,1].
    features = {
        'is_direct': bool,
        'from_vip': bool,
        'has_deadline_words': bool,
        'unread_count': int,
        'hours_since_arrival': float,
        'thread_len': int,
    }
    """
    score = 0.0
    score += 0.35 if features.get('is_direct') else 0.0
    score += 0.25 if features.get('from_vip') else 0.0
    score += 0.20 if features.get('has_deadline_words') else 0.0
    score += min(0.10, 0.01 * (features.get('unread_count', 0)))
    score += min(0.10, 0.02 * max(0, 24 - features.get('hours_since_arrival', 0)))
    score += min(0.10, 0.02 * features.get('thread_len', 0))
    return max(0.0, min(1.0, score))
