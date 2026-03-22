"""
PII v1.0 L3 — Adaptive Learning Loop
Orchestrates the full STATE → ACTION → RESULT → SCORE → UPDATE cycle.
"""
from typing import Tuple, Optional
from core.types import SystemState
from core.base_agent import BaseAgent
from core.cognition import update_cognitive_state, get_cognitive_status


class AdaptiveLoop:
    """
    Main orchestrator for the adaptive learning cycle.

    Flow:
    1. STATE: Current system_state with task, cognition, strategy
    2. ACTION: Agent executes run(state)
    3. RESULT: Agent produces output
    4. SCORE: Agent evaluates output (feedback)
    5. UPDATE: Agent learns from feedback, state is updated
    6. STATE': Refreshed state ready for next cycle
    """

    def __init__(self, max_cycles: int = 100, verbose: bool = True):
        self.max_cycles = max_cycles
        self.verbose = verbose
        self.cycle_count = 0

    def execute_cycle(
        self,
        state: SystemState,
        agent: BaseAgent,
        update_cognition: bool = True
    ) -> Tuple[SystemState, dict]:
        """
        Execute one full adaptive loop cycle.

        Args:
            state: Current SystemState
            agent: Agent to execute
            update_cognition: If True, refresh L2 metrics before evaluation

        Returns:
            (updated_state, cycle_report)
        """
        self.cycle_count += 1

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"[CYCLE {self.cycle_count}] {agent.name} → Adaptive Loop")
            print(f"{'='*60}")

        # PHASE 1: Update Cognition (L2)
        if update_cognition:
            state = update_cognitive_state(state)
            if self.verbose:
                status = get_cognitive_status(state["cognitive_state"])
                print(f"[L2] Cognition updated: {status}")

        # PHASE 2: ACTION - Agent runs
        if self.verbose:
            print(f"[L1] {agent.name}.run() executing...")
        state, output = agent.run(state)
        if self.verbose:
            print(f"[L1] ✓ {agent.name} produced output")

        # PHASE 3: SCORE - Agent evaluates
        if self.verbose:
            print(f"[L1] {agent.name}.evaluate() scoring...")
        feedback = agent.evaluate(state, output)
        if self.verbose:
            print(f"[L1] ✓ Score: success={feedback['success_score']:.2f}, "
                  f"efficiency={feedback['efficiency_score']:.2f}")

        # PHASE 4: UPDATE - Agent learns
        if self.verbose:
            old_mod = state["strategy"]["difficulty_modifier"]
        state = agent.learn(state, feedback)
        if self.verbose:
            new_mod = state["strategy"]["difficulty_modifier"]
            if abs(new_mod - old_mod) > 0.01:
                print(f"[L1] ✓ Strategy adapted: {old_mod:.2f} → {new_mod:.2f}")

        # PHASE 5: STATE' - Prepare next cycle
        cycle_report = {
            "cycle": self.cycle_count,
            "agent": agent.name,
            "feedback": feedback,
            "output": output,
            "strategy_modifier": state["strategy"]["difficulty_modifier"],
            "cognitive_state": state["cognitive_state"].copy(),
            "history_length": len(state["history"])
        }

        if self.verbose:
            print(f"[CYCLE {self.cycle_count}] Complete")
            print(f"{'='*60}")

        return state, cycle_report

    def execute_multi_cycle(
        self,
        state: SystemState,
        agents: list[BaseAgent],
        num_cycles: int = 1,
        round_robin: bool = True
    ) -> Tuple[SystemState, list[dict]]:
        """
        Execute multiple cycles with one or more agents.

        Args:
            state: Initial SystemState
            agents: List of agents to cycle through
            num_cycles: Number of complete cycles to run
            round_robin: If True, agents run in order. If False, same agent each cycle.

        Returns:
            (final_state, list_of_cycle_reports)
        """
        reports = []

        for cycle_num in range(num_cycles * len(agents) if round_robin else num_cycles):
            if round_robin:
                agent = agents[cycle_num % len(agents)]
            else:
                agent = agents[0]

            state, report = self.execute_cycle(state, agent)
            reports.append(report)

        return state, reports

    def get_learning_summary(self, reports: list[dict]) -> dict:
        """
        Summarize learning across multiple cycles.

        Returns metrics on improvement trajectory.
        """
        if not reports:
            return {}

        success_scores = [r["feedback"]["success_score"] for r in reports]
        efficiency_scores = [r["feedback"]["efficiency_score"] for r in reports]
        modifiers = [r["strategy_modifier"] for r in reports]

        return {
            "total_cycles": len(reports),
            "avg_success": sum(success_scores) / len(success_scores),
            "avg_efficiency": sum(efficiency_scores) / len(efficiency_scores),
            "success_trend": success_scores[-1] - success_scores[0],  # Delta
            "strategy_evolution": modifiers[-1] - modifiers[0],
            "max_success": max(success_scores),
            "min_success": min(success_scores),
            "peak_cycle": success_scores.index(max(success_scores)) + 1
        }

    def should_continue(self, state: SystemState, feedback: dict, cycle: int) -> bool:
        """
        Determine if the loop should continue.

        Rules:
        - Stop if success is excellent (> 0.95)
        - Stop if cognitive load is critical (> 0.9)
        - Stop if max cycles reached
        - Otherwise continue
        """
        if cycle >= self.max_cycles:
            return False

        if feedback["success_score"] > 0.95:
            if self.verbose:
                print("✓ Excellent performance reached, stopping.")
            return False

        if state["cognitive_state"]["cognitive_load"] > 0.9:
            if self.verbose:
                print("⚠ Cognitive load critical, stopping for recovery.")
            return False

        return True
