"""
PII v1.0 L2 — Cognitive Engine: Fatigue Module
Dynamically computes resource depletion.
"""
from core.types import SystemState


def compute_fatigue(state: SystemState) -> float:
    """
    Fatigue = resource depletion from continuous operation.

    Increases when:
    - Many consecutive actions without break
    - Output quality declines

    Decreases naturally over time (recovery).

    Range: [0.0, 1.0]
    """
    history = state["history"]

    if not history:
        return 0.0  # Fresh start = no fatigue

    # Count consecutive recent actions (more = more fatigue)
    action_count = min(len(history) / 10.0, 1.0)  # Normalize by 10 actions max

    # Quality decay: look at success trend
    # If recent actions are worse than older ones, fatigue increases
    recent_actions = history[-5:] if len(history) >= 5 else history
    older_actions = history[-10:-5] if len(history) >= 10 else []

    if recent_actions and older_actions:
        recent_success = sum(1 for a in recent_actions if a.get("success", True))
        older_success = sum(1 for a in older_actions if a.get("success", True))

        recent_rate = recent_success / len(recent_actions)
        older_rate = older_success / len(older_actions)

        # If performance declines, fatigue is higher
        quality_decay = max(0.0, older_rate - recent_rate)
    else:
        quality_decay = 0.0

    # Accumulate fatigue: action frequency + quality decline
    fatigue = (action_count * 0.6) + (quality_decay * 0.4)

    # Natural recovery factor: fatigue decays over time
    # (every 20 actions represent one "recovery cycle")
    recovery_factor = 1.0 - (1.0 / max(5.0 + len(history), 20.0))
    fatigue *= recovery_factor

    return max(0.0, min(1.0, fatigue))
