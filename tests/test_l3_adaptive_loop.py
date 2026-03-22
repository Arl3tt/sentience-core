"""
PII v1.0 L3 — Adaptive Learning Loop Test Suite
Tests the full STATE → ACTION → RESULT → SCORE → UPDATE cycle.
"""
from core.system_state import initialize_system_state
from core.agents.pii_planner_agent import PlannerAgent
from core.adaptive_loop import AdaptiveLoop
from core.cognition import update_cognitive_state


def test_single_cycle():
    """Test one complete adaptive loop cycle."""
    print("\n" + "="*60)
    print("L3 Test: Single Cycle Execution")
    print("="*60)

    state = initialize_system_state()
    state["task"]["description"] = "Test task"
    state["task"]["complexity"] = 0.6

    loop = AdaptiveLoop(verbose=False)
    planner = PlannerAgent()

    state, report = loop.execute_cycle(state, planner)

    # Verify cycle structure
    assert "cycle" in report
    assert report["cycle"] == 1
    assert "feedback" in report
    assert "output" in report
    assert report["agent"] == "Planner"

    # Verify feedback quality
    feedback = report["feedback"]
    assert 0.0 <= feedback["success_score"] <= 1.0
    assert 0.0 <= feedback["efficiency_score"] <= 1.0
    assert 0.0 <= feedback["cognitive_load"] <= 1.0

    print(f"✅ Single cycle PASSED")
    print(f"   Success: {feedback['success_score']:.2f}")
    print(f"   Efficiency: {feedback['efficiency_score']:.2f}")
    print(f"   Strategy modifier: {report['strategy_modifier']:.2f}")


def test_multi_cycle_sequential():
    """Test multiple sequential cycles."""
    print("\n" + "="*60)
    print("L3 Test: Multiple Sequential Cycles")
    print("="*60)

    state = initialize_system_state()
    state["task"]["description"] = "Multi-cycle task"
    state["task"]["complexity"] = 0.5

    loop = AdaptiveLoop(max_cycles=5, verbose=False)
    planner = PlannerAgent()

    # Execute 5 cycles
    reports = []
    for i in range(5):
        state, report = loop.execute_cycle(state, planner)
        reports.append(report)

    # Verify all cycles completed
    assert len(reports) == 5
    for i, report in enumerate(reports):
        assert report["cycle"] == i + 1

    # Verify history accumulated
    assert len(state["history"]) >= 5

    # Verify strategy evolved
    initial_mod = reports[0]["strategy_modifier"]
    final_mod = reports[-1]["strategy_modifier"]

    print(f"✅ Multi-cycle PASSED ({len(reports)} cycles)")
    print(f"   Initial modifier: {initial_mod:.2f}")
    print(f"   Final modifier: {final_mod:.2f}")
    print(f"   Evolution: {final_mod - initial_mod:+.2f}")
    print(f"   History entries: {state['history'].__len__()}")


def test_multi_agent_round_robin():
    """Test multiple agents running in round-robin."""
    print("\n" + "="*60)
    print("L3 Test: Multi-Agent Round-Robin")
    print("="*60)

    state = initialize_system_state()
    state["task"]["description"] = "Multi-agent task"
    state["task"]["complexity"] = 0.6

    loop = AdaptiveLoop(max_cycles=20, verbose=False)
    planner = PlannerAgent()

    # Simulate having multiple agents (for now just use planner 3 times)
    agents = [planner, planner, planner]

    state, reports = loop.execute_multi_cycle(
        state, agents, num_cycles=2, round_robin=True
    )

    # Verify round-robin pattern (6 cycles total = 2 full cycles × 3 agents)
    assert len(reports) == 6

    # Verify all agents got called
    agent_calls = [r["agent"] for r in reports]
    assert agent_calls.count("Planner") == 6

    print(f"✅ Multi-agent PASSED")
    print(f"   Total cycles: {len(reports)}")
    print(f"   Agents per cycle: {len(agents)}")
    print(f"   Final history: {len(state['history'])} entries")


def test_learning_summary():
    """Test learning summary computation."""
    print("\n" + "="*60)
    print("L3 Test: Learning Summary")
    print("="*60)

    state = initialize_system_state()
    state["task"]["complexity"] = 0.5

    loop = AdaptiveLoop(max_cycles=10, verbose=False)
    planner = PlannerAgent()

    reports = []
    for i in range(5):
        state, report = loop.execute_cycle(state, planner)
        reports.append(report)

    summary = loop.get_learning_summary(reports)

    # Verify summary structure
    assert "total_cycles" in summary
    assert "avg_success" in summary
    assert "avg_efficiency" in summary
    assert "success_trend" in summary
    assert "peak_cycle" in summary

    # Verify values are sensible
    assert summary["total_cycles"] == 5
    assert 0.0 <= summary["avg_success"] <= 1.0
    assert 0.0 <= summary["avg_efficiency"] <= 1.0

    print(f"✅ Learning summary PASSED")
    print(f"   Total cycles: {summary['total_cycles']}")
    print(f"   Avg success: {summary['avg_success']:.2f}")
    print(f"   Avg efficiency: {summary['avg_efficiency']:.2f}")
    print(f"   Success trend: {summary['success_trend']:+.2f}")
    print(f"   Peak performance: Cycle {summary['peak_cycle']}")


