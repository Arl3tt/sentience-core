"""
PII v1.0 Phase 3 — User Cognitive Model Tests
Verify personalization, user profiling, and analytics systems.
"""
from core.personalization import UserProfile, UserLearningAnalytics, PersonalizationEngine
from core.memory import MemoryManager
from core.system_state import initialize_system_state
from core.adaptive_loop import AdaptiveLoop
from core.agents.pii_planner_agent import PlannerAgent
import tempfile


def test_user_profile_creation():
    """Test user profile initialization and persistence."""
    print("\n" + "="*60)
    print("Test: User Profile Creation")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        profile = UserProfile("test_user_001", tmpdir)

        # Verify defaults
        assert profile.user_id == "test_user_001"
        assert profile.baseline.avg_focus == 0.65
        assert profile.baseline.fatigue_threshold == 0.75
        assert profile.learning.total_tasks_completed == 0
        print("[OK] Profile created with default baseline")

        # Verify persistence
        profile2 = UserProfile("test_user_001", tmpdir)
        assert profile2.baseline.avg_focus == profile.baseline.avg_focus
        print("[OK] Profile persisted correctly")

        # Get summary
        summary = profile.get_profile_summary()
        assert summary["user_id"] == "test_user_001"
        assert "baseline" in summary
        assert "learning" in summary
        print(f"[OK] Profile summary: focus={summary['baseline']['avg_focus']}")

    print("[PASS] User profile test PASSED\n")


def test_baseline_update():
    """Test updating baseline from cognitive history."""
    print("\n" + "="*60)
    print("Test: Baseline Update from History")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        profile = UserProfile("test_user_002", tmpdir)
        original_focus = profile.baseline.avg_focus

        # Simulate history with higher focus
        history = [
            {"focus": 0.9, "fatigue": 0.2, "learning_efficiency": 0.8},
            {"focus": 0.85, "fatigue": 0.25, "learning_efficiency": 0.75},
            {"focus": 0.88, "fatigue": 0.15, "learning_efficiency": 0.80}
        ]

        profile.update_baseline_from_history(history)

        # Should move towards higher focus
        assert profile.baseline.avg_focus > original_focus
        print(f"[OK] Baseline focus updated: {original_focus:.2f} -> {profile.baseline.avg_focus:.2f}")

        # Verify persistence
        profile2 = UserProfile("test_user_002", tmpdir)
        assert profile2.baseline.avg_focus == profile.baseline.avg_focus
        print("[OK] Updated baseline persisted")

    print("[PASS] Baseline update test PASSED\n")


def test_strategy_registration():
    """Test registering strategy successes."""
    print("\n" + "="*60)
    print("Test: Strategy Registration")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        profile = UserProfile("test_user_003", tmpdir)

        # Register strategy successes
        profile.register_strategy_success("conservative", 0.85)
        profile.register_strategy_success("aggressive", 0.60)
        profile.register_strategy_success("conservative", 0.88)

        assert "conservative" in profile.learning.preferred_strategies
        assert "aggressive" in profile.learning.preferred_strategies
        print("[OK] Strategies registered")

        # Suggest best strategy
        best = profile.suggest_best_strategy()
        assert best == "conservative"
        print(f"[OK] Best strategy identified: {best}")

    print("[PASS] Strategy registration test PASSED\n")


def test_complexity_difficulty_tracking():
    """Test tracking which complexity levels are easy/hard for user."""
    print("\n" + "="*60)
    print("Test: Complexity Difficulty Tracking")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        profile = UserProfile("test_user_004", tmpdir)

        # Register successes and failures
        profile.register_complexity_difficulty(0.3, succeeded=True)   # Easy
        profile.register_complexity_difficulty(0.5, succeeded=True)   # Easy
        profile.register_complexity_difficulty(0.8, succeeded=False)  # Hard
        profile.register_complexity_difficulty(0.9, succeeded=False)  # Hard

        assert 0.3 in profile.learning.strong_complexity_levels
        assert 0.5 in profile.learning.strong_complexity_levels
        assert 0.8 in profile.learning.difficult_complexity_levels
        assert 0.9 in profile.learning.difficult_complexity_levels
        print("[OK] Complexity levels tracked correctly")

    print("[PASS] Complexity tracking test PASSED\n")


def test_personalized_difficulty_adjustment():
    """Test personalized difficulty adjustment."""
    print("\n" + "="*60)
    print("Test: Personalized Difficulty Adjustment")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        profile = UserProfile("test_user_005", tmpdir)

        # Set user's typical focus
        profile.baseline.avg_focus = 0.7
        profile.baseline.fatigue_threshold = 0.75

        # Scenario 1: User is focused and not fatigued
        state = {
            "focus": 0.8,
            "fatigue": 0.2,
            "cognitive_load": 0.4
        }
        adjustment = profile.get_personalized_difficulty_adjustment(1.0, state)
        assert adjustment > 1.0  # Should increase
        print(f"[OK] Good state: difficulty adjusted UP to {adjustment:.2f}")

        # Scenario 2: User's focus dropped
        state = {
            "focus": 0.4,
            "fatigue": 0.3,
            "cognitive_load": 0.4
        }
        adjustment = profile.get_personalized_difficulty_adjustment(1.0, state)
        assert adjustment < 1.0  # Should decrease
        print(f"[OK] Low focus: difficulty adjusted DOWN to {adjustment:.2f}")

        # Scenario 3: User is fatigued
        state = {
            "focus": 0.7,
            "fatigue": 0.8,
            "cognitive_load": 0.4
        }
        adjustment = profile.get_personalized_difficulty_adjustment(1.0, state)
        assert adjustment < 1.0  # Should decrease
        print(f"[OK] High fatigue: difficulty adjusted DOWN to {adjustment:.2f}")

    print("[PASS] Personalized difficulty test PASSED\n")


