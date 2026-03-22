"""
PII v1.0 Phase 2 — Memory Layer
Procedural memory: successful strategies and how-to knowledge.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json
from pathlib import Path
from datetime import datetime


@dataclass
class Procedure:
    """A learned procedure/strategy."""
    procedure_id: str
    name: str  # "conservative_strategy", "recovery_from_fatigue"
    description: str
    steps: List[str]  # ["When focus < 0.3", "Reduce difficulty by 15%", "Wait 2 cycles"]
    success_rate: float  # 0.0-1.0
    times_used: int
    condition: Dict[str, Any]  # What conditions trigger this procedure
    metadata: Dict[str, Any]


class ProceduralStore:
    """
    Procedural memory: "How to do things" that work.

    Stores:
    - "When fatigued: reduce difficulty and take a break"
    - "When success_score drops: switch to conservative strategy"
    - "When focus > 0.8: increase difficulty for learning"
    - Custom multi-step procedures

    Enables:
    - "Use the procedure that worked before"
    - Decision trees ("If X, then do Y")
    - Automated responses
    - Strategy playbooks
    """

    def __init__(self, store_path: str = "core/memory/procedural.json"):
        """Initialize procedural memory store."""
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.procedures: Dict[str, Procedure] = self._load()

        # Initialize default procedures
        self._init_defaults()

    def _load(self) -> Dict[str, Procedure]:
        """Load procedures from file."""
        if self.store_path.exists():
            with open(self.store_path, "r") as f:
                data = json.load(f)
                return {k: Procedure(**v) for k, v in data.items()}
        return {}

    def _save(self):
        """Save procedures to file."""
        data = {}
        for k, p in self.procedures.items():
            data[k] = {
                "procedure_id": p.procedure_id,
                "name": p.name,
                "description": p.description,
                "steps": p.steps,
                "success_rate": p.success_rate,
                "times_used": p.times_used,
                "condition": p.condition,
                "metadata": p.metadata
            }
        with open(self.store_path, "w") as f:
            json.dump(data, f, indent=2)

    def _init_defaults(self):
        """Initialize default procedures."""
        if not self.procedures:
            # Procedure 1: Handle low focus
            self.add_procedure(
                name="low_focus_recovery",
                description="When focus drops below 0.3",
                steps=[
                    "Recognize focus is degraded",
                    "Reduce task difficulty by 20%",
                    "Simplify current task",
                    "Monitor focus recovery"
                ],
                condition={"focus": {"less_than": 0.3}},
                metadata={"severity": "medium"}
            )

            # Procedure 2: Handle high fatigue
            self.add_procedure(
                name="fatigue_recovery",
                description="When fatigue exceeds safe level (>0.75)",
                steps=[
                    "Pause current task",
                    "Wait 1-2 cycles",
                    "Reset difficulty to baseline",
                    "Reassess system state"
                ],
                condition={"fatigue": {"greater_than": 0.75}},
                metadata={"severity": "high"}
            )

            # Procedure 3: Capitalize on high performance
            self.add_procedure(
                name="success_acceleration",
                description="When success rate exceeds 0.85",
                steps=[
                    "Recognize excellent performance",
                    "Increase difficulty by 15%",
                    "Push learning boundaries",
                    "Track cognitive load"
                ],
                condition={"success_score": {"greater_than": 0.85}},
                metadata={"severity": "low", "risk": "learning opportunity"}
            )

    def add_procedure(
        self,
        name: str,
        description: str,
        steps: List[str],
        condition: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add a new procedure."""
        procedure_id = f"proc_{len(self.procedures)}"
        procedure = Procedure(
            procedure_id=procedure_id,
            name=name,
            description=description,
            steps=steps,
            success_rate=0.5,  # Start neutral
            times_used=0,
            condition=condition,
            metadata=metadata or {}
        )
        self.procedures[procedure_id] = procedure
        self._save()
        return procedure_id

    def find_applicable_procedures(self, state: Dict[str, Any]) -> List[Procedure]:
        """Find procedures that match current state."""
        applicable = []

        for procedure in self.procedures.values():
            if self._condition_matches(state, procedure.condition):
                applicable.append(procedure)

        # Sort by success rate (best first)
        return sorted(applicable, key=lambda p: p.success_rate, reverse=True)

    def _condition_matches(self, state: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Check if state matches condition."""
        for key, criteria in condition.items():
            if key not in state:
                return False

            value = state[key]

            if isinstance(criteria, dict):
                for op, threshold in criteria.items():
                    if op == "less_than" and value >= threshold:
                        return False
                    elif op == "greater_than" and value <= threshold:
                        return False
                    elif op == "equals" and value != threshold:
                        return False

        return True

    def execute_procedure(self, procedure_id: str) -> Dict[str, Any]:
        """Execute a procedure and record usage."""
        procedure = self.procedures.get(procedure_id)
        if not procedure:
            return {"error": f"Procedure {procedure_id} not found"}

        procedure.times_used += 1
        self._save()

        return {
            "procedure": procedure.name,
            "steps": procedure.steps,
            "description": procedure.description
        }

    def update_success_rate(self, procedure_id: str, success: bool):
        """Update procedure success rate based on outcome."""
        procedure = self.procedures.get(procedure_id)
        if not procedure:
            return

        # Exponential moving average
        alpha = 0.3
        outcome_value = 1.0 if success else 0.0
        procedure.success_rate = (alpha * outcome_value) + ((1 - alpha) * procedure.success_rate)

        self._save()

    def get_best_procedure(self) -> Optional[Procedure]:
        """Get highest-performing procedure."""
        if not self.procedures:
            return None
        return max(self.procedures.values(), key=lambda p: p.success_rate)

    def statistics(self) -> Dict[str, Any]:
        """Get procedure statistics."""
        if not self.procedures:
            return {"total_procedures": 0}

        total_uses = sum(p.times_used for p in self.procedures.values())
        avg_success = sum(p.success_rate for p in self.procedures.values()) / len(self.procedures)

        return {
            "total_procedures": len(self.procedures),
            "total_executions": total_uses,
            "avg_success_rate": avg_success,
            "most_used": max(self.procedures.values(), key=lambda p: p.times_used).name if self.procedures else None,
            "best_performing": max(self.procedures.values(), key=lambda p: p.success_rate).name if self.procedures else None
        }
