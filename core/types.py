"""
PII v1.0 Type Definitions
Core type system for the cognitive AI execution system.
"""
from typing import Any, Dict, List
from typing_extensions import TypedDict


class CognitiveState(TypedDict):
    """Real-time cognitive state of the system."""
    focus: float  # 0.0–1.0
    fatigue: float  # 0.0–1.0
    cognitive_load: float  # 0.0–1.0
    learning_efficiency: float  # 0.0–1.0


class Feedback(TypedDict):
    """Standardized feedback from agent execution."""
    success_score: float  # 0.0–1.0
    efficiency_score: float  # 0.0–1.0
    cognitive_load: float  # 0.0–1.0
    errors: List[str]


class Task(TypedDict):
    """Task definition."""
    id: str
    description: str
    complexity: float  # 0.0–1.0


class Strategy(TypedDict):
    """Adaptive strategy for task execution."""
    approach: str
    difficulty_modifier: float  # scales task difficulty


class SystemState(TypedDict):
    """
    Shared system state across all agents.
    This is the central source of truth for the cognitive system.
    """
    task: Task
    user_state: Dict[str, Any]
    cognitive_state: CognitiveState
    history: List[Dict[str, Any]]
    strategy: Strategy