def test_personalization_engine_integration():
    """Test PersonalizationEngine with MemoryManager."""
    print("\n" + "="*60)
    print("Test: Personalization Engine Integration")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        memory = MemoryManager(tmpdir)
        engine = PersonalizationEngine("test_user_006", memory, tmpdir)

        # Create state
        state = initialize_system_state()
        state["task"]["complexity"] = 0.6
        state["task"]["id"] = "test_task_001"
        state["strategy"]["approach"] = "conservative"

        # Test difficulty recommendation
        diff_rec = engine.recommend_difficulty(state, 1.0)
        assert "adjusted_difficulty" in diff_rec
        assert "rationale" in diff_rec
        print(f"[OK] Difficulty recommendation: {diff_rec['adjusted_difficulty']:.2f}")

        # Test strategy recommendation
        strat_rec = engine.recommend_strategy(state)
        assert "recommended_strategy" in strat_rec
        print(f"[OK] Strategy recommendation: {strat_rec['recommended_strategy']}")

        # Test fatigue prediction
        fatigue_pred = engine.predict_fatigue_risk(state, 5)
        assert "risk_level" in fatigue_pred
        print(f"[OK] Fatigue risk prediction: {fatigue_pred['risk_level']}")

        # Test difficulty rules
        should_reduce = engine.should_reduce_difficulty(state)
        should_increase = engine.should_increase_difficulty(state)
        print(f"[OK] Difficulty rules: reduce={should_reduce}, increase={should_increase}")

        del memory
        del engine

    print("[PASS] Personalization engine test PASSED\n")


def test_personalization_with_adaptive_loop():
    """Test personalization integrated with adaptive loop."""
    print("\n" + "="*60)
    print("Test: Personalization + Adaptive Loop Integration")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        memory = MemoryManager(tmpdir)
        engine = PersonalizationEngine("test_user_007", memory, tmpdir)
        loop = AdaptiveLoop(max_cycles=5, verbose=False)
        planner = PlannerAgent()

        state = initialize_system_state()
        state["task"]["description"] = "Personalization test task"
        state["task"]["complexity"] = 0.6
        state["task"]["id"] = "personalization_test_001"

        print("[OK] Running adaptive loop with personalization...")

        for i in range(3):
            # Get personalization recommendation BEFORE cycle
            diff_rec = engine.recommend_difficulty(state, 1.0)
            strat_rec = engine.recommend_strategy(state)

            # Run cycle
            state, output = loop.execute_cycle(state, planner, update_cognition=True)

            # Register outcome to update personalization
            report = {
                "cycle": i + 1,
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

            engine.register_task_outcome(state, report)
            memory.record_cycle_outcome(state, report)

            print(f"  Cycle {i+1}: Diff={diff_rec['adjusted_difficulty']:.2f}, Strategy={strat_rec['recommended_strategy']}")

        # Get final summary
        summary = engine.get_personalization_summary()
        assert summary["personalization_status"] == "active"
        print(f"[OK] Personalization completed: {state['task']['id']}")
        print(f"[OK] User profile: tasks={engine.profile.learning.total_tasks_completed}, cycles={engine.profile.learning.total_cycles}")

        del memory
        del engine

    print("[PASS] Personalization + adaptive loop test PASSED\n")


def test_user_profile_convergence():
    """Test that user profile converges to actual user characteristics."""
    print("\n" + "="*60)
    print("Test: User Profile Convergence")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        profile = UserProfile("converging_user", tmpdir)

        # Simulate user with consistent high focus and low fatigue
        assert profile.baseline.avg_focus == 0.65  # Default

        histories = [
            [{"focus": 0.9, "fatigue": 0.1, "learning_efficiency": 0.9}] * 3,
            [{"focus": 0.88, "fatigue": 0.12, "learning_efficiency": 0.88}] * 3,
            [{"focus": 0.85, "fatigue": 0.15, "learning_efficiency": 0.85}] * 3
        ]

        for history in histories:
            profile.update_baseline_from_history(history)
            print(f"  Update: focus={profile.baseline.avg_focus:.2f}, fatigue={profile.baseline.avg_fatigue:.2f}")

        # Final focus should be higher than default
        assert profile.baseline.avg_focus > 0.7
        assert profile.baseline.avg_fatigue < 0.3
        print("[OK] Profile converged to actual user characteristics")

    print("[PASS] Profile convergence test PASSED\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PII v1.0 Phase 3 — User Cognitive Model Test Suite")
    print("="*60)

    test_user_profile_creation()
    test_baseline_update()
    test_strategy_registration()
    test_complexity_difficulty_tracking()
    test_personalized_difficulty_adjustment()
    test_personalization_engine_integration()
    test_personalization_with_adaptive_loop()
    test_user_profile_convergence()

    print("="*60)
    print("All Phase 3 Personalization Tests PASSED!")
    print("User Cognitive Model Operational")
    print("="*60)
