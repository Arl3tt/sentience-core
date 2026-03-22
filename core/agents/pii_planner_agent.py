"""
PII v1.0 Planner Agent (L1 — Intelligence Kernel)
Example agent implementing the cognitive loop.
"""
from typing import Tuple

from core.base_agent import BaseAgent
from core.types import SystemState, Feedback


class PlannerAgent(BaseAgent):
    """
    Planner: Decomposes tasks and creates execution strategies.
    Reads from: task, cognitive_state, strategy
    Writes to: history, strategy (via learn)
    """

    def __init__(self):
        super().__init__("Planner")

    def run(self, state: SystemState) -> Tuple[SystemState, dict]:
        """
        Creates a plan based on task and cognitive state.
        Adjusts complexity based on current cognitive load.
        """
        task = state["task"]
        strategy = state["strategy"]

        # Adjust task complexity based on strategy modifier
        adjusted_complexity = task["complexity"] * strategy["difficulty_modifier"]

        # Create plan decomposition
        plan = {
            "original_complexity": task["complexity"],
            "adjusted_complexity": adjusted_complexity,
            "steps": [
                f"Analyze task: {task['description']}",
                "Break into subtasks",
                "Estimate resource requirements",
                "Execute sequentially"
            ],
            "estimated_cognitive_load": min(adjusted_complexity * 0.8, 1.0)
        }

        # Log to history
        state["history"].append({
            "agent": self.name,
            "action": "plan_created",
            "plan": plan
        })

        return state, plan

    def evaluate(self, state: SystemState, output: dict) -> Feedback:
        """
        Evaluates plan quality based on complexity alignment and efficiency.
        """
        adjusted_complexity = output["adjusted_complexity"]
        cognitive_load = state["cognitive_state"]["cognitive_load"]

        # Success: plan complexity is well-aligned (close to 0.5 is ideal)
        success = 1.0 - abs(adjusted_complexity - 0.5)

        # Efficiency: inversely related to current cognitive load
        efficiency = 1.0 - cognitive_load

        return {
            "success_score": max(0.0, min(1.0, success)),
            "efficiency_score": max(0.0, min(1.0, efficiency)),
            "cognitive_load": cognitive_load,
            "errors": []
        }

    def learn(self, state: SystemState, feedback: Feedback) -> SystemState:
        """
        Adaptive learning: adjust difficulty modifier based on feedback.

        Rules:
        - If cognitive load is too high (>0.7): reduce difficulty
        - If success is excellent (>0.8): increase difficulty
        """
        current_modifier = state["strategy"]["difficulty_modifier"]

        if feedback["cognitive_load"] > 0.7:
            # Task is too cognitively demanding
            state["strategy"]["difficulty_modifier"] = current_modifier * 0.9
        elif feedback["success_score"] > 0.8:
            # Task is going well, can increase difficulty
            state["strategy"]["difficulty_modifier"] = min(current_modifier * 1.1, 2.0)

        # Clamp to reasonable bounds
        state["strategy"]["difficulty_modifier"] = max(0.5, min(2.0, state["strategy"]["difficulty_modifier"]))

        return state
