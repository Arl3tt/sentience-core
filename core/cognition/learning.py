"""
PII v1.0 L2 — Cognitive Engine: Learning Efficiency Module
Dynamically computes learning effectiveness.
"""
from core.types import SystemState


def compute_learning_efficiency(state: SystemState) -> float:
    """
    Learning Efficiency = rate of improvement & adaptation.

    Increases when:
    - Success rate is improving over time
    - Strategy is adapting (difficulty_modifier changing)
    - Errors are decreasing

    Decreases when:
    - Performance is stagnant or declining
    - No adaptation happening
    - Errors persist

    Range: [0.0, 1.0]
    """
    history = state["history"]
    strategy = state["strategy"]

    if len(history) < 2:
        return 0.5  # Not enough data to measure learning

    # Split history into old and new periods
    split_point = len(history) // 2
    old_period = history[:split_point]
    new_period = history[split_point:]

    # Success rate trend: is it improving?
    if old_period and new_period:
        old_success_rate = sum(1 for a in old_period if a.get("success", True)) / len(old_period)
        new_success_rate = sum(1 for a in new_period if a.get("success", True)) / len(new_period)

        improvement_trajectory = new_success_rate - old_success_rate
    else:
        improvement_trajectory = 0.0

    # Error reduction: are errors decreasing?
    old_errors = sum(len(a.get("errors", [])) for a in old_period)
    new_errors = sum(len(a.get("errors", [])) for a in new_period)

    if old_errors > 0:
        error_reduction = (old_errors - new_errors) / old_errors
    else:
        error_reduction = 0.0

    # Adaptation indicator: is strategy changing?
    # (difficulty_modifier is dynamic, so frequent changes = learning)
    recent_modifier_changes = 0
    for i in range(1, min(len(history), 10)):
        if history[i].get("strategy_updated", False):
            recent_modifier_changes += 1

    adaptation_rate = min(recent_modifier_changes / 5.0, 1.0)

    # Combine metrics
    learning_eff = (
        (max(improvement_trajectory + 0.5, 0.0) * 0.4) +  # Improvement (biased positive)
        (error_reduction * 0.3) +                          # Error reduction
        (adaptation_rate * 0.3)                            # Adaptation rate
    )

    return max(0.0, min(1.0, learning_eff))
