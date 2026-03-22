"""
PII v1.0 Phase 3 — User Cognitive Model
User Profile: Personalized cognitive baseline and learning patterns.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json
from pathlib import Path
from datetime import datetime


@dataclass
class CognitiveBaseline:
    """User's typical cognitive characteristics."""
    avg_focus: float  # User's average focus level
    avg_fatigue: float  # User's typical fatigue trajectory
    avg_learning_efficiency: float  # How quickly user learns
    optimal_focus_range: tuple  # (min, max) where user performs best
    optimal_complexity_range: tuple  # (min, max) task complexity user prefers
    fatigue_threshold: float  # When fatigue becomes problematic for this user
    peak_performance_hour: int  # Time of day user performs best (-1 = no pattern)


@dataclass
class LearningProfile:
    """User's learning characteristics."""
    total_tasks_completed: int
    total_cycles: int
    avg_improvement_rate: float  # Average improvement per cycle
    preferred_strategies: Dict[str, float]  # Strategy -> success_rate
    difficult_complexity_levels: list  # Complexity levels where user struggles
    strong_complexity_levels: list  # Complexity levels where user excels
    learning_curve_steepness: float  # How quickly user improves (0.0-1.0)
    pattern_recognition_strength: float  # How well user recognizes patterns


class UserProfile:
    """
    Persistent user cognitive model: "Who is this user?"

    Stores:
    - Baseline cognitive characteristics (focus, fatigue, learning patterns)
    - Optimal working conditions (complexity ranges, time of day)
    - Strategy preferences (what works best for THIS user)
    - Learning trajectory (how quickly + how deeply)
    - Work habits (when they focus best, fatigue patterns)

    Enables:
    - Personalized difficulty adjustment
    - Strategy recommendation based on user history
    - Optimal task pacing for THIS user
    - Fatigue prediction and prevention
    - Individual learning rate computation
    """

    def __init__(self, user_id: str = "default", storage_path: str = "core/personalization"):
        """Initialize user profile."""
        self.user_id = user_id
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.profile_file = self.storage_path / f"user_{user_id}_profile.json"
        self.baseline = self._load_or_create_baseline()
        self.learning = self._load_or_create_learning()

    def _load_or_create_baseline(self) -> CognitiveBaseline:
        """Load baseline or create default."""
        profile_path = self.storage_path / f"user_{self.user_id}_baseline.json"

        if profile_path.exists():
            with open(profile_path, "r") as f:
                data = json.load(f)
                return CognitiveBaseline(**data)

        # Default baseline (average user)
        baseline = CognitiveBaseline(
            avg_focus=0.65,
            avg_fatigue=0.30,
            avg_learning_efficiency=0.60,
            optimal_focus_range=(0.7, 0.95),
            optimal_complexity_range=(0.4, 0.8),
            fatigue_threshold=0.75,
            peak_performance_hour=-1  # No pattern yet
        )
        self._save_baseline(baseline)
        return baseline

    def _load_or_create_learning(self) -> LearningProfile:
        """Load learning profile or create default."""
        learn_path = self.storage_path / f"user_{self.user_id}_learning.json"

        if learn_path.exists():
            with open(learn_path, "r") as f:
                data = json.load(f)
                return LearningProfile(**data)

        # Default learning profile (novice)
        learning = LearningProfile(
            total_tasks_completed=0,
            total_cycles=0,
            avg_improvement_rate=0.05,
            preferred_strategies={},
            difficult_complexity_levels=[],
            strong_complexity_levels=[],
            learning_curve_steepness=0.5,
            pattern_recognition_strength=0.5
        )
        self._save_learning(learning)
        return learning

    def _save_baseline(self, baseline: CognitiveBaseline):
        """Save baseline to file."""
        path = self.storage_path / f"user_{self.user_id}_baseline.json"
        with open(path, "w") as f:
            json.dump({
                "avg_focus": baseline.avg_focus,
                "avg_fatigue": baseline.avg_fatigue,
                "avg_learning_efficiency": baseline.avg_learning_efficiency,
                "optimal_focus_range": baseline.optimal_focus_range,
                "optimal_complexity_range": baseline.optimal_complexity_range,
                "fatigue_threshold": baseline.fatigue_threshold,
                "peak_performance_hour": baseline.peak_performance_hour
            }, f, indent=2)

    def _save_learning(self, learning: LearningProfile):
        """Save learning profile to file."""
        path = self.storage_path / f"user_{self.user_id}_learning.json"
        with open(path, "w") as f:
            json.dump({
                "total_tasks_completed": learning.total_tasks_completed,
                "total_cycles": learning.total_cycles,
                "avg_improvement_rate": learning.avg_improvement_rate,
                "preferred_strategies": learning.preferred_strategies,
                "difficult_complexity_levels": learning.difficult_complexity_levels,
                "strong_complexity_levels": learning.strong_complexity_levels,
                "learning_curve_steepness": learning.learning_curve_steepness,
                "pattern_recognition_strength": learning.pattern_recognition_strength
            }, f, indent=2)

    def update_baseline_from_history(self, cognitive_history: list):
        """
        Update baseline cognitive characteristics from execution history.

        Args:
            cognitive_history: List of {"focus", "fatigue", "learning_efficiency"} dicts
        """
        if not cognitive_history:
            return

        # Calculate averages
        avg_focus = sum(h.get("focus", 0.5) for h in cognitive_history) / len(cognitive_history)
        avg_fatigue = sum(h.get("fatigue", 0.3) for h in cognitive_history) / len(cognitive_history)
        avg_learning = sum(h.get("learning_efficiency", 0.5) for h in cognitive_history) / len(cognitive_history)

        # Update baseline with exponential moving average (give weight to new data)
        alpha = 0.3
        self.baseline.avg_focus = (alpha * avg_focus) + ((1 - alpha) * self.baseline.avg_focus)
        self.baseline.avg_fatigue = (alpha * avg_fatigue) + ((1 - alpha) * self.baseline.avg_fatigue)
        self.baseline.avg_learning_efficiency = (alpha * avg_learning) + ((1 - alpha) * self.baseline.avg_learning_efficiency)

        self._save_baseline(self.baseline)

    def register_strategy_success(self, strategy_name: str, success_rate: float):
        """Record that this strategy worked well for this user."""
        if strategy_name not in self.learning.preferred_strategies:
            self.learning.preferred_strategies[strategy_name] = success_rate
        else:
            # Exponential moving average
            alpha = 0.4
            current = self.learning.preferred_strategies[strategy_name]
            self.learning.preferred_strategies[strategy_name] = (alpha * success_rate) + ((1 - alpha) * current)

        self._save_learning(self.learning)

    def register_complexity_difficulty(self, complexity: float, succeeded: bool):
        """Record whether this complexity level was easy/hard for user."""
        if succeeded:
            if complexity not in self.learning.strong_complexity_levels:
                self.learning.strong_complexity_levels.append(complexity)
            # Remove from difficult if present
            if complexity in self.learning.difficult_complexity_levels:
                self.learning.difficult_complexity_levels.remove(complexity)
        else:
            if complexity not in self.learning.difficult_complexity_levels:
                self.learning.difficult_complexity_levels.append(complexity)
            # Remove from strong if present
            if complexity in self.learning.strong_complexity_levels:
                self.learning.strong_complexity_levels.remove(complexity)

        self._save_learning(self.learning)

    def register_task_completion(self, complexity: float, cycles: int, improvement_rate: float):
        """Record task completion metrics."""
        self.learning.total_tasks_completed += 1
        self.learning.total_cycles += cycles

        # Update average improvement rate
        alpha = 0.3
        self.learning.avg_improvement_rate = (alpha * improvement_rate) + ((1 - alpha) * self.learning.avg_improvement_rate)

        self._save_learning(self.learning)

    def get_personalized_difficulty_adjustment(self, base_difficulty: float, current_state: Dict[str, Any]) -> float:
        """
        Return adjusted difficulty for THIS user based on their profile.

        Args:
            base_difficulty: Starting difficulty modifier (1.0 = no change)
            current_state: Current cognitive state

        Returns:
            Adjusted difficulty modifier personalized to user
        """
        adjustment = base_difficulty

        # If user's focus is below their baseline, reduce difficulty
        user_typical_focus = self.baseline.avg_focus
        current_focus = current_state.get("focus", 0.5)
        if current_focus < (user_typical_focus - 0.2):
            adjustment *= 0.85  # Reduce by 15%

        # If user's fatigue is above their threshold, reduce difficulty
        if current_state.get("fatigue", 0.3) > self.baseline.fatigue_threshold:
            adjustment *= 0.80  # Reduce by 20%

        # If user is in their optimal range, maybe increase
        if current_focus > self.baseline.optimal_focus_range[0] and \
           current_state.get("fatigue", 0.3) < self.baseline.fatigue_threshold * 0.8:
            adjustment *= 1.05  # Increase by 5%

        return max(0.5, min(1.5, adjustment))  # Clamp between 0.5-1.5

    def suggest_best_strategy(self) -> Optional[str]:
        """Suggest the strategy that has worked best for this user."""
        if not self.learning.preferred_strategies:
            return None

        return max(self.learning.preferred_strategies.items(), key=lambda x: x[1])[0]

    def get_profile_summary(self) -> Dict[str, Any]:
        """Get human-readable summary of user profile."""
        return {
            "user_id": self.user_id,
            "baseline": {
                "avg_focus": f"{self.baseline.avg_focus:.2f}",
                "avg_fatigue": f"{self.baseline.avg_fatigue:.2f}",
                "avg_learning_efficiency": f"{self.baseline.avg_learning_efficiency:.2f}",
                "optimal_focus_range": tuple(f"{x:.2f}" for x in self.baseline.optimal_focus_range),
                "optimal_complexity_range": tuple(f"{x:.2f}" for x in self.baseline.optimal_complexity_range),
                "fatigue_threshold": f"{self.baseline.fatigue_threshold:.2f}"
            },
            "learning": {
                "total_tasks_completed": self.learning.total_tasks_completed,
                "total_cycles": self.learning.total_cycles,
                "avg_improvement_rate": f"{self.learning.avg_improvement_rate:.3f}",
                "preferred_strategies": {k: f"{v:.2f}" for k, v in self.learning.preferred_strategies.items()},
                "strong_complexity_levels": [f"{c:.2f}" for c in sorted(self.learning.strong_complexity_levels)],
                "difficult_complexity_levels": [f"{c:.2f}" for c in sorted(self.learning.difficult_complexity_levels)],
                "learning_curve_steepness": f"{self.learning.learning_curve_steepness:.2f}",
                "pattern_recognition_strength": f"{self.learning.pattern_recognition_strength:.2f}"
            }
        }
