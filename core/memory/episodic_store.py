"""
PII v1.0 Phase 2 — Memory Layer
Persistent episodic memory: facts about what happened.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from core.types import SystemState, Feedback


@dataclass
class EpisodeRecord:
    """A single task execution episode."""
    episode_id: str
    task_id: str
    task_description: str
    complexity: float
    cycle: int
    agent_name: str
    success_score: float
    efficiency_score: float
    cognitive_load: float
    focus: float
    fatigue: float
    learning_efficiency: float
    strategy_modifier: float
    timestamp: str  # ISO format


class EpisodicStore:
    """
    Episodic memory: factual records of what happened.

    Stores:
    - Each cycle's results
    - Cognitive states
    - Success/failure data
    - Strategy effectiveness

    Enables:
    - "What happened before in similar situations?"
    - Learning curves (historical performance)
    - Pattern detection (error trends)
    """

    def __init__(self, db_path: str = "core/memory/episodic.db"):
        """Initialize episodic memory store."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Create database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY,
                    task_id TEXT,
                    task_description TEXT,
                    complexity REAL,
                    cycle INTEGER,
                    agent_name TEXT,
                    success_score REAL,
                    efficiency_score REAL,
                    cognitive_load REAL,
                    focus REAL,
                    fatigue REAL,
                    learning_efficiency REAL,
                    strategy_modifier REAL,
                    timestamp TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_id ON episodes(task_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent ON episodes(agent_name)
            """)
            conn.commit()

    def record_episode(self, state: SystemState, report: Dict[str, Any]) -> str:
        """
        Record a single cycle/episode to memory.

        Args:
            state: Current system state
            report: Cycle report from adaptive loop

        Returns:
            episode_id
        """
        episode_id = f"{state['task']['id']}_cycle_{report['cycle']}"
        timestamp = datetime.now().isoformat()

        record = EpisodeRecord(
            episode_id=episode_id,
            task_id=state["task"]["id"],
            task_description=state["task"]["description"],
            complexity=state["task"]["complexity"],
            cycle=report["cycle"],
            agent_name=report["agent"],
            success_score=report["feedback"]["success_score"],
            efficiency_score=report["feedback"]["efficiency_score"],
            cognitive_load=report["feedback"]["cognitive_load"],
            focus=report["cognitive_state"]["focus"],
            fatigue=report["cognitive_state"]["fatigue"],
            learning_efficiency=report["cognitive_state"]["learning_efficiency"],
            strategy_modifier=report["strategy_modifier"],
            timestamp=timestamp
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO episodes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(asdict(record).values()))
            conn.commit()

        return episode_id

    def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all episodes for a task."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM episodes WHERE task_id = ? ORDER BY cycle ASC",
                (task_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_agent_history(self, agent_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent episodes for an agent."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM episodes WHERE agent_name = ? ORDER BY timestamp DESC LIMIT ?",
                (agent_name, limit)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_similar_scenario(self, complexity: float, tolerance: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Find a past episode with similar task complexity.
        Useful for: "What worked last time for a task like this?"
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM episodes
                WHERE complexity BETWEEN ? AND ?
                AND success_score > 0.7
                ORDER BY timestamp DESC
                LIMIT 1
            """, (complexity - tolerance, complexity + tolerance)).fetchone()
            return dict(row) if row else None

    def get_learning_curve(self, task_id: str) -> Dict[str, Any]:
        """
        Compute learning curve for a task.
        Shows: Are we improving? By how much? Trend direction?
        """
        episodes = self.get_task_history(task_id)
        if not episodes:
            return {}

        success_scores = [e["success_score"] for e in episodes]
        efficiency_scores = [e["efficiency_score"] for e in episodes]

        first_half = success_scores[:len(success_scores)//2]
        second_half = success_scores[len(success_scores)//2:]

        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0

        return {
            "total_cycles": len(episodes),
            "initial_success": success_scores[0],
            "final_success": success_scores[-1],
            "first_half_avg": avg_first,
            "second_half_avg": avg_second,
            "improvement": avg_second - avg_first,
            "trend": "improving" if avg_second > avg_first else "declining"
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics from all episodes."""
        with sqlite3.connect(self.db_path) as conn:
            stats = conn.execute("""
                SELECT
                    COUNT(*) as total_episodes,
                    COUNT(DISTINCT task_id) as unique_tasks,
                    COUNT(DISTINCT agent_name) as unique_agents,
                    AVG(success_score) as avg_success,
                    AVG(efficiency_score) as avg_efficiency,
                    AVG(cognitive_load) as avg_load,
                    MIN(focus) as min_focus,
                    MAX(focus) as max_focus
                FROM episodes
            """).fetchone()

            return {
                "total_episodes": stats[0],
                "unique_tasks": stats[1],
                "unique_agents": stats[2],
                "avg_success": stats[3],
                "avg_efficiency": stats[4],
                "avg_cognitive_load": stats[5],
                "focus_range": (stats[6], stats[7])
            }
