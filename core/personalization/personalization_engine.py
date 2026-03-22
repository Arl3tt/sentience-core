"""
PII v1.0 Phase 3 — User Cognitive Model
Personalization Engine: Personalized recommendations based on user profile.
"""
from typing import Dict, Any, Optional, List
from core.personalization.user_profile import UserProfile
from core.personalization.user_analytics import UserLearningAnalytics
from core.memory.manager import MemoryManager
from core.types import SystemState


class PersonalizationEngine:
    """
    Personalized AI assistant tailored to YOUR unique patterns.

    Coordinates:
    - User Profile: Your baseline cognition + learning preferences
    - User Analytics: Extracted patterns from your task history
    - Memory System: What worked for you before

    Provides:
    - Personalized difficulty adjustment
    - Strategy recommendations for YOUR style
    - Optimal task timing/pacing for YOU
    - Fatigue prediction specific to your patterns
    - Individual learning insights
    """

    def __init__(self, user_id: str = "default", memory_manager: Optional[MemoryManager] = None, storage_path: str = "core/personalization"):
        """Initialize personalization for a user."""
        self.user_id = user_id
        self.profile = UserProfile(user_id, storage_path)
        self.memory = memory_manager
        self.analytics = UserLearningAnalytics(memory_manager.episodic) if memory_manager else None

    def recommend_difficulty(self, state: SystemState, base_difficulty: float = 1.0) -> Dict[str, Any]:
        """
        Recommend personalized difficulty adjustment.

        Considers:
        - User's cognitive baseline
        - Current cognitive state
        - User's history with this complexity level
        """
        current_state = state["cognitive_state"]
        task_complexity = state["task"]["complexity"]

        # Get personalized adjustment from profile
        adjusted_difficulty = self.profile.get_personalized_difficulty_adjustment(base_difficulty, current_state)

        # Additional adjustment based on user's history with this complexity
        if task_complexity in self.profile.learning.strong_complexity_levels:
            adjusted_difficulty *= 1.10  # User is strong at this level, increase slightly
        elif task_complexity in self.profile.learning.difficult_complexity_levels:
            adjusted_difficulty *= 0.90  # User struggles here, decrease slightly

        return {
            "adjusted_difficulty": max(0.5, min(1.5, adjusted_difficulty)),
            "rationale": self._get_difficulty_rationale(current_state, task_complexity),
            "base_difficulty": base_difficulty,
            "profile_adjustment": adjusted_difficulty / base_difficulty
        }

    def _get_difficulty_rationale(self, current_state: Dict[str, Any], complexity: float) -> str:
        """Explain why difficulty was adjusted."""
        reasons = []

        if current_state["focus"] < self.profile.baseline.avg_focus - 0.2:
            reasons.append("focus_below_baseline")

        if current_state["fatigue"] > self.profile.baseline.fatigue_threshold:
            reasons.append("fatigue_elevated")

        if complexity in self.profile.learning.difficult_complexity_levels:
            reasons.append("complexity_historically_difficult")

        if not reasons:
            reasons.append("performing_within_baseline")

        return "; ".join(reasons)

    def recommend_strategy(self, state: SystemState) -> Dict[str, Any]:
        """
        Recommend strategy based on user's proven effectiveness.

        Returns strategy that has worked best for THIS user.
        """
        complexity = state["task"]["complexity"]

        # Option 1: Use strategy that worked best for user overall
        best_overall = self.profile.suggest_best_strategy()

        # Option 2: Use memory recall for similar complexity
        if self.memory:
            similar = self.memory.recall_similar_tasks(complexity)
            if similar and similar.get("best_strategy"):
                return {
                    "recommended_strategy": similar["best_strategy"],
                    "source": "similar_task_history",
                    "confidence": 0.8,
                    "success_rate": similar.get("avg_success_rate", 0.5)
                }

        # Fallback to general insights
        if self.memory:
            insights = self.memory.recall_applicable_insights(complexity)
            if insights:
                return {
                    "recommended_strategy": insights[0]["description"],
                    "source": "learned_insights",
                    "confidence": insights[0]["confidence"],
                    "complexity_match": insights[0]["applies_to_complexity"]
                }

        # Last resort: use best strategy for this user
        if best_overall:
            success_rate = self.profile.learning.preferred_strategies.get(best_overall, 0.5)
            return {
                "recommended_strategy": best_overall,
                "source": "user_preference",
                "confidence": success_rate,
                "total_uses": len([s for s in self.profile.learning.preferred_strategies if s == best_overall])
            }

        return {
            "recommended_strategy": "conservative",
            "source": "default",
            "confidence": 0.5
        }

    def predict_fatigue_risk(self, state: SystemState, num_cycles: int = 5) -> Dict[str, Any]:
        """
        Predict if user will hit fatigue overload in next N cycles.

        Returns:
        - risk_level: "low", "medium", "high"
        - estimated_peak_fatigue: Predicted fatigue after N cycles
        - recommendation: What to do to prevent fatigue
        """
        current_fatigue = state["cognitive_state"]["fatigue"]

        # Get user's fatigue pattern from analytics
        if not self.analytics:
            return {"risk_level": "unknown", "reason": "no_analytics"}

        # Simulate fatigue accumulation
        # Estimate rate from baseline: if avg_fatigue is 0.30 and user has done 10+ cycles
        if self.profile.learning.total_cycles > 0:
            accumulation_rate = self.profile.baseline.avg_fatigue / max(1, self.profile.learning.total_cycles)
        else:
            accumulation_rate = 0.05  # Default estimate
        predicted_fatigue = current_fatigue + (accumulation_rate * num_cycles)
        predicted_fatigue = min(predicted_fatigue, 1.0)

        # Determine risk
        if predicted_fatigue > self.profile.baseline.fatigue_threshold:
            risk_level = "high"
            recommendation = "Take a break or reduce difficulty soon"
        elif predicted_fatigue > self.profile.baseline.fatigue_threshold * 0.8:
            risk_level = "medium"
            recommendation = "Monitor fatigue closely, prepare recovery procedure"
        else:
            risk_level = "low"
            recommendation = "Normal operation, fatigue under control"

        return {
            "risk_level": risk_level,
            "current_fatigue": current_fatigue,
            "predicted_fatigue_in_n_cycles": predicted_fatigue,
            "n_cycles": num_cycles,
            "user_fatigue_threshold": self.profile.baseline.fatigue_threshold,
            "accumulation_rate": accumulation_rate,
            "recommendation": recommendation
        }

    def get_personalization_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive personalization summary for user.

        Shows:
        - User's proven strengths/weaknesses
        - Historical performance
        - Recommended next steps
        """
        profile_summary = self.profile.get_profile_summary()

        analytics_summary = {}
        if self.analytics and self.memory:
            # Get all task IDs from memory
            stats = self.memory.get_memory_summary()
            if stats.get("episodic", {}).get("total_episodes", 0) > 0:
                analytics_summary = {
                    "memory_summary": stats
                }

        return {
            "user_profile": profile_summary,
            "analytics": analytics_summary,
            "personalization_status": "active" if self.profile.learning.total_tasks_completed > 0 else "initializing"
        }

    def register_task_outcome(self, state: SystemState, report: Dict[str, Any]):
        """
        Register task outcome to update user profile.

        Called after each task to personalize future recommendations.
        """
        complexity = state["task"]["complexity"]
        cycles = report.get("cycle", 1)
        success_score = report["feedback"]["success_score"]
        strategy = state["strategy"]["approach"]

        # Register strategy success
        self.profile.register_strategy_success(strategy, success_score)

        # Register complexity difficulty
        self.profile.register_complexity_difficulty(complexity, success_score > 0.7)

        # Register task completion
        trajectory = self.analytics.compute_improvement_trajectory(state["task"]["id"]) if self.analytics else {}
        improvement_rate = trajectory.get("improvement_rate", 0.05)
        self.profile.register_task_completion(complexity, cycles, improvement_rate)

    def should_reduce_difficulty(self, state: SystemState) -> bool:
        """Check if user should reduce difficulty based on their profile."""
        # Reduce if user's focus is below their typical 2 stddevs
        if state["cognitive_state"]["focus"] < (self.profile.baseline.avg_focus - 0.3):
            return True

        # Reduce if fatigue is above user's threshold
        if state["cognitive_state"]["fatigue"] > self.profile.baseline.fatigue_threshold:
            return True

        return False

    def should_increase_difficulty(self, state: SystemState) -> bool:
        """Check if user should increase difficulty based on their profile."""
        # Increase only if user is consistently in optimal range
        if state["cognitive_state"]["focus"] > self.profile.baseline.optimal_focus_range[1] and \
           state["cognitive_state"]["fatigue"] < self.profile.baseline.fatigue_threshold * 0.7 and \
           state["cognitive_state"]["cognitive_load"] < 0.6:
            return True

        return False
