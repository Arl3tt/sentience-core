"""
PII v1.0 Phase 2 — Memory Layer Tests
Verify episodic, semantic, and procedural memory systems.
"""
from core.system_state import initialize_system_state
from core.agents.pii_planner_agent import PlannerAgent
from core.adaptive_loop import AdaptiveLoop
from core.memory import MemoryManager, EpisodicStore, SemanticStore, ProceduralStore
import tempfile
import shutil


def test_episodic_store():
    """Test episodic memory: recording what happened."""
    print("\n" + "="*60)
    print("Test: Episodic Memory Store")
    print("="*60)

    # Use temp directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        store = EpisodicStore(f"{tmpdir}/episodic.db")

        # Create a mock cycle report
        state = initialize_system_state()
        state["task"]["id"] = "test_001"

        report = {
            "cycle": 1,
            "agent": "Planner",
            "feedback": {
                "success_score": 0.8,
                "efficiency_score": 0.75,
                "cognitive_load": 0.4,
                "errors": []
            },
            "cognitive_state": {
                "focus": 0.8,
                "fatigue": 0.1,
                "cognitive_load": 0.4,
                "learning_efficiency": 0.7
            },
            "strategy_modifier": 1.0
        }

        # Record episode
        episode_id = store.record_episode(state, report)
        print(f"✓ Recorded episode: {episode_id}")

        # Retrieve history
        history = store.get_task_history("test_001")
        assert len(history) == 1
        assert history[0]["success_score"] == 0.8
        print(f"✓ Retrieved history: {len(history)} episodes")

        # Get learning curve
        curve = store.get_learning_curve("test_001")
        assert "total_cycles" in curve
        print(f"✓ Learning curve computed: {curve['total_cycles']} cycles")

        # Get statistics
        stats = store.get_statistics()
        print(f"✓ Statistics: {stats['total_episodes']} episodes recorded")

        # Explicitly close connection
        del store

    print("✅ Episodic store test PASSED")


def test_semantic_store():
    """Test semantic memory: learning patterns."""
    print("\n" + "="*60)
    print("Test: Semantic Memory Store")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        store = SemanticStore(f"{tmpdir}/semantic.json")

        # Record insights
        id1 = store.record_insight(
            category="strategy",
            description="Conservative strategy works for high complexity",
            evidence_score=0.85,
            applicable_complexity=0.8,
            metadata={"approach": "cautious"}
        )
        print(f"✓ Recorded insight: {id1}")

        # Get insights by category
        strategies = store.get_insights_by_category("strategy")
        assert len(strategies) > 0
        print(f"✓ Retrieved {len(strategies)} strategy insights")

        # Get applicable insights
        applicable = store.get_applicable_insights(0.75)
        assert len(applicable) > 0
        print(f"✓ Found {len(applicable)} applicable insights")

        # Suggest strategy
        suggestion = store.suggest_strategy(0.8)
        assert suggestion is not None
        print(f"✓ Strategy suggestion: {suggestion['suggestion']}")

        # Statistics
        stats = store.statistics()
        assert stats["total_insights"] > 0
        print(f"✓ Statistics: {stats['total_insights']} insights stored")

    print("✅ Semantic store test PASSED")


def test_procedural_store():
    """Test procedural memory: learned procedures."""
    print("\n" + "="*60)
    print("Test: Procedural Memory Store")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        store = ProceduralStore(f"{tmpdir}/procedural.json")

        # Check default procedures initialized
        procedures = store.procedures
        assert len(procedures) > 0
        print(f"✓ Initialized with {len(procedures)} default procedures")

        # Find applicable procedures for high fatigue
        state = {
            "focus": 0.8,
            "fatigue": 0.8,
            "cognitive_load": 0.5
        }

        applicable = store.find_applicable_procedures(state)
        assert len(applicable) > 0
        print(f"✓ Found {len(applicable)} applicable procedures for state")

        # Execute a procedure
        if applicable:
            proc_id = applicable[0].procedure_id
            result = store.execute_procedure(proc_id)
            assert result["procedure"]
            print(f"✓ Executed procedure: {result['procedure']}")

            # Update success rate
            store.update_success_rate(proc_id, success=True)
            print(f"✓ Updated success rate")

        # Get best procedure
        best = store.get_best_procedure()
        if best:
            print(f"✓ Best procedure: {best.name} ({best.success_rate:.2f})")

        # Statistics
        stats = store.statistics()
        print(f"✓ Statistics: { stats['total_procedures']} procedures")

    print("✅ Procedural store test PASSED")


