"""
PII v1.0 Foundation Test Suite
Tests the BaseAgent architecture and core cognitive loop.
"""
from core.system_state import initialize_system_state
from core.agents.pii_planner_agent import PlannerAgent


def test_planner_cognitive_loop():
    """
    Test the complete cognitive loop: run() → evaluate() → learn()
    """
    # Initialize fresh state
    state = initialize_system_state()

    # Set task
    state["task"]["description"] = "Build a neural network model"
    state["task"]["complexity"] = 0.7
    state["task"]["id"] = "ml_task_001"

    # Create agent
    planner = PlannerAgent()

    print("\n" + "="*60)
    print("PII v1.0 Foundation Test: Planner Cognitive Loop")
    print("="*60)

    # Phase 1: RUN
    print("\n[PHASE 1] RUN - Agent executes primary function")
    state, output = planner.run(state)
    print(f"✓ Plan created with {len(output['steps'])} steps")
    print(f"  Original complexity: {output['original_complexity']}")
    print(f"  Adjusted complexity: {output['adjusted_complexity']}")

    # Phase 2: EVALUATE
    print("\n[PHASE 2] EVALUATE - Agent evaluates output quality")
    feedback = planner.evaluate(state, output)
    print(f"✓ Feedback generated")
    print(f"  Success score: {feedback['success_score']:.2f}")
    print(f"  Efficiency score: {feedback['efficiency_score']:.2f}")
    print(f"  Cognitive load: {feedback['cognitive_load']:.2f}")

    # Phase 3: LEARN
    print("\n[PHASE 3] LEARN - Agent adapts strategy")
    original_modifier = state["strategy"]["difficulty_modifier"]
    state = planner.learn(state, feedback)
    new_modifier = state["strategy"]["difficulty_modifier"]
    print(f"✓ Strategy updated")
    print(f"  Original modifier: {original_modifier}")
    print(f"  New modifier: {new_modifier}")

    # Verify state integrity
    print("\n[VERIFICATION] State Integrity Checks")
    assert state["task"]["id"] == "ml_task_001", "Task ID should persist"
    assert len(state["history"]) > 0, "History should contain actions"
    assert 0.0 <= state["strategy"]["difficulty_modifier"] <= 2.0, "Modifier should be bounded"
    print("✓ All state integrity checks passed")

    # Print final state
    print("\n[FINAL STATE]")
    print(f"  History length: {len(state['history'])}")
    print(f"  Strategy approach: {state['strategy']['approach']}")
    print(f"  Difficulty modifier: {state['strategy']['difficulty_modifier']:.2f}")

    print("\n" + "="*60)
    print("✅ Test PASSED: Complete cognitive loop operational")
    print("="*60)


def test_high_cognitive_load_adaptation():
    """
    Test that planner adapts when cognitive load is high.
    """
    state = initialize_system_state()
    state["task"]["description"] = "Complex data analysis"
    state["task"]["complexity"] = 0.9
    state["cognitive_state"]["cognitive_load"] = 0.85  # High load

    planner = PlannerAgent()

    print("\n" + "="*60)
    print("PII v1.0 Test: High Cognitive Load Adaptation")
    print("="*60)

    state, output = planner.run(state)
    feedback = planner.evaluate(state, output)

    print(f"Cognitive load: {feedback['cognitive_load']:.2f} (HIGH)")
    print(f"Before adaptation: modifier = {state['strategy']['difficulty_modifier']}")

    state = planner.learn(state, feedback)

    print(f"After adaptation: modifier = {state['strategy']['difficulty_modifier']:.2f}")
    assert state["strategy"]["difficulty_modifier"] < 1.0, "Should reduce difficulty under high load"

    print("✅ Adaptation works correctly under stress")
    print("="*60)


def test_excellent_performance_difficulty_increase():
    """
    Test that planner increases difficulty on excellent performance.
    """
    state = initialize_system_state()
    state["task"]["description"] = "Simple task"
    state["task"]["complexity"] = 0.4  # Closer to 0.5 for better success score
    state["cognitive_state"]["cognitive_load"] = 0.1  # Very low load

    planner = PlannerAgent()

    print("\n" + "="*60)
    print("PII v1.0 Test: Difficulty Increase on Success")
    print("="*60)

    state, output = planner.run(state)
    feedback = planner.evaluate(state, output)

    print(f"Success score: {feedback['success_score']:.2f} (EXCELLENT)")
    print(f"Before adaptation: modifier = {state['strategy']['difficulty_modifier']}")

    state = planner.learn(state, feedback)

    print(f"After adaptation: modifier = {state['strategy']['difficulty_modifier']:.2f}")
    assert state["strategy"]["difficulty_modifier"] > 1.0, "Should increase difficulty on success"

    print("✅ Difficulty scaling works correctly")
    print("="*60)


if __name__ == "__main__":
    # Run all tests
    test_planner_cognitive_loop()
    test_high_cognitive_load_adaptation()
    test_excellent_performance_difficulty_increase()

    print("\n" + "🎯 "*30)
    print("All PII v1.0 foundation tests PASSED!")
    print("The Intelligence Kernel (L1) is operational.")
    print("🎯 "*30)