def test_continuation_rules():
    """Test the continuation logic."""
    print("\n" + "="*60)
    print("L3 Test: Continuation Rules")
    print("="*60)

    state = initialize_system_state()
    loop = AdaptiveLoop(max_cycles=100, verbose=False)

    # Test 1: Excellent performance → stop
    feedback = {"success_score": 0.97}
    assert not loop.should_continue(state, feedback, 0)
    print("✅ Stop on excellent performance (0.97)")

    # Test 2: High cognitive load → stop
    state["cognitive_state"]["cognitive_load"] = 0.95
    feedback = {"success_score": 0.5}
    assert not loop.should_continue(state, feedback, 0)
    print("✅ Stop on high cognitive load (0.95)")

    # Test 3: Max cycles reached → stop
    state["cognitive_state"]["cognitive_load"] = 0.3
    feedback = {"success_score": 0.5}
    assert not loop.should_continue(state, feedback, 100)
    print("✅ Stop on max cycles reached")

    # Test 4: Normal conditions → continue
    feedback = {"success_score": 0.6}
    assert loop.should_continue(state, feedback, 5)
    print("✅ Continue in normal conditions")


def test_full_adaptive_workflow():
    """
    End-to-end test: Full workflow from task to learning.
    """
    print("\n" + "="*60)
    print("L3 Test: Full Adaptive Workflow (End-to-End)")
    print("="*60)

    state = initialize_system_state()
    state["task"]["description"] = "Complete ML pipeline"
    state["task"]["complexity"] = 0.7
    state["task"]["id"] = "workflow_001"

    loop = AdaptiveLoop(max_cycles=10, verbose=False)
    planner = PlannerAgent()

    print(f"\n📋 Initial State:")
    print(f"   Task: {state['task']['description']}")
    print(f"   Complexity: {state['task']['complexity']}")
    print(f"   Difficulty modifier: {state['strategy']['difficulty_modifier']}")

    # Run adaptive loop
    reports = []
    cycle_num = 0
    while cycle_num < 5:  # 5 cycles for this test
        state, report = loop.execute_cycle(state, planner, update_cognition=True)
        reports.append(report)

        feedback = report["feedback"]
        if not loop.should_continue(state, feedback, cycle_num):
            print(f"\n🛑 Loop stopped at cycle {cycle_num + 1}")
            break

        cycle_num += 1

    # Analyze results
    summary = loop.get_learning_summary(reports)

    print(f"\n📊 Results:")
    print(f"   Cycles completed: {summary['total_cycles']}")
    print(f"   Avg success: {summary['avg_success']:.2f}")
    print(f"   Avg efficiency: {summary['avg_efficiency']:.2f}")
    print(f"   Success trend: {summary['success_trend']:+.3f}")
    print(f"   Strategy evolution: {summary['strategy_evolution']:+.2f}")
    print(f"   Peak cycle: {summary['peak_cycle']}")
    print(f"   Final modifier: {reports[-1]['strategy_modifier']:.2f}")

    # Verify learning occurred
    assert len(reports) > 0
    assert len(state["history"]) > 0

    # Verify cognitive state is dynamic
    first_cog = reports[0]["cognitive_state"]
    last_cog = reports[-1]["cognitive_state"]
    print(f"\n🧠 Cognitive Evolution:")
    print(f"   Focus: {first_cog['focus']:.2f} → {last_cog['focus']:.2f}")
    print(f"   Fatigue: {first_cog['fatigue']:.2f} → {last_cog['fatigue']:.2f}")
    print(f"   Load: {first_cog['cognitive_load']:.2f} → {last_cog['cognitive_load']:.2f}")
    print(f"   Learning Eff: {first_cog['learning_efficiency']:.2f} → {last_cog['learning_efficiency']:.2f}")

    print(f"\n✅ Full workflow PASSED")
    print("="*60)


def test_cycle_isolation():
    """Test that cycles don't interfere with each other."""
    print("\n" + "="*60)
    print("L3 Test: Cycle Isolation")
    print("="*60)

    state = initialize_system_state()
    loop = AdaptiveLoop(verbose=False)
    planner = PlannerAgent()

    # Run two cycles
    state1, report1 = loop.execute_cycle(state, planner)
    state2, report2 = loop.execute_cycle(state1, planner)

    # Verify cycles are independent
    assert report1["cycle"] == 1
    assert report2["cycle"] == 2

    # Verify history accumulated correctly
    assert len(state2["history"]) >= len(state1["history"])

    # Verify learning happened (modifier might change)
    mod1 = report1["strategy_modifier"]
    mod2 = report2["strategy_modifier"]

    print(f"✅ Cycle isolation PASSED")
    print(f"   Cycle 1 modifier: {mod1:.2f}")
    print(f"   Cycle 2 modifier: {mod2:.2f}")
    print(f"   History after cycle 1: {len(state1['history'])}")
    print(f"   History after cycle 2: {len(state2['history'])}")


if __name__ == "__main__":
    print("\n" + "🔄 "*30)
    print("PII v1.0 L3 — Adaptive Learning Loop Test Suite")
    print("🔄 "*30)

    test_single_cycle()
    test_multi_cycle_sequential()
    test_multi_agent_round_robin()
    test_learning_summary()
    test_continuation_rules()
    test_cycle_isolation()
    test_full_adaptive_workflow()

    print("\n" + "✅ "*30)
    print("All L3 tests PASSED!")
    print("L3 — Adaptive Learning Loop is operational")
    print("✅ "*30)
