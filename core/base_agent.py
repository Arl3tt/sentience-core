"""
PII v1.0 Base Agent Architecture
Abstract base class for all agents in the cognitive system.
"""
from abc import ABC, abstractmethod
from typing import Tuple

from core.types import SystemState, Feedback


class BaseAgent(ABC):
    """
    All agents must inherit from this class.
    Enforces the cognitive loop: run() → evaluate() → learn()
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, state: SystemState) -> Tuple[SystemState, dict]:
        """
        Executes the agent's primary function.

        Args:
            state: Current system state

        Returns:
            (updated_state, output_data)
        """
        pass

    @abstractmethod
    def evaluate(self, state: SystemState, output: dict) -> Feedback:
        """
        Evaluates the output and returns structured feedback.

        Args:
            state: System state after execution
            output: Output from run()

        Returns:
            Standardized Feedback object
        """
        pass

    @abstractmethod
    def learn(self, state: SystemState, feedback: Feedback) -> SystemState:
        """
        Updates system_state based on feedback.
        This is the learning hook for adaptation.

        Args:
            state: Current system state
            feedback: Feedback from evaluate()

        Returns:
            Updated system state
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
