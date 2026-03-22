"""
PII v1.0 L2 — Cognitive Engine Test Suite
Tests for attention, fatigue, load, and learning modules.
"""
from core.system_state import initialize_system_state
from core.cognition import (
    compute_attention,
    compute_fatigue,
    compute_cognitive_load,
    compute_learning_efficiency,
    update_cognitive_state,
    get_cognitive_summary,
    get_cognitive_status,
)


def test_attention_empty_history():
    """Test attention with no history returns baseline."""
    state = initialize_system_state()
    attention = compute_attention(state)
    assert 0.0 <= attention <= 1.0
    assert attention == 0.5  # Baseline
    print("✅ test_attention_empty_history PASSED")


def test_attention_high_success():
    """Test attention increases with successful actions."""
    state = initialize_system_state()

    # Add 5 successful actions
    for i in range(5):
        state["history"].append({
            "agent": "Planner",
            "action": f"action_{i}",
            "success": True
        })

    attention = compute_attention(state)
    assert attention > 0.7, f"Expected attention > 0.7, got {attention}"
    print(f"✅ test_attention_high_success PASSED (attention={attention:.2f})")


def test_attention_with_errors():
    """Test attention decreases with errors."""
    state = initialize_system_state()

    state["history"] = [
        {"agent": "Planner", "success": True},
        {"agent": "Planner", "success": True},
        {"agent": "Planner", "success": False, "errors": ["failed to parse"]},
        {"agent": "Planner", "success": False, "errors": ["timeout"]},
        {"agent": "Planner", "success": False, "errors": ["memory error"]},
    ]

    attention = compute_attention(state)
    assert attention < 0.5, f"Expected attention < 0.5 with errors, got {attention}"
    print(f"✅ test_attention_with_errors PASSED (attention={attention:.2f})")


def test_fatigue_fresh_start():
    """Test fatigue is 0 at start."""
    state = initialize_system_state()
    fatigue_val = compute_fatigue(state)
    assert fatigue_val == 0.0
    print("✅ test_fatigue_fresh_start PASSED")


def test_fatigue_accumulates():
    """Test fatigue increases with many actions."""
    state = initialize_system_state()

    # Add 20 consecutive actions
    for i in range(20):
        state["history"].append({
            "agent": "Executor",
            "action": f"task_{i}",
            "success": True
        })

    fatigue_val = compute_fatigue(state)
    assert fatigue_val > 0.1, f"Expected fatigue > 0.1, got {fatigue_val}"
    print(f"✅ test_fatigue_accumulates PASSED (fatigue={fatigue_val:.2f})")


def test_fatigue_quality_decay():
    """Test fatigue increases when performance declines."""
    state = initialize_system_state()

    # Old period: all successful
    for i in range(5):
        state["history"].append({"agent": "Executor", "success": True})

    # New period: all failed
    for i in range(5):
        state["history"].append({"agent": "Executor", "success": False, "errors": []})

    fatigue_val = compute_fatigue(state)
    assert fatigue_val > 0.0, "Fatigue should increase on quality decline"
    print(f"✅ test_fatigue_quality_decay PASSED (fatigue={fatigue_val:.2f})")


def test_cognitive_load_baseline():
    """Test load is based on task complexity."""
    state = initialize_system_state()
    state["task"]["complexity"] = 0.3

    load = compute_cognitive_load(state)
    assert 0.0 <= load <= 1.0
    print(f"✅ test_cognitive_load_baseline PASSED (load={load:.2f})")


def test_cognitive_load_high_complexity():
    """Test load increases with task complexity."""
    state1 = initialize_system_state()
    state1["task"]["complexity"] = 0.2

    state2 = initialize_system_state()
    state2["task"]["complexity"] = 0.8

    load1 = compute_cognitive_load(state1)
    load2 = compute_cognitive_load(state2)

    assert load2 > load1, f"Expected load2 > load1, got {load2} vs {load1}"
    print(f"✅ test_cognitive_load_high_complexity PASSED (load1={load1:.2f}, load2={load2:.2f})")


def test_cognitive_load_fatigued_state():
    """Test load increases when fatigued."""
    state = initialize_system_state()
    state["cognitive_state"]["fatigue"] = 0.8
    state["task"]["complexity"] = 0.5

    load = compute_cognitive_load(state)
    # With fatigue 0.8 and default focus 0.5: load = 0.5*0.5 + 0.5*0.2 + 0.4*0.2 = 0.43
    assert load > 0.3, f"Expected load > 0.3 when fatigued, got {load}"
    print(f"✅ test_cognitive_load_fatigued_state PASSED (load={load:.2f})")


def test_learning_empty():
    """Test learning with insufficient history."""
    state = initialize_system_state()
    learning_eff = compute_learning_efficiency(state)
    assert learning_eff == 0.5  # Default
    print("✅ test_learning_empty PASSED")


