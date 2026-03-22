"""
PII v1.0 Phase 2 — Integration Tests
Tests for integrated agents, memory system, and adaptive loop.
"""

import pytest
import json
import tempfile
from pathlib import Path

from core.phase2_orchestrator import (
    Phase2Orchestrator,
    TaskRequest,
    WorkflowScheduler,
    IntegrationConfig
)
from core.pii_integration import (
    MemoryAwareAgent,
    PlannerAgent,
    ResearcherAgent,
    ExecutorAgent,
    CriticAgent,
    ToolExecutor
)
from core.memory.manager import MemoryManager
from core.system_state import initialize_system_state
from core.types import Task


class TestIntegrationConfig:
    """Test integration configuration."""

    def test_default_config(self):
        config = IntegrationConfig()
        assert config.use_memory is True
        assert config.use_tools is True
        assert config.safe_mode is True

    def test_custom_config(self):
        config = IntegrationConfig(
            use_memory=False,
            use_tools=False,
            safe_mode=False
        )
        assert config.use_memory is False
        assert config.use_tools is False
        assert config.safe_mode is False


class TestMemoryAwareAgent:
    """Test memory-aware agent functionality."""

    @pytest.fixture
    def memory_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield MemoryManager(tmpdir)

    def test_agent_initialization(self, memory_manager):
        config = IntegrationConfig()
        agent = PlannerAgent("test_planner", memory_manager, config)

        assert agent.agent_id == "test_planner"
        assert agent.memory_manager is memory_manager
        assert agent.config is config

    def test_recall_context_empty(self, memory_manager):
        """Test recall with no prior memories."""
        config = IntegrationConfig()
        agent = PlannerAgent("test_planner", memory_manager, config)

        state = initialize_system_state(
            Task(id="1", description="Test task", complexity=0.5)
        )

        context = agent.recall_context(state)

        assert "similar_task" in context
        assert "insights" in context
        assert "procedures" in context

    def test_save_learning(self, memory_manager):
        """Test saving learning to memory."""
        config = IntegrationConfig()
        agent = PlannerAgent("test_planner", memory_manager, config)

        state = initialize_system_state(
            Task(id="1", description="Test task", complexity=0.5)
        )

        feedback = {
            "success_score": 0.9,
            "efficiency_score": 0.85,
            "cognitive_load": 0.3,
            "errors": []
        }

        # Should not raise
        agent.save_learning(state, feedback)


