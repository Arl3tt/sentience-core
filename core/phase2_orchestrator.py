"""
PII v1.0 Phase 2 — Orchestration Layer
Coordinates real agents through PII adaptive loop with memory and tools.

This orchestrator:
- Runs integrated agents (Planner, Researcher, Executor, Critic)
- Manages cognitive state transitions
- Handles memory integration
- Provides unified API for running workflows
"""

from typing import Dict, Any, List, Optional
import uuid
from dataclasses import dataclass
from datetime import datetime

from core.adaptive_loop import AdaptiveLoop
from core.system_state import initialize_system_state
from core.types import CognitiveState, Task
from core.cognition import get_cognitive_summary
from core.memory.manager import MemoryManager
from core.pii_integration import (
    IntegrationConfig,
    MemoryAwareAgent,
    PlannerAgent,
    ResearcherAgent,
    ExecutorAgent,
    CriticAgent,
    ToolExecutor
)


@dataclass
class TaskRequest:
    """Request to execute a task through integrated system."""
    task_id: str
    description: str
    complexity: float = 0.5  # 0.0-1.0
    max_cycles: int = 5
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowResult:
    """Result from workflow execution."""
    task_id: str
    success: bool
    cycles_executed: int
    final_cognitive_state: Dict[str, Any]
    history: List[Dict[str, Any]]
    errors: List[str]
    execution_time: float


