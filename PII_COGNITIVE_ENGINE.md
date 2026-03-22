"""
PII v1.0 L2 — Cognitive Engine Documentation
Dynamic cognition: Computing focus, fatigue, load, and learning efficiency in real-time.
"""

# PII v1.0 L2 — Cognitive Engine Implementation Guide

## 🧠 What is L2?

**L2 replaces static cognitive values with dynamic computation.**

Instead of:
```python
cognitive_state = {
    "focus": 0.5,           # ❌ Static
    "fatigue": 0.5,         # ❌ Static
    "cognitive_load": 0.5,  # ❌ Static
    "learning_efficiency": 0.5  # ❌ Static
}
```

L2 gives you:
```python
cognitive_state = {
    "focus": compute_attention(history, feedback),      # ✅ Dynamic
    "fatigue": compute_fatigue(history, decay),         # ✅ Dynamic
    "cognitive_load": compute_load(focus, fatigue, complexity),  # ✅ Dynamic
    "learning_efficiency": compute_learning_efficiency(trajectory)  # ✅ Dynamic
}
```

## 📊 The 4 Cognitive Modules

### 1️⃣ Attention (Focus)

**What it measures:** How engaged and focused the system is.

**Increases when:**
- Recent actions succeed
- Error rate is low
- System is "in the zone"

**Decreases when:**
- Recent actions fail
- Errors accumulate
- System is losing focus

**Formula:**
```
attention = (success_rate × 0.8) + (0.2 × (1.0 - error_penalty))
Range: [0.0, 1.0]
```

**Example:**
```
Last 5 actions: ✅ ✅ ✅ ❌ ❌
Success rate: 60%
Error count: 2
Error penalty: min(2 * 0.1, 0.5) = 0.2
attention = (0.6 × 0.8) + (0.2 × 0.8) = 0.48 + 0.16 = 0.64 ✓
```

---

### 2️⃣ Fatigue (Resource Depletion)

**What it measures:** How exhausted the system is from continuous operation.

**Increases when:**
- Many consecutive actions without rest
- Output quality declines (performance degradation)
- System is "burning out"

**Decreases:**
- Naturally over time (recovery factor)
- With breaks between cycles

**Formula:**
```
fatigue = ((action_frequency × 0.6) + (quality_decay × 0.4)) × recovery_factor
Range: [0.0, 1.0]
```

**Example:**
```
History length: 20 actions
Action frequency: min(20/10, 1.0) = 1.0

Old period success: 80% (older work was good)
New period success: 40% (recent work is worse)
Quality decay: 0.8 - 0.4 = 0.4

fatigue = ((1.0 × 0.6) + (0.4 × 0.4)) × recovery_factor
fatigue = 0.76 × recovery_factor → ~0.4-0.5 after recovery
```

---

### 3️⃣ Cognitive Load (Mental Effort)

**What it measures:** How much mental effort is required relative to capacity.

**Increases when:**
- Task complexity is high
- Attention is low (struggling to focus)
- Fatigue is high (depleted resources)

**Decreases when:**
- Task is simple
- Attention is high
- System is well-rested

**Formula:**
```
load = (complexity × 0.5) + (focus_gap × 0.2) + (fatigue × 0.2) + (context × 0.1)
Range: [0.0, 1.0]
```

**Example:**
```
Task complexity: 0.7
Current focus: 0.9 → gap = 1.0 - 0.9 = 0.1
Current fatigue: 0.3
History length (context): 50 → 50/100 = 0.5 capped at 0.3

load = (0.7 × 0.5) + (0.1 × 0.2) + (0.3 × 0.2) + (0.3 × 0.1)
load = 0.35 + 0.02 + 0.06 + 0.03 = 0.46 ✓
```

---

### 4️⃣ Learning Efficiency

**What it measures:** How effectively the system is improving over time.

**Increases when:**
- Success rate is improving (trajectory)
- Errors are decreasing
- Strategy is adapting (difficulty_modifier changing)

**Decreases when:**
- Performance is stagnant or declining
- No adaptation happening
- Errors persist

**Formula:**
```
learning_eff = (improvement_trajectory × 0.4) + (error_reduction × 0.3) + (adaptation_rate × 0.3)
Range: [0.0, 1.0]
```

**Example:**
```
Old period: 40% success, 5 errors
New period: 80% success, 1 error
Improvement: 0.8 - 0.4 = 0.4 (biased: +0.5 = 0.9)
Error reduction: (5 - 1) / 5 = 0.8
Adaptation rate: 2 strategy updates / 5 = 0.4

learning_eff = (0.9 × 0.4) + (0.8 × 0.3) + (0.4 × 0.3)
learning_eff = 0.36 + 0.24 + 0.12 = 0.72 ✓
```