class TestPlannerAgent:
    """Test planner agent functionality."""

    @pytest.fixture
    def planner(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_manager = MemoryManager(tmpdir)
            config = IntegrationConfig(safe_mode=False)
            yield PlannerAgent("planner", memory_manager, config)

    def test_planner_run(self, planner):
        """Test planner execution."""
        state = initialize_system_state(
            Task(id="1", description="Test task", complexity=0.5)
        )

        state, output = planner.run(state)

        assert "plan" in output
        assert "tasks" in output["plan"]
        assert len(output["plan"]["tasks"]) > 0

    def test_planner_evaluate(self, planner):
        """Test planner evaluation."""
        state = initialize_system_state(
            Task(id="1", description="Test task", complexity=0.5)
        )

        output = {
            "plan": {
                "tasks": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
                "effort_estimate": 5.0,
                "errors": []
            }
        }

        feedback = planner.evaluate(state, output)

        assert "success_score" in feedback
        assert "efficiency_score" in feedback
        assert feedback["success_score"] > 0.0

    def test_planner_learn(self, planner):
        """Test planner learning."""
        state = initialize_system_state(
            Task(id="1", description="Test task", complexity=0.5)
        )

        feedback = {
            "success_score": 0.8,
            "efficiency_score": 0.85,
            "cognitive_load": 0.3,
            "errors": []
        }

        new_state = planner.learn(state, feedback)

        assert "strategy" in new_state
        assert "planning_approach" in new_state["strategy"]


class TestResearcherAgent:
    """Test researcher agent functionality."""

    @pytest.fixture
    def researcher(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_manager = MemoryManager(tmpdir)
            config = IntegrationConfig(safe_mode=False)
            yield ResearcherAgent("researcher", memory_manager, config)

    def test_researcher_run(self, researcher):
        """Test researcher execution."""
        state = initialize_system_state(
            Task(id="1", description="Test task", complexity=0.5)
        )

        state, output = researcher.run(state)

        assert "research" in output
        assert "insights" in output["research"]

    def test_researcher_evaluate(self, researcher):
        """Test researcher evaluation."""
        state = initialize_system_state(
            Task(id="1", description="Test task", complexity=0.5)
        )

        output = {
            "research": {
                "insights": [{}, {}, {}],
                "errors": []
            }
        }

        feedback = researcher.evaluate(state, output)

        assert feedback["success_score"] > 0.0


class TestExecutorAgent:
    """Test executor agent functionality."""

    @pytest.fixture
    def executor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_manager = MemoryManager(tmpdir)
            config = IntegrationConfig(safe_mode=False)
            tool_executor = ToolExecutor(config)
            yield ExecutorAgent("executor", memory_manager, tool_executor, config)

    def test_executor_run_noop(self, executor):
        """Test executor with no-op action."""
        state = initialize_system_state(
            Task(id="1", description="Test task", complexity=0.5)
        )
        state["strategy"] = {"action": None}

        state, output = executor.run(state)

        assert "execution_result" in output

    def test_executor_evaluate(self, executor):
        """Test executor evaluation."""
        state = initialize_system_state(
            Task(id="1", description="Test task", complexity=0.5)
        )

        output = {
            "execution_result": {"success": True, "errors": []}
        }

        feedback = executor.evaluate(state, output)

        assert feedback["success_score"] == 1.0


class TestCriticAgent:
    """Test critic agent functionality."""

    @pytest.fixture
    def critic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_manager = MemoryManager(tmpdir)
            config = IntegrationConfig(safe_mode=False)
            yield CriticAgent("critic", memory_manager, config)

    def test_critic_run(self, critic):
        """Test critic execution."""
        state = initialize_system_state(
            Task(id="1", description="Test task", complexity=0.5)
        )

        state, output = critic.run(state)

        assert "critique" in output
        assert "overall_score" in output["critique"]

    def test_critic_evaluate(self, critic):
        """Test critic self-evaluation."""
        state = initialize_system_state(
            Task(id="1", description="Test task", complexity=0.5)
        )

        feedback = critic.evaluate(state, {})

        assert feedback["success_score"] == 0.9


class TestPhase2Orchestrator:
    """Test orchestrator functionality."""

    @pytest.fixture
    def orchestrator(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = IntegrationConfig(safe_mode=False)
            yield Phase2Orchestrator(tmpdir, config)

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert "planner" in orchestrator.agents
        assert "researcher" in orchestrator.agents
        assert "executor" in orchestrator.agents
        assert "critic" in orchestrator.agents

    def test_execute_task_simple(self, orchestrator):
        """Test simple task execution."""
        request = TaskRequest(
            task_id="task_1",
            description="Simple test task",
            complexity=0.3,
            max_cycles=1
        )

        result = orchestrator.execute_task(request)

        assert result.task_id == "task_1"
        assert result.success is True or len(result.errors) == 0
        assert result.cycles_executed >= 1

    def test_execute_task_with_max_cycles(self, orchestrator):
        """Test task execution with cycle limits."""
        request = TaskRequest(
            task_id="task_2",
            description="Multi-cycle task",
            complexity=0.7,
            max_cycles=3
        )

        result = orchestrator.execute_task(request)

        assert result.cycles_executed <= 3

    def test_cognitive_metrics(self, orchestrator):
        """Test cognitive metrics retrieval."""
        metrics = orchestrator.get_cognitive_metrics()

        assert isinstance(metrics, dict)

    def test_orchestrator_reset(self, orchestrator):
        """Test orchestrator reset."""
        orchestrator.reset()

        assert orchestrator.adaptive_loop is not None


class TestWorkflowScheduler:
    """Test workflow scheduler functionality."""

    @pytest.fixture
    def scheduler(self):
        return WorkflowScheduler(max_concurrent=2)

    def test_submit_task(self, scheduler):
        """Test task submission."""
        request = TaskRequest(
            task_id="task_1",
            description="Test task",
            complexity=0.5
        )

        task_id = scheduler.submit_task(request)

        assert task_id == "task_1"

    def test_get_queued_status(self, scheduler):
        """Test getting status of queued task."""
        request = TaskRequest(
            task_id="task_1",
            description="Test task",
            complexity=0.5
        )

        scheduler.submit_task(request)
        status = scheduler.get_task_status("task_1")

        assert status["status"] == "queued"
        assert status["task_id"] == "task_1"

    def test_process_queue(self, scheduler):
        """Test queue processing."""
        request = TaskRequest(
            task_id="task_1",
            description="Test task",
            complexity=0.3,
            max_cycles=1
        )

        scheduler.submit_task(request)
        scheduler.process_queue()

        status = scheduler.get_task_status("task_1")
        assert status["status"] == "completed"

    def test_get_results(self, scheduler):
        """Test results retrieval."""
        request = TaskRequest(
            task_id="task_1",
            description="Test task",
            complexity=0.3,
            max_cycles=1
        )

        scheduler.submit_task(request)
        scheduler.process_queue()

        result = scheduler.get_results("task_1")

        assert result is not None
        assert result.task_id == "task_1"


class TestToolExecutor:
    """Test tool executor functionality."""

    def test_tools_disabled(self):
        """Test with tools disabled."""
        config = IntegrationConfig(use_tools=False)
        executor = ToolExecutor(config)

        result = executor.execute_code("print('hello')")

        assert "error" in result
        assert result["error"] == "Tools disabled"

    def test_simple_python_execution(self):
        """Test Python code execution."""
        config = IntegrationConfig(use_tools=True, safe_mode=False)
        executor = ToolExecutor(config)

        result = executor.execute_code("print('hello')")

        assert result["success"] is True
        assert "hello" in result["stdout"]


class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    def test_complete_workflow(self):
        """Test complete workflow from task to results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = IntegrationConfig(safe_mode=False)
            orchestrator = Phase2Orchestrator(tmpdir, config)

            # Submit task
            request = TaskRequest(
                task_id="e2e_test",
                description="End-to-end test task",
                complexity=0.5,
                max_cycles=2
            )

            # Execute
            result = orchestrator.execute_task(request)

            # Verify
            assert result.task_id == "e2e_test"
            assert result.cycles_executed > 0
            assert len(result.history) > 0
            assert "planner" in str(result.history)

    def test_workflow_with_error_recovery(self):
        """Test workflow error recovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = IntegrationConfig(safe_mode=False)
            orchestrator = Phase2Orchestrator(tmpdir, config)

            request = TaskRequest(
                task_id="error_test",
                description="Task that may error",
                complexity=0.8,
                max_cycles=1
            )

            # Should not crash even if errors occur
            result = orchestrator.execute_task(request)

            assert result.task_id == "error_test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
