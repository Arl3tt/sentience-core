"""
PII v1.0 System State Management
Initialization and utilities for shared system state.
"""
from core.types import SystemState


def initialize_system_state() -> SystemState:
    """
    Creates a fresh system state with sensible defaults.
    L3 (Adaptive Loop) will update these values dynamically.
    """
    return {
        "task": {
            "id": "task_001",
            "description": "Default task",
            "complexity": 0.5
        },
        "user_state": {},
        "cognitive_state": {
            "focus": 0.5,
            "fatigue": 0.5,
            "cognitive_load": 0.5,
            "learning_efficiency": 0.5
        },
        "history": [],
        "strategy": {
            "approach": "default",
            "difficulty_modifier": 1.0
        }
    }


def reset_history(state: SystemState) -> SystemState:
    """Clear history while preserving other state."""
    state["history"] = []
    return state


def get_last_action(state: SystemState) -> dict | None:
    """Get the most recent action from history."""
    if state["history"]:
        return state["history"][-1]
    return None
