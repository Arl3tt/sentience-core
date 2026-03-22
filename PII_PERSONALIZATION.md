# PII v1.0 Phase 3 — User Cognitive Model

## Overview

**Phase 3** implements personalization: building a unique cognitive profile of each user and adapting system behavior to that user's patterns.

### What It Builds

Your AI system now learns **about YOU**:
- ✅ Your typical focus levels
- ✅ How quickly you fatigue
- ✅ Which task complexities you excel at
- ✅ Which strategies work best for YOU
- ✅ Your optimal learning pace
- ✅ When you're most vulnerable to cognitive overload

### Architecture

```
Phase 3: User Cognitive Model
├── UserProfile (core/personalization/user_profile.py)
│   ├── CognitiveBaseline
│   │   ├── avg_focus, avg_fatigue, avg_learning_efficiency
│   │   ├── optimal_complexity_range
│   │   └── fatigue_threshold
│   └── LearningProfile
│       ├── total_tasks_completed, total_cycles
│       ├── preferred_strategies {strategy → success_rate}
│       ├── strong_complexity_levels, difficult_complexity_levels
│       └── learning_curve_steepness
│
├── UserLearningAnalytics (core/personalization/user_analytics.py)
│   ├── compute_improvement_trajectory() → learning speed
│   ├── compute_complexity_preference() → easy/hard levels
│   ├── compute_fatigue_pattern() → fatigue characteristics
│   ├── compute_strategy_effectiveness() → which strategies work
│   └── compute_learning_rate() → how quickly user learns
│
└── PersonalizationEngine (core/personalization/personalization_engine.py)
    ├── recommend_difficulty() → Personalized difficulty adjustment
    ├── recommend_strategy() → Strategy that works for THIS user
    ├── predict_fatigue_risk() → When user will hit overload
    ├── should_reduce_difficulty() → Auto-reduce for user safety
    ├── should_increase_difficulty() → Push learning boundaries
    └── register_task_outcome() → Update profile after each task
```

## Key Components

### 1. UserProfile (`user_profile.py`)

Persistent user model with two parts:

**CognitiveBaseline**
- User's typical cognitive characteristics
- Optimal focus range (e.g., user performs best at 0.75-0.95 focus)
- Optimal complexity range (e.g., user excels at 0.4-0.8 complexity)
- Fatigue threshold specific to THIS user

**LearningProfile**
- Strategy preferences {strategy_name → success_rate}
- Complexity levels where user is strong vs. struggles
- Learning curve steepness (fast vs. slow learner)
- Pattern recognition strength

**Methods**
```python
profile = UserProfile("user_001")
profile.register_strategy_success("conservative", 0.85)
profile.register_complexity_difficulty(0.8, succeeded=False)
profile.register_task_completion(0.6, cycles=5, improvement_rate=0.05)
adjustment = profile.get_personalized_difficulty_adjustment(1.0, current_state)
```

### 2. UserLearningAnalytics (`user_analytics.py`)

Extracts patterns from episodic memory (what user has done):

**Key Analyses**
- `compute_improvement_trajectory()` — How fast does user learn?
- `compute_complexity_preference()` — Which difficulty levels work best?
- `compute_fatigue_pattern()` — How does fatigue accumulate?
- `compute_strategy_effectiveness()` — Which strategies work for THIS user?
- `compute_learning_rate()` — How consistent is learning across tasks?

**Example**: If user tends to succeed at complexity 0.6 but fail at 0.9, analytics discovers this pattern and personalizes accordingly.

### 3. PersonalizationEngine (`personalization_engine.py`)

Main coordinator: combines profile + analytics + memory to make personalized decisions.

**Key Methods**

```python
engine = PersonalizationEngine("user_001", memory_manager)

# Before task: Get personalized difficulty
rec = engine.recommend_difficulty(state, base_difficulty=1.0)
# → {"adjusted_difficulty": 0.85, "rationale": "fatigue_elevated"}

# Recommend strategy that has worked for THIS user
strat = engine.recommend_strategy(state)
# → {"recommended_strategy": "conservative", "confidence": 0.85}

# Predict if user will hit fatigue overload
risk = engine.predict_fatigue_risk(state, num_cycles=5)
# → {"risk_level": "medium", "recommendation": "Monitor fatigue..."}

# Auto-reduce difficulty if user struggling
if engine.should_reduce_difficulty(state):
    difficulty *= 0.9

# Push learning boundaries if user performing well
if engine.should_increase_difficulty(state):
    difficulty *= 1.05

# After task: Update user profile
engine.register_task_outcome(state, report)
```

## Integration with Adaptive Loop

### Before Each Cycle

1. Get personalized difficulty recommendation
2. Get strategy recommendation for this user
3. Predict fatigue risk

```python
engine = PersonalizationEngine("user_001", memory)

# Before cycle
diff_rec = engine.recommend_difficulty(state, 1.0)
state["strategy"]["difficulty_modifier"] = diff_rec["adjusted_difficulty"]

strat_rec = engine.recommend_strategy(state)
state["strategy"]["approach"] = strat_rec["recommended_strategy"]
```

