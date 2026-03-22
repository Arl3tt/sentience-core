"""
PII v1.0 Phase 3 — User Cognitive Model
User Learning Analytics: Extract patterns from user's execution history.
"""
from typing import Dict, Any, List, Tuple
from core.memory.episodic_store import EpisodicStore
import statistics


class UserLearningAnalytics:
    """
    Analyze user's learning patterns from episodic memory.

    Computes:
    - Improvement trajectory (are they getting better?)
    - Complexity preferences (which difficulty levels work best?)
    - Fatigue patterns (when does user get tired?)
    - Strategy effectiveness (what strategies work for THIS user?)
    - Learning rate (how fast does user improve?)
    """

    def __init__(self, episodic_store: EpisodicStore):
        """Initialize with access to episodic memory."""
        self.episodic = episodic_store

    def compute_improvement_trajectory(self, task_id: str) -> Dict[str, Any]:
        """
        Analyze how user improved on a specific task.

        Returns:
        - improvement_rate: Success score delta per cycle
        - cycles_to_plateau: When learning stopped improving
        - steepness: How fast learning happened initially
        """
        history = self.episodic.get_task_history(task_id)
        if not history or len(history) < 2:
            return {"status": "insufficient_data"}

        success_scores = [h.get("success_score", 0.5) for h in history]

        # Compute improvement rate
        first_half = success_scores[:len(success_scores)//2]
        second_half = success_scores[len(success_scores)//2:]

        avg_first = statistics.mean(first_half) if first_half else 0.5
        avg_second = statistics.mean(second_half) if second_half else 0.5
        total_improvement = avg_second - avg_first

        # Find plateau
        cycles_to_plateau = len(history)
        for i in range(1, len(success_scores)):
            if abs(success_scores[i] - success_scores[i-1]) < 0.02:  # Plateaued
                cycles_to_plateau = i
                break

        return {
            "improvement_rate": total_improvement,
            "cycles_to_plateau": cycles_to_plateau,
            "steepness": (avg_second - avg_first) / max(len(history), 1),
            "first_half_avg": avg_first,
            "second_half_avg": avg_second,
            "total_cycles": len(history)
        }

    def compute_complexity_preference(self, task_histories: List[str]) -> Dict[str, Any]:
        """
        Analyze which complexity levels work best for user.

        Returns:
        - optimal_complexity: Best performing complexity level
        - difficulty_map: Complexity -> average_success_rate
        """
        complexity_scores = {}

        for task_id in task_histories:
            history = self.episodic.get_task_history(task_id)
            if not history:
                continue

            # Get task complexity (assume consistent per task)
            task_data = self.episodic._get_task_metadata(task_id)
            if task_data:
                complexity = task_data.get("complexity", 0.5)
                success_scores = [h.get("success_score", 0.5) for h in history]
                avg_success = statistics.mean(success_scores)

                if complexity not in complexity_scores:
                    complexity_scores[complexity] = []
                complexity_scores[complexity].append(avg_success)

        # Compute averages
        difficulty_map = {
            c: statistics.mean(scores)
            for c, scores in complexity_scores.items()
        }

        if not difficulty_map:
            return {"status": "insufficient_data"}

        optimal = max(difficulty_map.items(), key=lambda x: x[1])

        return {
            "optimal_complexity": optimal[0],
            "optimal_success_rate": optimal[1],
            "difficulty_map": {f"{k:.2f}": f"{v:.3f}" for k, v in difficulty_map.items()},
            "complexity_range": (min(difficulty_map.keys()), max(difficulty_map.keys()))
        }

    def compute_fatigue_pattern(self, task_histories: List[str]) -> Dict[str, Any]:
        """
        Analyze user's fatigue accumulation pattern.

        Returns:
        - fatigue_accumulation_rate: How fast fatigue builds
        - recovery_time: Cycles needed to recover from high fatigue
        - peak_fatigue_tendency: How high fatigue gets
        """
        fatigue_readings = []

        for task_id in task_histories:
            history = self.episodic.get_task_history(task_id)
            if not history:
                continue

            for record in history:
                if "fatigue" in record:
                    fatigue_readings.append(record["fatigue"])

        if not fatigue_readings or len(fatigue_readings) < 3:
            return {"status": "insufficient_data"}

        # Compute accumulation rate (slope of fatigue over cycles)
        accumulation_rates = []
        for i in range(1, len(fatigue_readings)):
            rate = fatigue_readings[i] - fatigue_readings[i-1]
            accumulation_rates.append(rate)

        avg_accumulation = statistics.mean(accumulation_rates)

        return {
            "avg_fatigue": statistics.mean(fatigue_readings),
            "peak_fatigue": max(fatigue_readings),
            "min_fatigue": min(fatigue_readings),
            "accumulation_rate_per_cycle": avg_accumulation,
            "fatigue_variance": statistics.variance(fatigue_readings) if len(fatigue_readings) > 1 else 0.0
        }

    def compute_strategy_effectiveness(self, task_histories: List[str]) -> Dict[str, Any]:
        """
        Compare effectiveness of different strategies for THIS user.

        Returns:
        - best_strategy: Strategy with highest average success
        - strategy_rankings: All strategies ranked by effectiveness
        """
        strategy_performance = {}

        for task_id in task_histories:
            history = self.episodic.get_task_history(task_id)
            if not history:
                continue

            for record in history:
                strategy = record.get("strategy", "unknown")
                success_score = record.get("success_score", 0.5)

                if strategy not in strategy_performance:
                    strategy_performance[strategy] = []
                strategy_performance[strategy].append(success_score)

        # Compute averages and counts
        rankings = {}
        for strategy, scores in strategy_performance.items():
            avg = statistics.mean(scores)
            rankings[strategy] = {
                "avg_success_rate": avg,
                "num_uses": len(scores),
                "min_success": min(scores),
                "max_success": max(scores)
            }

        if not rankings:
            return {"status": "insufficient_data"}

        best = max(rankings.items(), key=lambda x: x[1]["avg_success_rate"])

        return {
            "best_strategy": best[0],
            "best_strategy_success_rate": best[1]["avg_success_rate"],
            "strategy_rankings": rankings
        }

    def compute_learning_rate(self, task_histories: List[str]) -> Dict[str, Any]:
        """
        Compute how fast user learns across multiple tasks.

        Returns:
        - avg_learning_rate: Average improvement per cycle across tasks
        - learning_consistency: How consistent is learning across tasks
        """
        improvement_rates = []

        for task_id in task_histories:
            trajectory = self.compute_improvement_trajectory(task_id)
            if "improvement_rate" in trajectory:
                improvement_rates.append(trajectory["improvement_rate"])

        if not improvement_rates:
            return {"status": "insufficient_data"}

        avg_rate = statistics.mean(improvement_rates)
        consistency = 1.0 - (statistics.stdev(improvement_rates) / (abs(avg_rate) + 0.01)) if len(improvement_rates) > 1 else 1.0

        return {
            "avg_learning_rate": avg_rate,
            "learning_consistency": max(0.0, min(1.0, consistency)),
            "learning_variance": statistics.variance(improvement_rates) if len(improvement_rates) > 1 else 0.0,
            "num_tasks_analyzed": len(improvement_rates)
        }

    def generate_user_analytics_report(self, task_histories: List[str]) -> Dict[str, Any]:
        """
        Generate comprehensive analytics report for user.
        """
        return {
            "improvement_trajectory": self.compute_improvement_trajectory(task_histories[0] if task_histories else ""),
            "complexity_preference": self.compute_complexity_preference(task_histories),
            "fatigue_pattern": self.compute_fatigue_pattern(task_histories),
            "strategy_effectiveness": self.compute_strategy_effectiveness(task_histories),
            "learning_rate": self.compute_learning_rate(task_histories)
        }
