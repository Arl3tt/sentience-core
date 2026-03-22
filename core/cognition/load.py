"""
PII v1.0 L2 — Cognitive Engine: Load Module
Dynamically computes cognitive load.
"""
from core.types import SystemState


def compute_cognitive_load(state: SystemState) -> float:
    """
    Cognitive Load = mental effort required relative to capacity.

    Increases when:
    - Task complexity is high
    - Attention is low (struggling to focus)
    - Fatigue is high (depleted resources)

    Decreases when:
    - Task is simple
    - Attention is high
    - System is well-rested

    Range: [0.0, 1.0]
    """
    task = state["task"]
    history = state["history"]

    # Base load: task complexity
    base_load = task["complexity"]

    # Import current cognitive metrics (computed earlier in engine)
    # These are available from previous computation step
    current_focus = state["cognitive_state"].get("focus", 0.5)
    current_fatigue = state["cognitive_state"].get("fatigue", 0.0)

    # Focus modifier: low focus means higher load
    # (struggling to focus = more cognitive effort)
    focus_modifier = 1.0 - current_focus  # inverted

    # Fatigue modifier: tired people find things harder
    fatigue_modifier = current_fatigue * 0.5

    # Task history modifier: more actions in history = contextual complexity
    history_complexity = min(len(history) / 100.0, 0.3)

    # Combine all factors
    total_load = (
        (base_load * 0.5) +           # Task complexity (primary)
        (focus_modifier * 0.2) +       # Attention impact
        (fatigue_modifier * 0.2) +     # Fatigue impact
        (history_complexity * 0.1)     # Context complexity
    )

    return max(0.0, min(1.0, total_load))