def test_memory_manager():
    """Test central memory manager."""
    print("\n" + "="*60)
    print("Test: Memory Manager Integration")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MemoryManager(tmpdir)

        # Simulate a task execution
        state = initialize_system_state()
        state["task"]["id"] = "learn_001"
        state["task"]["complexity"] = 0.7

        report = {
            "cycle": 1,
            "agent": "Planner",
            "feedback": {
                "success_score": 0.88,
                "efficiency_score": 0.8,
                "cognitive_load": 0.4,
                "errors": []
            },
            "cognitive_state": {
                "focus": 0.85,
                "fatigue": 0.1,
                "cognitive_load": 0.4,
                "learning_efficiency": 0.75
            },
            "strategy_modifier": 1.1
        }

        # Record outcome
        manager.record_cycle_outcome(state, report)
        print("✓ Recorded cycle outcome")

        # Recall similar task
        similar = manager.recall_similar_tasks(0.7)
        if similar:
            print(f"✓ Recalled similar task: {similar['task_id']}")

        # Get applicable insights
        insights = manager.recall_applicable_insights(0.7)
        print(f"✓ Retrieved {len(insights)} applicable insights")

        # Get applicable procedures
        local_state = {
            "focus": 0.85,
            "fatigue": 0.1,
            "cognitive_load": 0.4
        }
        procedures = manager.get_applicable_procedures(local_state)
        print(f"✓ Found {len(procedures)} applicable procedures")

        # Get memory summary
        summary = manager.get_memory_summary()
        print(f"✓ Memory summary: {summary}")

        # Suggest next action
        suggestion = manager.suggest_next_action(state)
        if suggestion:
            print(f"✓ Suggestion: {suggestion['action']}")

        # Explicitly close
        del manager

    print("✅ Memory manager test PASSED")


def test_memory_persistence():
    """Test that memory persists across sessions."""
    print("\n" + "="*60)
    print("Test: Memory Persistence")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Session 1: Record something
        store1 = EpisodicStore(f"{tmpdir}/episodic.db")

        state = initialize_system_state()
        state["task"]["id"] = "persist_001"

        report = {
            "cycle": 1,
            "agent": "Planner",
            "feedback": {"success_score": 0.9, "efficiency_score": 0.85, "cognitive_load": 0.3, "errors": []},
            "cognitive_state": {"focus": 0.9, "fatigue": 0.05, "cognitive_load": 0.3, "learning_efficiency": 0.8},
            "strategy_modifier": 1.2
        }

        store1.record_episode(state, report)
        print("✓ Session 1: Recorded episode")
        del store1  # Close connection

        # Session 2: Load and verify persistence
        import time
        time.sleep(0.1)  # Brief pause for file locks
        store2 = EpisodicStore(f"{tmpdir}/episodic.db")

        history = store2.get_task_history("persist_001")
        assert len(history) == 1
        assert history[0]["success_score"] == 0.9
        print("✓ Session 2: Memory persisted correctly")

        # Check statistics were retained
        stats = store2.get_statistics()
        assert stats["total_episodes"] == 1
        print(f"✓ Statistics persisted: {stats['total_episodes']} episodes")

        del store2

    print("✅ Persistence test PASSED")


def test_full_adaptive_loop_with_memory():
    """Full end-to-end: Adaptive loop + Memory."""
    print("\n" + "="*60)
    print("Test: Full System with Memory Integration")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MemoryManager(tmpdir)
        loop = AdaptiveLoop(max_cycles=5, verbose=False)
        planner = PlannerAgent()

        state = initialize_system_state()
        state["task"]["description"] = "Memory test task"
        state["task"]["complexity"] = 0.6

        print("✓ Running adaptive loop with memory...")

        # Run cycles
        reports = []
        for i in range(3):
            state, _ = loop.execute_cycle(state, planner, update_cognition=True)
            # Manually get report for testing
            state_report = {
                "cycle": i+1,
                "agent": planner.name,
                "feedback": {
                    "success_score": 0.7 + (i * 0.05),
                    "efficiency_score": 0.65,
                    "cognitive_load": 0.4,
                    "errors": []
                },
                "cognitive_state": state["cognitive_state"].copy(),
                "strategy_modifier": state["strategy"]["difficulty_modifier"]
            }
            manager.record_cycle_outcome(state, state_report)
            reports.append(state_report)

        print(f"✓ Completed {len(reports)} cycles")

        # Check memory was populated
        summary = manager.get_memory_summary()
        assert summary["episodic"]["total_episodes"] > 0
        print(f"✓ Memory populated: {summary['episodic']['total_episodes']} episodes")

        # Verify learning curve
        learning = manager.get_learning_summary(state["task"]["id"])
        print(f"✓ Learning curve: {learning['learning_curve']}")

        del manager

    print("✅ Full integration test PASSED")


if __name__ == "__main__":
    print("\n" + "🧠 "*30)
    print("PII v1.0 Phase 2 — Memory Layer Test Suite")
    print("🧠 "*30)

    test_episodic_store()
    test_semantic_store()
    test_procedural_store()
    test_memory_manager()
    test_memory_persistence()
    test_full_adaptive_loop_with_memory()

    print("\n" + "✅ "*30)
    print("All Phase 2 Memory Tests PASSED!")
    print("Persistent Intelligence Layer Operational ✅")
    print("✅ "*30)