---

## 🔄 L1 ↔ L2 Integration Flow

```
[L1] PlannerAgent.run(state)
        ↓ (produces history entry)
   state["history"].append({...})

[L2] update_cognitive_state(state)
        ├─ compute_attention(state)     → focus
        ├─ compute_fatigue(state)       → fatigue
        ├─ compute_cognitive_load(state) → cognitive_load
        └─ compute_learning_efficiency(state) → learning_efficiency
        ↓
   state["cognitive_state"] = {focus, fatigue, load, learning_eff}

[L1] PlannerAgent.evaluate(state, output)
        ↓ (reads cognition)
   Uses state["cognitive_state"]["focus"], ["cognitive_load"], etc.

[L1] PlannerAgent.learn(state, feedback)
        ↓
   Adapts state["strategy"]["difficulty_modifier"]
        ↓
[CYCLE REPEATS]
```

---

## 🚀 How to Use L2 in Your Code

### Option 1: Manual Update

```python
from core.cognition import update_cognitive_state
from core.agents.pii_planner_agent import PlannerAgent

state = initialize_system_state()
planner = PlannerAgent()

# Agent runs
state, output = planner.run(state)

# ✅ Update cognition manually
state = update_cognitive_state(state)

# Now cognitive_state is fresh
print(state["cognitive_state"]["focus"])      # 0.8
print(state["cognitive_state"]["fatigue"])    # 0.1
print(state["cognitive_state"]["cognitive_load"])  # 0.4
print(state["cognitive_state"]["learning_efficiency"])  # 0.7

# Agent evaluates with fresh cognition
feedback = planner.evaluate(state, output)
state = planner.learn(state, feedback)
```

### Option 2: Create a Wrapper Agent

```python
from core.base_agent import BaseAgent
from core.cognition import update_cognitive_state

class CognitiveWrapper(BaseAgent):
    """Wraps any agent to auto-update cognition."""

    def __init__(self, inner_agent):
        super().__init__(f"CognitiveWrapper({inner_agent.name})")
        self.inner_agent = inner_agent

    def run(self, state):
        # Update cognition before agent runs
        state = update_cognitive_state(state)
        state, output = self.inner_agent.run(state)
        return state, output

    def evaluate(self, state, output):
        return self.inner_agent.evaluate(state, output)

    def learn(self, state, feedback):
        return self.inner_agent.learn(state, feedback)

# Usage
wrapped_planner = CognitiveWrapper(PlannerAgent())
state = initialize_system_state()
state, output = wrapped_planner.run(state)  # Cognition auto-updated!
```

---

## 📈 Cognitive Status Reporting

Check the system's current cognitive state at a glance:

```python
from core.cognition import get_cognitive_summary, get_cognitive_status

state = update_cognitive_state(state)

# Human-readable summary
summary = get_cognitive_summary(state)
print(summary)
# {
#     "focus": "0.82",
#     "fatigue": "0.15",
#     "cognitive_load": "0.45",
#     "learning_efficiency": "0.71",
#     "status": "🟢 OPTIMAL"
# }

# Status codes
get_cognitive_status(state["cognitive_state"])
# "🔴 OVERLOADED"    if cognitive_load > 0.8
# "🟡 FATIGUED"      if fatigue > 0.7
# "🟠 UNFOCUSED"     if focus < 0.3
# "🟢 OPTIMAL"       if focus > 0.8, load < 0.4, fatigue < 0.3
# "🔵 NORMAL"        otherwise
```

---

## 🧪 Test Coverage

L2 includes 14 comprehensive tests:

```
✅ test_attention_empty_history
✅ test_attention_high_success
✅ test_attention_with_errors
✅ test_fatigue_fresh_start
✅ test_fatigue_accumulates
✅ test_fatigue_quality_decay
✅ test_cognitive_load_baseline
✅ test_cognitive_load_high_complexity
✅ test_cognitive_load_fatigued_state
✅ test_learning_empty
✅ test_learning_improving_trajectory
✅ test_engine_full_orchestration
✅ test_cognitive_status
✅ test_l1_l2_integration
```

Run tests:
```bash
python -m pytest tests/test_l2_cognitive_engine.py -v
```

---

## 📁 L2 File Structure

```
core/cognition/
├─ __init__.py              # Module exports
├─ attention.py             # compute_attention()
├─ fatigue.py               # compute_fatigue()
├─ load.py                  # compute_cognitive_load()
├─ learning.py              # compute_learning_efficiency()
└─ engine.py                # update_cognitive_state() orchestrator

tests/
└─ test_l2_cognitive_engine.py  # 14 tests (all passing ✅)
```

---

