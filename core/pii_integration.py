"""
PII v1.0 Phase 2 — Integration Layer
Bridges PII cognitive system with existing Sentience Core agents and memory.

This adapter enables:
- PII agents to access existing memory (episodic, semantic, procedural)
- Real tool execution via existing sandbox runner
- Integration with brain orchestrator
- Full cognitive cycle with self-improvement
"""

from typing import Dict, Any, List, Tuple
import json
from dataclasses import dataclass

from core.base_agent import BaseAgent
from core.types import CognitiveState, Feedback, Task, SystemState
from core.memory.manager import MemoryManager
from core.tools.tool_runner import run_python_snippet, run_shell
from core.cognition import get_cognitive_summary


@dataclass
class IntegrationConfig:
    """Configuration for PII-Sentience integration."""
    use_memory: bool = True
    use_tools: bool = True
    safe_mode: bool = True  # Require confirmation for tool execution
    max_retries: int = 3
    fallback_on_error: bool = True


class MemoryAwareAgent(BaseAgent):
    """
    Base class for agents that integrate with the memory system.

    Extends BaseAgent to provide memory access for:
    - Recalling similar past scenarios
    - Learning from previous strategies
    - Updating procedural knowledge
    """

    def __init__(
        self,
        agent_id: str,
        memory_manager: MemoryManager,
        config: IntegrationConfig = None
    ):
        super().__init__(agent_id)
        self.memory_manager = memory_manager
        self.config = config or IntegrationConfig()

    def recall_context(self, state: SystemState) -> Dict[str, Any]:
        """Recall relevant memories for current task."""
        if not self.config.use_memory:
            return {}

        task_complexity = state.get("task", {}).get("complexity", 0.5)

        # Get similar past scenarios
        similar_task = self.memory_manager.recall_similar_tasks(task_complexity)

        # Get applicable insights
        insights = self.memory_manager.recall_applicable_insights(task_complexity)

        # Get applicable procedures
        local_state = state.get("user_state", {})
        procedures = self.memory_manager.get_applicable_procedures(local_state)

        return {
            "similar_task": similar_task,
            "insights": insights,
            "procedures": procedures
        }

    def save_learning(self, state: SystemState, feedback: Feedback) -> None:
        """Save what we learned from this interaction."""
        if not self.config.use_memory:
            return

        # Save episodic memory (what happened)
        task_id = state.get("task", {}).get("id", "unknown")
        complexity = state.get("task", {}).get("complexity", 0.5)

        episode = {
            "task_id": task_id,
            "complexity": complexity,
            "success": feedback.success,
            "efficiency": feedback.efficiency,
            "cognitive_load": feedback.cognitive_load,
            "strategy": state.get("strategy", {})
        }
        self.memory_manager.episodic.save_scenario(episode)

        # Save semantic insights (what we learned)
        if feedback.success > 0.7:  # Only save successful patterns
            insight = {
                "description": f"Strategy {state.get('strategy', {}).get('approach')} "
                              f"works well for complexity {complexity}",
                "evidence_score": feedback.success,
                "applicable_complexity": complexity
            }
            self.memory_manager.semantic.store_insight(insight)