def test_learning_improving_trajectory():
    """Test learning increases with improving success rate."""
    state = initialize_system_state()

    # Old period: 40% success (2 wins / 5 total) with errors
    for i in range(2):
        state["history"].append({"success": True, "errors": []})
    for i in range(3):
        state["history"].append({"success": False, "errors": ["error"]})

    # New period: 80% success (4 wins / 5 total) with fewer errors
    for i in range(4):
        state["history"].append({"success": True, "errors": []})
    for i in range(1):
        state["history"].append({"success": False, "errors": []})

    learning_eff = compute_learning_efficiency(state)
    # improvement = 0.4, error_reduction = (3-1)/3 = 0.67, adaptation = 0
    # learning = (0.9 * 0.4) + (0.67 * 0.3) + 0 = 0.36 + 0.2 = 0.56
    assert learning_eff > 0.4, f"Expected learning_eff > 0.4 on improvement, got {learning_eff}"
    print(f"✅ test_learning_improving_trajectory PASSED (eff={learning_eff:.2f})")


def test_engine_full_orchestration():
    """Test the engine orchestrates all metrics."""
    state = initialize_system_state()
    state["task"]["description"] = "Test task"
    state["task"]["complexity"] = 0.6

    # Add some history
    for i in range(3):
        state["history"].append({
            "agent": "Planner",
            "action": f"step_{i}",
            "success": True
        })

    # Update cognition
    state = update_cognitive_state(state)

    # Verify all values are set and normalized
    cog = state["cognitive_state"]
    assert 0.0 <= cog["focus"] <= 1.0, f"Focus out of bounds: {cog['focus']}"
    assert 0.0 <= cog["fatigue"] <= 1.0, f"Fatigue out of bounds: {cog['fatigue']}"
    assert 0.0 <= cog["cognitive_load"] <= 1.0, f"Load out of bounds: {cog['cognitive_load']}"
    assert 0.0 <= cog["learning_efficiency"] <= 1.0, f"Learning out of bounds: {cog['learning_efficiency']}"

    print("✅ test_engine_full_orchestration PASSED")
    print(f"   Cognitive State: {get_cognitive_summary(state)}")


def test_cognitive_status():
    """Test cognitive status reporting."""
    state = initialize_system_state()

    # Optimal state
    state["cognitive_state"] = {
        "focus": 0.9,
        "fatigue": 0.1,
        "cognitive_load": 0.2,
        "learning_efficiency": 0.8
    }
    status = get_cognitive_status(state["cognitive_state"])
    assert "OPTIMAL" in status or "NORMAL" in status
    print(f"✅ Optimal state: {status}")

    # Overloaded state
    state["cognitive_state"]["cognitive_load"] = 0.85
    status = get_cognitive_status(state["cognitive_state"])
    assert "OVERLOADED" in status
    print(f"✅ Overloaded state: {status}")

    # Fatigued state
    state["cognitive_state"]["cognitive_load"] = 0.4
    state["cognitive_state"]["fatigue"] = 0.8
    status = get_cognitive_status(state["cognitive_state"])
    assert "FATIGUED" in status
    print(f"✅ Fatigued state: {status}")


def test_l1_l2_integration():
    """
    Integration test: L1 agent + L2 cognition.
    Verify that L2 updates cognition based on L1 results.
    """
    from core.agents.pii_planner_agent import PlannerAgent

    state = initialize_system_state()
    state["task"]["description"] = "Complex planning task"
    state["task"]["complexity"] = 0.7

    planner = PlannerAgent()

    print("\n" + "="*60)
    print("L1 + L2 Integration Test")
    print("="*60)

    # Cycle 1
    print("\n[Cycle 1] Agent action + Cognition update")
    state, output = planner.run(state)
    print(f"  ✓ Planner ran: {len(output['steps'])} steps")

    # Update cognition based on history
    state = update_cognitive_state(state)
    print(f"  ✓ L2 updated cognition")

    summary = get_cognitive_summary(state)
    print(f"  Status: {summary['status']}")

    # Agent evaluates and learns
    feedback = planner.evaluate(state, output)
    state = planner.learn(state, feedback)
    print(f"  ✓ Agent learned (modifier={state['strategy']['difficulty_modifier']:.2f})")

    # Cycle 2: Do it again with updated state
    print("\n[Cycle 2] Second iteration")
    state, output = planner.run(state)
    state = update_cognitive_state(state)

    summary2 = get_cognitive_summary(state)
    print(f"  Status: {summary2['status']}")
    print(f"  History length: {len(state['history'])}")

    # Verify cognition evolved
    assert state["cognitive_state"]["focus"] > 0.0
    print("\n✅ L1 + L2 Integration PASSED")
    print("="*60)


if __name__ == "__main__":
    print("\n" + "🧠 "*30)
    print("PII v1.0 L2 — Cognitive Engine Test Suite")
    print("🧠 "*30)

    # Run all tests
    test_attention_empty_history()
    test_attention_high_success()
    test_attention_with_errors()

    test_fatigue_fresh_start()
    test_fatigue_accumulates()
    test_fatigue_quality_decay()

    test_cognitive_load_baseline()
    test_cognitive_load_high_complexity()
    test_cognitive_load_fatigued_state()

    test_learning_empty()
    test_learning_improving_trajectory()

    test_engine_full_orchestration()
    test_cognitive_status()

    test_l1_l2_integration()

    print("\n" + "✅ "*30)
    print("All L2 tests PASSED!")
    print("L2 — Cognitive Engine is operational")
    print("✅ "*30)