class Phase2Orchestrator:
    """
    Orchestrates integrated agents through PII adaptive loop.

    Workflow:
    1. Planner: Break down task
    2. Researcher: Gather context and insights
    3. Executor: Implement solution
    4. Critic: Evaluate and provide feedback
    5. Loop: Improve based on feedback (if not excellent/overloaded)
    """

    def __init__(
        self,
        memory_path: str = "core/memory",
        config: IntegrationConfig = None
    ):
        self.config = config or IntegrationConfig()
        self.memory_manager = MemoryManager(memory_path)
        self.tool_executor = ToolExecutor(self.config)

        # Initialize agents
        self.agents = {
            "planner": PlannerAgent(
                "planner",
                self.memory_manager,
                self.config
            ),
            "researcher": ResearcherAgent(
                "researcher",
                self.memory_manager,
                self.config
            ),
            "executor": ExecutorAgent(
                "executor",
                self.memory_manager,
                self.tool_executor,
                self.config
            ),
            "critic": CriticAgent(
                "critic",
                self.memory_manager,
                self.config
            )
        }

        # Initialize adaptive loop
        self.adaptive_loop = AdaptiveLoop()

    def execute_task(self, request: TaskRequest) -> WorkflowResult:
        """Execute a task through the integrated workflow."""
        start_time = datetime.now()

        # Initialize system state
        state = initialize_system_state(
            task=Task(
                id=request.task_id,
                description=request.description,
                complexity=request.complexity
            ),
            metadata=request.metadata or {}
        )

        # Execute cycles
        history = []
        errors = []
        cycle_count = 0

        try:
            for cycle in range(request.max_cycles):
                cycle_result = self._execute_cycle(
                    state,
                    cycle,
                    history
                )

                state = cycle_result["state"]
                cycle_success = cycle_result["success"]
                cycle_count += 1

                # Check stopping conditions
                cognitive = state.get("cognitive_state", {})
                focus = cognitive.get("focus", 0.5)
                load = cognitive.get("cognitive_load", 0.5)

                # Stop if excellent or overloaded
                if cycle_success > 0.85 or load > 0.9:
                    break

        except Exception as e:
            errors.append(str(e))

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Get final cognitive state
        final_cognitive = get_cognitive_summary(state)

        return WorkflowResult(
            task_id=request.task_id,
            success=not errors,
            cycles_executed=cycle_count,
            final_cognitive_state=final_cognitive,
            history=history,
            errors=errors,
            execution_time=execution_time
        )

    def _execute_cycle(
        self,
        state: Dict[str, Any],
        cycle_num: int,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute one improvement cycle."""
        cycle_start = datetime.now()
        agents_executed = []

        try:
            # Step 1: Planner
            state, plan_output = self.agents["planner"].run(state)
            state = self.agents["planner"].learn(state, {"success_score": 0.8, "efficiency_score": 0.85, "cognitive_load": 0, "errors": []})
            agents_executed.append("planner")

            # Step 2: Researcher
            state, research_output = self.agents["researcher"].run(state)
            state = self.agents["researcher"].learn(state, {"success_score": 0.9, "efficiency_score": 0.9, "cognitive_load": 0, "errors": []})
            agents_executed.append("researcher")

            # Step 3: Executor
            state, exec_output = self.agents["executor"].run(state)
            state = self.agents["executor"].learn(state, {"success_score": 0.8, "efficiency_score": 0.75, "cognitive_load": 0, "errors": []})
            agents_executed.append("executor")

            # Step 4: Critic
            state, critique_output = self.agents["critic"].run(state)
            state = self.agents["critic"].learn(state, {"success_score": 0.9, "efficiency_score": 0.95, "cognitive_load": 0, "errors": []})
            agents_executed.append("critic")

            # Aggregate cycle score
            cycle_score = self._calculate_cycle_score(
                state,
                plan_output,
                research_output,
                exec_output,
                critique_output
            )

            cycle_time = (datetime.now() - cycle_start).total_seconds()

            cycle_record = {
                "cycle": cycle_num + 1,
                "agents": agents_executed,
                "success_score": cycle_score,
                "cognition": state.get("cognitive_state", {}),
                "timestamp": datetime.now().isoformat(),
                "duration": cycle_time
            }

            history.append(cycle_record)

            return {
                "state": state,
                "success": cycle_score
            }

        except Exception as e:
            history.append({
                "cycle": cycle_num + 1,
                "error": str(e),
                "agents_executed": agents_executed,
                "timestamp": datetime.now().isoformat()
            })
            raise

    def _calculate_cycle_score(
        self,
        state: Dict[str, Any],
        plan_output: Dict[str, Any],
        research_output: Dict[str, Any],
        exec_output: Dict[str, Any],
        critique_output: Dict[str, Any]
    ) -> float:
        """Calculate overall cycle success score."""
        # Extract scores from agent outputs
        plan_score = min(1.0, len(plan_output.get("plan", {}).get("tasks", [])) / 5.0)
        research_score = min(1.0, len(research_output.get("research", {}).get("insights", [])) / 5.0)
        exec_success = exec_output.get("execution_result", {}).get("success", 0.2)
        critique_score = critique_output.get("critique", {}).get("overall_score", 0.5)

        # Weighted average
        overall = (
            0.2 * plan_score +
            0.2 * research_score +
            0.3 * exec_success +
            0.3 * critique_score
        )

        return overall

    def get_cognitive_metrics(self) -> Dict[str, Any]:
        """Get current cognitive metrics of the system."""
        return get_cognitive_summary({})

    def reset(self):
        """Reset orchestrator state."""
        self.adaptive_loop = AdaptiveLoop()


class WorkflowScheduler:
    """
    Manages multiple workflows and task queues.

    Enables:
    - Queuing tasks
    - Prioritization
    - Concurrent execution (with limits)
    - Status tracking
    """

    def __init__(self, max_concurrent: int = 3):
        self.orchestrator = Phase2Orchestrator()
        self.max_concurrent = max_concurrent
        self.task_queue: List[TaskRequest] = []
        self.active_tasks: Dict[str, 'WorkflowResult'] = {}
        self.completed_tasks: Dict[str, 'WorkflowResult'] = {}

    def submit_task(self, request: TaskRequest) -> str:
        """Submit a task for execution."""
        self.task_queue.append(request)
        return request.task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a task."""
        if task_id in self.active_tasks:
            return {
                "status": "running",
                "task_id": task_id,
                "start_time": self.active_tasks[task_id].get("start_time")
            }
        elif task_id in self.completed_tasks:
            result = self.completed_tasks[task_id]
            return {
                "status": "completed",
                "task_id": task_id,
                "success": result.success,
                "cycles": result.cycles_executed,
                "execution_time": result.execution_time
            }
        else:
            return {
                "status": "queued",
                "task_id": task_id
            }

    def process_queue(self):
        """Process waiting tasks."""
        while self.task_queue and len(self.active_tasks) < self.max_concurrent:
            request = self.task_queue.pop(0)

            # Execute task
            result = self.orchestrator.execute_task(request)

            # Move to completed
            self.completed_tasks[request.task_id] = result

    def get_results(self, task_id: str) -> Optional[WorkflowResult]:
        """Get completed task results."""
        return self.completed_tasks.get(task_id)