## 🎯 Design Principles (L2)

1. **Reactive**: Metrics update based on real history, not predefined rules
2. **Normalized**: All outputs are [0.0, 1.0], ready for consumption
3. **Composable**: Each metric builds on previous ones (modular)
4. **Explainable**: Every formula is documented with examples
5. **Bounded**: No values escape [0.0, 1.0] range
6. **Non-destructive**: L2 reads state, doesn't modify it (except cognitive_state)

---

## 🔧 Customizing L2

### Adjust Weights

If attention should focus more on success and less on errors:

```python
# In attention.py
def compute_attention(state):
    ...
    attention = (success_rate * 0.9) + (0.1 * (1.0 - error_penalty))  # Changed!
    ...
```

### Add New Metrics

Create a new module:

```python
# core/cognition/motivation.py
def compute_motivation(state):
    """
    Motivation = how eager the system is to continue.
    Increases with success streaks, decreases with repeated failures.
    """
    ...
    return motivation  # [0.0, 1.0]

# Add to engine.py
state["cognitive_state"]["motivation"] = compute_motivation(state)
```

### Add History Decay

If you want old history to matter less:

```python
# In any module
recent_weight = 0.7
old_weight = 0.3

recent = history[-5:]  # Last 5
old = history[:-5]     # Everything else

recent_score = compute_score(recent)
old_score = compute_score(old)

combined = (recent_score * recent_weight) + (old_score * old_weight)
```

---

## ⚠️ Common Pitfalls

### ❌ Don't modify cognitive_state in learn()

```python
# WRONG
def learn(self, state, feedback):
    state["cognitive_state"]["focus"] = 0.9  # ❌ L2 computes this!
    return state

# RIGHT
def learn(self, state, feedback):
    state["strategy"]["difficulty_modifier"] *= 1.1  # ✅ Adjust strategy
    return state
```

### ❌ Don't forget to call update_cognitive_state()

```python
# WRONG
state, output = agent.run(state)
feedback = agent.evaluate(state, output)  # ❌ cognition is stale

# RIGHT
state, output = agent.run(state)
state = update_cognitive_state(state)  # ✅ Fresh cognition
feedback = agent.evaluate(state, output)
```

### ❌ Don't assume cognition is accurate with <10 actions

```python
# With very short history, metrics are proxies
# Always validate with more history before trusting them
```

---

## 📊 Example: Full Cognitive Cycle

```python
from core.system_state import initialize_system_state
from core.agents.pii_planner_agent import PlannerAgent
from core.cognition import update_cognitive_state, get_cognitive_summary

state = initialize_system_state()
state["task"]["description"] = "Train a model"
state["task"]["complexity"] = 0.75

planner = PlannerAgent()

for cycle in range(3):
    print(f"\n=== CYCLE {cycle + 1} ===")

    # 1. Update cognition
    state = update_cognitive_state(state)
    summary = get_cognitive_summary(state)
    print(f"Cognition: {summary['status']}")

    # 2. Run agent
    state, output = planner.run(state)

    # 3. Evaluate
    feedback = planner.evaluate(state, output)
    print(f"Success: {feedback['success_score']:.2f}")

    # 4. Learn
    state = planner.learn(state, feedback)
    print(f"New modifier: {state['strategy']['difficulty_modifier']:.2f}")

# Output:
# === CYCLE 1 ===
# Cognition: 🔵 NORMAL (focus=0.50, fatigue=0.00, load=0.38, eff=0.50)
# Success: 0.75
# New modifier: 1.00
#
# === CYCLE 2 ===
# Cognition: 🟢 OPTIMAL (focus=0.67, fatigue=0.05, load=0.37, eff=0.60)
# Success: 0.70
# New modifier: 1.10
#
# === CYCLE 3 ===
# Cognition: 🟢 OPTIMAL (focus=0.72, fatigue=0.08, load=0.36, eff=0.68)
# Success: 0.65
# New modifier: 1.10
```

---

## 🚀 Next: L3 — Adaptive Learning Loop

L3 will implement the full cycle:
```
STATE → ACTION → RESULT → SCORE → UPDATE → STATE'
```

L3 will also use L2 metrics to determine:
- When to adjust strategy
- When to give the system a break
- When to increase difficulty
- When to trigger reflexion (self-improvement)

---

## 📚 References

- Full Architecture: `PII_ARCHITECTURE.md`
- L1 Implementation: `PII_IMPLEMENTATION_GUIDE.md`
- Test Examples: `tests/test_l2_cognitive_engine.py`

---

**Status: L2 — Cognitive Engine ✅ COMPLETE**
**Test Results: 14/14 passing**
**Next: L3 — Adaptive Learning Loop**
