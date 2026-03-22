"""
PII v1.0 Phase 2 — Memory Layer
Semantic memory: patterns and insights learned.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class Insight:
    """A learned pattern or insight."""
    insight_id: str
    category: str  # "strategy", "error_pattern", "optimal_range", "timing"
    description: str
    evidence_score: float  # 0.0-1.0 (how confident we are)
    applicable_complexity: float  # Best applies when task complexity is ~this
    metadata: Dict[str, Any]
    timestamp: str


class SemanticStore:
    """
    Semantic memory: patterns, insights, generalizations.

    Stores:
    - "Complex tasks work better with conservative strategy"
    - "User gets fatigued after 15 cycles"
    - "When focus < 0.3, drop difficulty by 20%"
    - "Efficiency + success correlation at >0.8"

    Enables:
    - Pattern matching ("I've seen this before")
    - Causal understanding ("When X, then Y")
    - Generalization ("This applies to tasks like...")

    Note: In Phase 2, we store to JSON.
          In Phase 3, we'll add Vector DB (Chroma) for semantic similarity.
    """

    def __init__(self, store_path: str = "core/memory/semantic.json"):
        """Initialize semantic memory store."""
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.insights: Dict[str, Insight] = self._load()

    def _load(self) -> Dict[str, Insight]:
        """Load insights from file."""
        if self.store_path.exists():
            with open(self.store_path, "r") as f:
                data = json.load(f)
                return {
                    k: Insight(**v) for k, v in data.items()
                }
        return {}

    def _save(self):
        """Save insights to file."""
        with open(self.store_path, "w") as f:
            json.dump(
                {k: self._insight_to_dict(v) for k, v in self.insights.items()},
                f,
                indent=2
            )

    def _insight_to_dict(self, insight: Insight) -> Dict[str, Any]:
        """Convert Insight to dict for JSON."""
        return {
            "insight_id": insight.insight_id,
            "category": insight.category,
            "description": insight.description,
            "evidence_score": insight.evidence_score,
            "applicable_complexity": insight.applicable_complexity,
            "metadata": insight.metadata,
            "timestamp": insight.timestamp
        }

    def record_insight(
        self,
        category: str,
        description: str,
        evidence_score: float,
        applicable_complexity: float,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Record a new insight.

        Args:
            category: Type of insight ("strategy", "error_pattern", etc.)
            description: Human-readable insight
            evidence_score: Confidence (0.0-1.0)
            applicable_complexity: Task complexity where this applies
            metadata: Additional data

        Returns:
            insight_id
        """
        from datetime import datetime

        insight_id = f"{category}_{len(self.insights)}"
        insight = Insight(
            insight_id=insight_id,
            category=category,
            description=description,
            evidence_score=evidence_score,
            applicable_complexity=applicable_complexity,
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )

        self.insights[insight_id] = insight
        self._save()

        return insight_id

    def get_insights_by_category(self, category: str) -> List[Insight]:
        """Get all insights of a specific category."""
        return [i for i in self.insights.values() if i.category == category]

    def get_applicable_insights(self, complexity: float, tolerance: float = 0.15) -> List[Insight]:
        """Get insights applicable to a given complexity level."""
        return [
            i for i in self.insights.values()
            if abs(i.applicable_complexity - complexity) < tolerance
        ]

    def get_high_confidence_insights(self, min_evidence: float = 0.7) -> List[Insight]:
        """Get insights we're confident about."""
        return [
            i for i in self.insights.values()
            if i.evidence_score >= min_evidence
        ]

    def suggest_strategy(self, complexity: float) -> Optional[Dict[str, Any]]:
        """
        Suggest a strategy based on past learning.
        E.g., "For complexity 0.7, use conservative approach"
        """
        insights = self.get_applicable_insights(complexity)
        strategy_insights = [i for i in insights if i.category == "strategy"]

        if strategy_insights:
            # Return highest confidence
            best = max(strategy_insights, key=lambda i: i.evidence_score)
            return {
                "suggestion": best.description,
                "confidence": best.evidence_score,
                "metadata": best.metadata
            }
        return None

    def suggest_adjustment(self, current_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Suggest adjustments based on current state.
        E.g., "Your focus is low, should reduce difficulty"
        """
        focus = current_state.get("focus", 0.5)
        fatigue = current_state.get("fatigue", 0.5)

        # Look for relevant patterns
        patterns = [i for i in self.insights.values() if i.category == "pattern"]

        suggestions = []

        if focus < 0.3 and fatigue > 0.7:
            suggestions.append("System is both unfocused and fatigued. Take a break.")

        if fatigue > 0.8:
            suggestions.append("High fatigue detected. Consider reducing difficulty or pausing.")

        if focus > 0.9:
            suggestions.append("High focus and engagement detected. Could increase difficulty.")

        if suggestions:
            return {
                "suggestions": suggestions,
                "based_on_state": {
                    "focus": focus,
                    "fatigue": fatigue
                }
            }

        return None

    def statistics(self) -> Dict[str, Any]:
        """Get memory statistics."""
        categories = {}
        for insight in self.insights.values():
            if insight.category not in categories:
                categories[insight.category] = 0
            categories[insight.category] += 1

        avg_evidence = (
            sum(i.evidence_score for i in self.insights.values()) / len(self.insights)
            if self.insights else 0.0
        )

        return {
            "total_insights": len(self.insights),
            "categories": categories,
            "avg_evidence_score": avg_evidence,
            "high_confidence": sum(1 for i in self.insights.values() if i.evidence_score > 0.8)
        }
