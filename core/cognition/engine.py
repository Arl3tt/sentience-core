"""
PII v1.0 L2 — Cognitive Engine (Orchestrator)
Coordinates all cognition modules and updates SystemState.
"""
from core.types import SystemState
from core.cognition import attention, fatigue, load, learning


def update_cognitive_state(state: SystemState) -> SystemState:
    """
    Main orchestrator: compute all 4 cognitive metrics and update state.

    Call this before each agent execution to refresh cognition.

    Flow:
    1. Compute attention (based on recent success)
    2. Compute fatigue (based on action frequency + quality decay)
    3. Compute load (based on task complexity + attention + fatigue)
    4. Compute learning (based on improvement trajectory)

    Args:
        state: SystemState to update

    Returns:
        Updated SystemState with fresh cognitive_state values
    """

    # Step 1: Compute attention (feedback-driven focus)
    new_focus = attention.compute_attention(state)

    # Step 2: Compute fatigue (resource depletion)
    new_fatigue = fatigue.compute_fatigue(state)

    # Temporarily update state for load computation (load depends on focus/fatigue)
    state["cognitive_state"]["focus"] = new_focus
    state["cognitive_state"]["fatigue"] = new_fatigue

    # Step 3: Compute load (effort required given current state)
    new_load = load.compute_cognitive_load(state)

    # Step 4: Compute learning efficiency (improvement rate)
    new_learning_eff = learning.compute_learning_efficiency(state)

    # Update cognitive state with all values
    state["cognitive_state"] = {
        "focus": new_focus,
        "fatigue": new_fatigue,
        "cognitive_load": new_load,
        "learning_efficiency": new_learning_eff
    }

    return state


def get_cognitive_summary(state: SystemState) -> dict:
    """
    Returns a human-readable summary of current cognitive state.
    Useful for debugging and visualization.
    """
    cog = state["cognitive_state"]
    return {
        "focus": f"{cog['focus']:.2f}",
        "fatigue": f"{cog['fatigue']:.2f}",
        "cognitive_load": f"{cog['cognitive_load']:.2f}",
        "learning_efficiency": f"{cog['learning_efficiency']:.2f}",
        "status": get_cognitive_status(cog)
    }


def get_cognitive_status(cog: dict) -> str:
    """
    Returns a status string describing the cognitive state.
    """
    load = cog["cognitive_load"]
    focus = cog["focus"]
    fatigue = cog["fatigue"]

    if load > 0.8:
        return "🔴 OVERLOADED"
    elif fatigue > 0.7:
        return "🟡 FATIGUED"
    elif focus < 0.3:
        return "🟠 UNFOCUSED"
    elif focus > 0.8 and load < 0.4 and fatigue < 0.3:
        return "🟢 OPTIMAL"
    else:
        return "🔵 NORMAL"