### After Each Cycle

1. Register outcome to update user profile
2. Track strategy success for this user
3. Refine complexity preference

```python
engine.register_task_outcome(state, report)
# Now profile has learned from this task
```

## How It Works

### Personalization Flow

```
Task Execution
    ↓
[PersonalizationEngine] consults:
  - UserProfile (baseline + history)
  - UserLearningAnalytics (computed patterns)
  - MemoryManager (what worked before)
    ↓
Returns:
  - Personalized difficulty adjustment
  - Recommended strategy for THIS user
  - Fatigue risk prediction
    ↓
[Adaptive Loop] uses recommendations
    ↓
Task completes
    ↓
[PersonalizationEngine.register_task_outcome()]
Updates UserProfile for next task
```

### Learning from User Behavior

**Example Scenario:**

1. User completes 10 tasks with complexity 0.6 → avg success 0.85
2. User attempts 5 tasks with complexity 0.8 → avg success 0.40
3. Analytics discovers: User excels at 0.6, struggles at 0.8
4. Next task at 0.8: System automatically reduces difficulty

Result: Personalization prevents user frustration and optimizes learning.

## Cognitive Personality Traits

Each user develops unique characteristics:

| Trait | Description | Impact |
|-------|-----------|--------|
| Learning Speed | How fast user improves | Adjust complexity increment |
| Strategy Preference | What approach works best | Auto-select best strategy |
| Fatigue Sensitivity | How much fatigue builds | Auto-reduce difficulty earlier |
| Focus Stability | How consistent is focus | Predict when breaks needed |
| Complexity Sweet Spot | Optimal difficulty level | Personalize task generation |

## Use Cases

### 1. Personalized Difficulty Selection
```python
# Generic system: difficulty = 0.6
# Personalized system for THIS user: difficulty = 0.85
# Result: Optimal learning for individual user
```

### 2. Strategy Recommendation
```python
# Generic: "Try conservative approach"
# Personalized: "You succeed 92% with aggressive approach, only 60% with conservative"
# Result: User gets strategy that actually works for THEM
```

### 3. Fatigue Prevention
```python
# Generic: "Fatigue > 0.75, reduce difficulty"
# Personalized: "You typically fatigue fast, reduce at > 0.65"
# Result: Prevents burnout for sensitive users
```

### 4. Learning Path Optimization
```python
# Generic: complexity 0.5 → 0.6 → 0.7 → 0.8
# Personalized: complexity following user's actual learning curve
# Result: User-appropriate progression
```

## Files Created

- `core/personalization/user_profile.py` — Persistent user model (CognitiveBaseline + LearningProfile)
- `core/personalization/user_analytics.py` — Pattern extraction from history
- `core/personalization/personalization_engine.py` — Main coordinator
- `core/personalization/__init__.py` — Exports
- `tests/test_phase3_personalization.py` — 8 test cases validating personalization

## Tests Included

```
✅ test_user_profile_creation() — Profile initialization & persistence
✅ test_baseline_update() — Baseline converges to actual user characteristics
✅ test_strategy_registration() — Strategy success tracking
✅ test_complexity_difficulty_tracking() — Map easy/hard complexity levels
✅ test_personalized_difficulty_adjustment() — Difficulty adapts to user state
✅ test_personalization_engine_integration() — Engine with MemoryManager
✅ test_personalization_with_adaptive_loop() — Full integration test
✅ test_user_profile_convergence() — Profile converges over time
```

## Building Towards BCI

This layer is foundational for Brain-Computer Interface:

1. **User Profile** ← Neural baseline ("What does THIS brain look like?")
2. **Learning Analytics** ← Neural learning patterns ("How does THIS brain learn?")
3. **Personalization Engine** ← Neural adaptation ("How to optimize for THIS brain?")
4. **→ Future: BCI Integration** ("Direct neural interface to personalized AI")

The user cognitive model becomes the reference frame for direct brain measurement.

## Next Steps (Phase 4-6)

After Phase 3 (Personalization), recommended paths:

### Product Path
- **Phase 4**: Dashboard & Visualization
  - Real-time cognition visualization
  - Learning progress display
  - Strategy effectiveness charts
  - User profile overview

### Neuro-AI Path (BCI Prep)
- **Phase 4**: Neural Baseline Calibration
  - Connect to BCI hardware
  - Calibrate cognitive metrics to neural signals
  - Build user neural profile

### Research Path
- **Phase 4**: Cognitive Twin
  - Full neural simulation of user
  - Predictive cognitive modeling
  - "Simulate user's next move"

---

**Phase 3 Status**: ✅ COMPLETE
- 3 core modules (profile, analytics, engine)
- 8 comprehensive tests
- Full memory integration
- Production-grade personalization system
- Foundation for BCI integration
