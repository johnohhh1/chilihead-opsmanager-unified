"""
Model quality tracking and tiering system
Helps identify which models are reliable vs experimental vs unreliable
"""
from typing import Dict

# Model tier definitions based on performance and reliability
MODEL_TIERS: Dict[str, str] = {
    # Trusted - Production-ready, rarely hallucinates
    "gpt-4o": "trusted",
    "gpt-5": "trusted",
    "o1": "trusted",
    "o1-preview": "trusted",
    "gpt-oss-120b": "trusted",  # Open-weight GPT model (120B params, cloud-hosted)
    "gpt-oss": "trusted",  # User confirmed: better than GPT-5 for restaurant ops, doesn't hallucinate
    "deepseek-r1": "trusted",

    # Experimental - Good but needs validation
    "gpt-4o-mini": "experimental",
    "gpt-3.5-turbo": "experimental",
    "llama3-70b": "experimental",
    "qwen2-72b": "experimental",

    # Unreliable - Fast/cheap but hallucinates
    "llama3-8b": "unreliable",
    "phi-3": "unreliable",
    "gemma-7b": "unreliable",
    "mistral-7b": "unreliable",
}

# Default trust scores for each tier
TIER_TRUST_SCORES = {
    "trusted": 90,
    "experimental": 60,
    "unreliable": 30,
}


def get_model_tier(model_name: str) -> str:
    """
    Determine tier for a given model
    Returns 'trusted', 'experimental', or 'unreliable'
    """
    # Direct match
    if model_name in MODEL_TIERS:
        return MODEL_TIERS[model_name]

    # Fuzzy matching for model families
    if "gpt-5" in model_name or "o1" in model_name or "o3" in model_name:
        return "trusted"

    if "gpt-4" in model_name:
        if "mini" in model_name:
            return "experimental"
        return "trusted"

    if "gpt-oss" in model_name or "oss-120b" in model_name or "deepseek" in model_name:
        return "trusted"

    if "70b" in model_name or "72b" in model_name:
        return "experimental"

    if "7b" in model_name or "8b" in model_name:
        return "unreliable"

    # Unknown models default to experimental
    return "experimental"


def get_default_trust_score(model_name: str) -> int:
    """Get initial trust score for a model based on its tier"""
    tier = get_model_tier(model_name)
    return TIER_TRUST_SCORES[tier]


def should_auto_reanalyze(
    model_tier: str,
    trust_score: int,
    priority_score: int,
    days_old: int = 0
) -> Dict[str, any]:
    """
    Determine if an email should be automatically re-analyzed
    Returns {should_reanalyze: bool, reason: str}
    """
    # Unreliable models on high-priority emails = always reanalyze
    if model_tier == "unreliable" and priority_score > 70:
        return {
            "should_reanalyze": True,
            "reason": "upgrade_to_better_model",
            "suggested_model": "oss-120b-cloud"
        }

    # Low trust score on urgent emails
    if trust_score < 40 and priority_score > 80:
        return {
            "should_reanalyze": True,
            "reason": "low_trust_urgent_email",
            "suggested_model": "gpt-4o"
        }

    # Experimental models older than 7 days for important emails
    if model_tier == "experimental" and days_old > 7 and priority_score > 60:
        return {
            "should_reanalyze": True,
            "reason": "validate_old_experimental_analysis",
            "suggested_model": "oss-120b-cloud"
        }

    return {"should_reanalyze": False, "reason": None}


def update_trust_score(current_score: int, feedback: str) -> int:
    """
    Adjust trust score based on user feedback
    Returns new trust score (0-100)
    """
    adjustments = {
        "accurate": +5,
        "missed_details": -3,
        "hallucinated": -20,  # Severe penalty
        "wrong_priority": -10,
    }

    adjustment = adjustments.get(feedback, 0)
    new_score = current_score + adjustment

    # Clamp between 0-100
    return max(0, min(100, new_score))


def get_recommended_model(
    priority_score: int,
    has_images: bool = False,
    preferred_model: str = None
) -> str:
    """
    Recommend best model for analyzing an email
    Based on priority and content type

    Args:
        priority_score: 0-100, how urgent/important the email is
        has_images: Whether email contains images (needs vision model)
        preferred_model: User's preferred model (overrides defaults)
    """
    # If user has a preferred model, use it for high-priority
    if preferred_model and priority_score > 70:
        return preferred_model

    # Vision models for emails with images
    if has_images:
        if priority_score > 70:
            return "gpt-4o"  # Best vision model
        return "gpt-4o-mini"  # Cheap vision model

    # Default recommendations by priority
    if priority_score > 80:
        return "gpt-4o"  # Safe default for high priority

    if priority_score > 50:
        return "gpt-4o-mini"

    # Low priority = cheap is fine
    return "gpt-4o-mini"