class ToolExecutor:
    """
    Integrates with existing tool runner and sandbox system.
    Provides safe execution context for agents.
    """

    def __init__(self, config: IntegrationConfig = None):
        self.config = config or IntegrationConfig()

    def execute_code(self, code: str, timeout_s: int = 20) -> Dict[str, Any]:
        """Execute Python code safely."""
        if not self.config.use_tools:
            return {"error": "Tools disabled"}

        try:
            result = run_python_snippet(
                code,
                timeout_s=timeout_s,
                require_confirm=self.config.safe_mode
            )
            return {
                "success": result.get("returncode", 0) == 0,
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "output": result
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def execute_shell(self, cmd: str) -> Dict[str, Any]:
        """Execute shell command safely."""
        if not self.config.use_tools:
            return {"error": "Tools disabled"}

        try:
            result = run_shell(cmd, require_confirm=self.config.safe_mode)
            return {
                "success": result.get("returncode", 0) == 0,
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "output": result
            }
        except Exception as e:
            return {"error": str(e), "success": False}


class PlannerAgent(MemoryAwareAgent):
    """
    Real planner agent combining PII cognitive engine with actual planning.

    Responsibilities:
    - Break down tasks into sub-tasks
    - Consider cognitive state and load
    - Learn from memory about what works
    - Adapt strategy based on feedback
    """

    def run(self, state: SystemState) -> Tuple[SystemState, Dict[str, Any]]:
        """Execute planning cycle."""
        # Recall context from memory
        context = self.recall_context(state)

        # Get cognitive metrics
        cognitive = state.get("cognitive_state", {})

        # Generate plan (simplified - in real use, call LLM)
        plan = self._generate_plan(
            state.get("task", {}),
            context,
            cognitive
        )

        # Update history
        history = state.get("history", [])
        history.append({
            "agent": self.agent_id,
            "action": "plan_generated",
            "tasks_count": len(plan.get("tasks", []))
        })
        state["history"] = history

        return state, {"plan": plan}

    def evaluate(self, state: SystemState, output: Dict[str, Any]) -> Feedback:
        """Evaluate plan quality."""
        plan = output.get("plan", {})
        tasks = plan.get("tasks", [])

        # Plan quality metrics
        success = min(1.0, len(tasks) / 5.0)  # Good if 5+ tasks
        efficiency = plan.get("effort_estimate", 0.5) / 10.0  # Normalized

        return {
            "success_score": success,
            "efficiency_score": efficiency,
            "cognitive_load": state.get("cognitive_state", {}).get("cognitive_load", 0.5),
            "errors": plan.get("errors", [])
        }

    def learn(self, state: SystemState, feedback: Feedback) -> SystemState:
        """Learn from planning experience."""
        # Save memories
        self.save_learning(state, feedback)

        # Update strategy preferences
        strategy = state.get("strategy", {})
        strategy["planning_approach"] = "hierarchical" if feedback.success > 0.7 else "linear"
        state["strategy"] = strategy

        return state

    def _generate_plan(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any],
        cognitive: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a task plan."""
        # Simple hierarchical planning
        complexity = task.get("complexity", 0.5)

        # Determine number of subtasks based on complexity
        num_tasks = max(2, int(complexity * 5))

        tasks = [
            {
                "id": f"task_{i}",
                "description": f"Subtask {i+1} of {task.get('description', 'main task')}",
                "priority": 1.0 - (i / num_tasks),
                "depends_on": f"task_{i-1}" if i > 0 else None
            }
            for i in range(num_tasks)
        ]

        # Consider cognitive load in planning
        load = cognitive.get("cognitive_load", 0.5)
        parallelizable = 3 if load < 0.7 else 1  # Reduce parallelism if fatigued

        return {
            "tasks": tasks,
            "total_steps": num_tasks,
            "parallelizable_groups": parallelizable,
            "effort_estimate": complexity * 10,
            "errors": []
        }


class ResearcherAgent(MemoryAwareAgent):
    """
    Real researcher agent that gathers context and insights.

    Responsibilities:
    - Research task requirements
    - Gather relevant precedents from memory
    - Synthesize actionable insights
    - Evaluate feasibility
    """

    def run(self, state: SystemState) -> Tuple[SystemState, Dict[str, Any]]:
        """Execute research cycle."""
        task = state.get("task", {})
        context = self.recall_context(state)

        # Synthesize research
        research = self._conduct_research(task, context)

        # Update history
        history = state.get("history", [])
        history.append({
            "agent": self.agent_id,
            "action": "research_conducted",
            "insights_found": len(research.get("insights", []))
        })
        state["history"] = history

        return state, {"research": research}

    def evaluate(self, state: SystemState, output: Dict[str, Any]) -> Feedback:
        """Evaluate research quality."""
        research = output.get("research", {})
        insights = research.get("insights", [])

        success = min(1.0, len(insights) / 5.0)

        return {
            "success_score": success,
            "efficiency_score": 0.8,  # Research is usually efficient
            "cognitive_load": state.get("cognitive_state", {}).get("cognitive_load", 0.5),
            "errors": research.get("errors", [])
        }

    def learn(self, state: SystemState, feedback: Feedback) -> SystemState:
        """Learn from research experience."""
        self.save_learning(state, feedback)
        return state

    def _conduct_research(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Conduct research on the task."""
        # Combine memory insights with new analysis
        insights = context.get("insights", [])
        procedures = context.get("procedures", [])

        return {
            "task_analysis": f"Analyzed complexity: {task.get('complexity', 0.5)}",
            "insights": insights,
            "applicable_procedures": procedures,
            "recommendations": [
                f"Use procedure: {p.get('name')}"
                for p in procedures[:3]
            ],
            "feasibility_score": 0.85,
            "errors": []
        }


class ExecutorAgent(MemoryAwareAgent):
    """
    Real executor agent that implements decisions with tools.

    Responsibilities:
    - Execute approved actions
    - Use tools and sandbox safely
    - Handle errors and fallback
    - Report execution results
    """

    def __init__(
        self,
        agent_id: str,
        memory_manager: MemoryManager,
        tool_executor: ToolExecutor = None,
        config: IntegrationConfig = None
    ):
        super().__init__(agent_id, memory_manager, config)
        self.tool_executor = tool_executor or ToolExecutor(config)

    def run(self, state: SystemState) -> Tuple[SystemState, Dict[str, Any]]:
        """Execute task."""
        task = state.get("task", {})

        # Get execution plan from strategy
        strategy = state.get("strategy", {})
        action = strategy.get("action")

        # Execute
        result = self._execute_action(action, task)

        # Update history
        history = state.get("history", [])
        history.append({
            "agent": self.agent_id,
            "action": "executed",
            "success": result.get("success", False)
        })
        state["history"] = history

        return state, {"execution_result": result}

    def evaluate(self, state: SystemState, output: Dict[str, Any]) -> Feedback:
        """Evaluate execution quality."""
        result = output.get("execution_result", {})
        success = 1.0 if result.get("success") else 0.2

        return {
            "success_score": success,
            "efficiency_score": result.get("efficiency", 0.5),
            "cognitive_load": state.get("cognitive_state", {}).get("cognitive_load", 0.5),
            "errors": result.get("errors", [])
        }

    def learn(self, state: SystemState, feedback: Feedback) -> SystemState:
        """Learn from execution."""
        self.save_learning(state, feedback)
        return state

    def _execute_action(self, action: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action."""
        if not action:
            return {"success": False, "error": "No action specified"}

        action_type = action.get("type", "noop")

        if action_type == "run_code":
            code = action.get("code", "")
            return self.tool_executor.execute_code(code)
        elif action_type == "run_shell":
            cmd = action.get("cmd", "")
            return self.tool_executor.execute_shell(cmd)
        else:
            return {
                "success": True,
                "action_type": action_type,
                "message": f"Executed {action_type}"
            }


class CriticAgent(MemoryAwareAgent):
    """
    Real critic agent that evaluates and provides feedback.

    Responsibilities:
    - Evaluate execution results
    - Provide constructive feedback
    - Identify improvements
    - Update learning signals
    """

    def run(self, state: SystemState) -> Tuple[SystemState, Dict[str, Any]]:
        """Conduct critique."""
        # Analyze execution history
        history = state.get("history", [])

        critique = self._analyze_execution(history, state)

        # Update history
        history.append({
            "agent": self.agent_id,
            "action": "critique_provided",
            "score": critique.get("overall_score", 0)
        })
        state["history"] = history

        return state, {"critique": critique}

    def evaluate(self, state: SystemState, output: Dict[str, Any]) -> Feedback:
        """Self-evaluate critique quality."""
        return {
            "success_score": 0.9,
            "efficiency_score": 0.95,
            "cognitive_load": state.get("cognitive_state", {}).get("cognitive_load", 0.5),
            "errors": []
        }

    def learn(self, state: SystemState, feedback: Feedback) -> SystemState:
        """Learn from critique."""
        self.save_learning(state, feedback)
        return state

    def _analyze_execution(
        self,
        history: List[Dict[str, Any]],
        state: SystemState
    ) -> Dict[str, Any]:
        """Analyze and critique execution."""
        # Count successes
        successes = sum(1 for h in history if h.get("success", False))
        total = max(1, len(history))

        success_rate = successes / total

        # Cognitive metrics
        cognitive = state.get("cognitive_state", {})

        return {
            "overall_score": success_rate,
            "execution_quality": success_rate,
            "cognitive_efficiency": 1.0 - cognitive.get("cognitive_load", 0.5),
            "improvements": [
                "Reduce cognitive load by parallelizing tasks",
                "Reuse successful strategies from memory"
            ] if success_rate < 0.7 else ["Execution quality excellent"],
            "next_steps": ["Continue with current strategy", "Monitor fatigue"],
            "errors": []
        }
