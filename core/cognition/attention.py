"""
PII v1.0 L2 — Cognitive Engine: Attention Module
Dynamically computes focus based on recent performance.
"""
from core.types import SystemState


def compute_attention(state: SystemState) -> float:
    """
    Attention (focus) = success-driven engagement.

    Increases when:
    - Recent actions succeed
    - Errors are low or decreasing

    Decreases when:
    - Recent errors accumulate
    - Success rate drops

    Range: [0.0, 1.0]
    """
    history = state["history"]

    if not history:
        # Fresh start = baseline focus
        return 0.5

    # Look at last 5 actions (recent performance window)
    recent_actions = history[-5:]
    recent_count = len(recent_actions)

    # Count successes: actions with no errors and positive intent
    successes = sum(
        1 for action in recent_actions
        if action.get("success", True)  # Default to success if not specified
    )

    success_rate = successes / recent_count if recent_count > 0 else 0.5

    # Error count in recent history
    errors_recently = sum(
        len(action.get("errors", []))
        for action in recent_actions
    )

    # Penalty for errors
    error_penalty = min(errors_recently * 0.1, 0.5)

    # Compute focus: success-driven with error penalty
    attention = (success_rate * 0.8) + (0.2 * (1.0 - error_penalty))

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, attention))
