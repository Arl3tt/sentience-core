"""
PII v1.0 Phase 2 — Memory Layer
Central memory manager coordinating episodic, semantic, and procedural stores.
"""
from typing import Optional, Dict, Any, List
from core.memory.episodic_store import EpisodicStore
from core.memory.semantic_store import SemanticStore
from core.memory.procedural_store import ProceduralStore
from core.types import SystemState


class MemoryManager:
    """
    Central memory system: coordinates all three memory types.

    Enables:
    - "Recall: What happened before in similar situations?"
    - "Generalize: What patterns have we learned?"
    - "Execute: What procedures are applicable now?"

    Integration with adaptive loop:
    - BEFORE cycle: Load applicable memories
    - AFTER cycle: Save what we learned
    """

    def __init__(self, base_path: str = "core/memory"):
        """Initialize all memory stores."""
        self.episodic = EpisodicStore(f"{base_path}/episodic.db")
        self.semantic = SemanticStore(f"{base_path}/semantic.json")
        self.procedural = ProceduralStore(f"{base_path}/procedural.json")

    def recall_similar_tasks(self, complexity: float) -> Optional[Dict[str, Any]]:
        """
        Recall: What happened before with similar complexity?

        Returns what worked before so we can use similar strategy.
        """
        return self.episodic.get_similar_scenario(complexity)

    def recall_applicable_insights(self, complexity: float) -> List[Dict[str, Any]]:
        """Get insights that apply to current complexity level."""
        insights = self.semantic.get_applicable_insights(complexity)
        return [
            {
                "description": i.description,
                "confidence": i.evidence_score,
                "applies_to_complexity": i.applicable_complexity
            }
            for i in insights
        ]

    def get_applicable_procedures(self, local_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        What procedures should we consider executing?

        Given current state, find procedures that match conditions.
        """
        procedures = self.procedural.find_applicable_procedures(local_state)
        return [
            {
                "name": p.name,
                "steps": p.steps,
                "success_rate": p.success_rate,
                "times_used": p.times_used
            }
            for p in procedures
        ]

    def record_cycle_outcome(self, state: SystemState, report: Dict[str, Any]):
        """
        After a cycle completes: save what happened + what we learned.

        This is called from adaptive loop after each cycle.
        """
        # 1. Record the episode (facts)
        self.episodic.record_episode(state, report)

        # 2. Extract and store insights (patterns)
        self._extract_insights(state, report)

        # 3. Update procedure success rates
        self._update_procedures(report)

    def _extract_insights(self, state: SystemState, report: Dict[str, Any]):
        """Extract patterns from cycle outcome."""
        success_score = report["feedback"]["success_score"]
        complexity = state["task"]["complexity"]

        # Insight 1: Strategy effectiveness
        if success_score > 0.85:
            self.semantic.record_insight(
                category="strategy",
                description=f"Conservative approach works well for complexity {complexity:.2f}",
                evidence_score=min(success_score, 1.0),
                applicable_complexity=complexity,
                metadata={"modifier": report["strategy_modifier"]}
            )

        # Insight 2: Fatigue patterns
        if report["cognitive_state"]["fatigue"] > 0.7:
            self.semantic.record_insight(
                category="fatigue_pattern",
                description="Fatigue accumulates quickly on complex tasks",
                evidence_score=0.6,
                applicable_complexity=complexity,
                metadata={"cycle": report["cycle"]}
            )

        # Insight 3: Learning trends
        cog = report["cognitive_state"]
        if cog["learning_efficiency"] > 0.7:
            self.semantic.record_insight(
                category="learning",
                description="High learning efficiency when focus > 0.8",
                evidence_score=0.7,
                applicable_complexity=complexity,
                metadata={"focus": cog["focus"], "efficiency": cog["learning_efficiency"]}
            )

    def _update_procedures(self, report: Dict[str, Any]):
        """Update procedure success rates based on outcome."""
        # In future: track which procedures were used and update their success
        pass

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of all memory."""
        return {
            "episodic": self.episodic.get_statistics(),
            "semantic": self.semantic.statistics(),
            "procedural": self.procedural.statistics()
        }

    def get_learning_summary(self, task_id: str) -> Dict[str, Any]:
        """Get complete learning summary for a task."""
        return {
            "learning_curve": self.episodic.get_learning_curve(task_id),
            "insights": self.semantic.get_high_confidence_insights(min_evidence=0.6),
            "applicable_procedures": self.procedural.statistics()
        }

    def suggest_next_action(self, state: SystemState) -> Optional[Dict[str, Any]]:
        """
        Based on memory: What should we do next?

        Combines insights + procedures + patterns.
        """
        complexity = state["task"]["complexity"]
        cog = state["cognitive_state"]

        # Check if we have a procedure that fits current state
        local_state = {
            "focus": cog["focus"],
            "fatigue": cog["fatigue"],
            "cognitive_load": cog["cognitive_load"]
        }

        procedures = self.get_applicable_procedures(local_state)

        if procedures:
            best = max(procedures, key=lambda p: p["success_rate"])
            return {
                "type": "procedure",
                "action": best["name"],
                "steps": best["steps"],
                "confidence": best["success_rate"]
            }

        # Fallback: suggest strategy based on learned insights
        strategy_suggestion = self.semantic.suggest_strategy(complexity)
        if strategy_suggestion:
            return {
                "type": "strategy",
                "action": strategy_suggestion["suggestion"],
                "confidence": strategy_suggestion["confidence"]
            }

        return None
