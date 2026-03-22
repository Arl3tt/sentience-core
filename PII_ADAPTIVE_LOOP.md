"""
PII v1.0 L3 — Adaptive Learning Loop Documentation
Full STATE → ACTION → RESULT → SCORE → UPDATE cycle orchestration.
"""

# PII v1.0 L3 — Adaptive Learning Loop Implementation Guide

## 🔄 What is L3?

**L3 orchestrates the complete adaptive learning cycle.**

It ties together L1 (Intelligence Kernel) and L2 (Cognitive Engine) into a unified workflow that continuously improves.

```
┌─────────────────────────────────────────────────────────┐
│  L3: Adaptive Learning Loop                             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  STATE (current system_state)                           │
│     ↓                                                    │
│  ACTION (agent.run)                                     │
│     ↓                                                    │
│  RESULT (output from agent)                             │
│     ↓                                                    │
│  SCORE (agent.evaluate)                                 │
│     ↓                                                    │
│  UPDATE (agent.learn)                                   │
│     ↓                                                    │
│  STATE' (refreshed state)                               │
│                                                          │
│  [REPEAT]                                               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 The 5-Phase Cycle

### Phase 1: STATE
**Read current state** — cognitive state, strategy, history

```python
state = {
    "task": {...},
    "cognitive_state": {"focus": 0.5, "fatigue": 0.1, ...},
    "strategy": {"difficulty_modifier": 1.0},
    "history": [...],
    ...
}
```

### Phase 2: ACTION
**Agent executes** via `run(state)`

```python
state, output = agent.run(state)
# Agent produces output based on current state
# Agent logs action to history
```

### Phase 3: RESULT
**Examine output** from agent

```python
output = {
    "steps": [...],
    "adjusted_complexity": 0.7,
    "plan": {...}
}
```

### Phase 4: SCORE
**Evaluate quality** via `evaluate(state, output)`

```python
feedback = agent.evaluate(state, output)
# Returns: {success_score, efficiency_score, cognitive_load, errors}
```

### Phase 5: UPDATE
**Learn from feedback** via `learn(state, feedback)`

```python
state = agent.learn(state, feedback)
# Agent adapts strategy based on feedback
# STATE is now refreshed for next cycle
```

---

## 🚀 Using L3: The AdaptiveLoop Class

### Single Cycle

```python
from core.system_state import initialize_system_state
from core.agents.pii_planner_agent import PlannerAgent
from core.adaptive_loop import AdaptiveLoop

state = initialize_system_state()
state["task"]["description"] = "Your task"

loop = AdaptiveLoop(verbose=True)
planner = PlannerAgent()

# Execute one complete cycle
state, report = loop.execute_cycle(state, planner)

print(f"Success: {report['feedback']['success_score']:.2f}")
print(f"Efficiency: {report['feedback']['efficiency_score']:.2f}")
print(f"New modifier: {report['strategy_modifier']:.2f}")
```

### Multiple Cycles

```python
# Run 5 cycles with the same agent
loop = AdaptiveLoop(max_cycles=100)  # Stop if reaches 100 cycles
reports = []
for i in range(5):
    state, report = loop.execute_cycle(state, planner)
    reports.append(report)

# Get learning summary
summary = loop.get_learning_summary(reports)
print(f"Avg success: {summary['avg_success']:.2f}")
print(f"Success trend: {summary['success_trend']:+.3f}")
print(f"Peak cycle: {summary['peak_cycle']}")
```

### Multi-Agent Round-Robin

```python
from core.agents.pii_planner_agent import PlannerAgent
from core.agents.my_researcher_agent import ResearcherAgent
from core.agents.my_executor_agent import ExecutorAgent

agents = [PlannerAgent(), ResearcherAgent(), ExecutorAgent()]

# Cycle agents in order: Planner → Researcher → Executor → Planner → ...
state, reports = loop.execute_multi_cycle(
    state, agents, num_cycles=3, round_robin=True
)

# Reports will have 9 entries (3 cycles × 3 agents)
print(f"Total reports: {len(reports)}")  # 9
```

---

## 📊 Understanding Cycle Reports

Each cycle returns a report:

```python
report = {
    "cycle": 1,                     # Cycle number
    "agent": "Planner",             # Agent name
    "feedback": {                   # Evaluation feedback
        "success_score": 0.75,
        "efficiency_score": 0.8,
        "cognitive_load": 0.4,
        "errors": []
    },
    "output": {...},                # Agent output
    "strategy_modifier": 1.1,       # Updated difficulty modifier
    "cognitive_state": {            # Fresh L2 cognition
        "focus": 0.82,
        "fatigue": 0.1,
        "cognitive_load": 0.38,
        "learning_efficiency": 0.71
    },
    "history_length": 5             # Total history entries
}
```

---

## 📈 Learning Summary

Summarize multiple cycles:

```python
summary = loop.get_learning_summary(reports)

# Returns:
{
    "total_cycles": 5,
    "avg_success": 0.72,            # Average success across all cycles
    "avg_efficiency": 0.68,         # Average efficiency
    "success_trend": 0.15,          # Last success - First success
    "strategy_evolution": 0.2,      # How much strategy changed
    "max_success": 0.95,            # Best cycle
    "min_success": 0.45,            # Worst cycle
    "peak_cycle": 3                 # Which cycle was best
}
```

**Interpreting Trends:**
- `success_trend > 0`: System is improving ✓
- `success_trend < 0`: System is degrading ✗
- `avg_success > 0.8`: Consistently performing well ✓
- `strategy_evolution > 0`: Learning is adapting ✓

---

## 🎯 Continuation Rules

L3 automatically decides whether to continue or stop:

```python
should_continue = loop.should_continue(state, feedback, current_cycle)
```

**Stops if:**
- Success score > 0.95 (excellent performance achieved)
- Cognitive load > 0.9 (system overwhelmed, needs rest)
- Cycle count reaches max_cycles (iteration limit)

**Continues if:**
- None of the above are true

### Custom Continuation Logic

Override `should_continue()`:

```python
class CustomLoop(AdaptiveLoop):
    def should_continue(self, state, feedback, cycle):
        # Stop if error rate is too high
        if len(feedback["errors"]) > 5:
            return False

        # Stop if learning efficiency drops below threshold
        if state["cognitive_state"]["learning_efficiency"] < 0.2:
            return False

        # Otherwise use default rules
        return super().should_continue(state, feedback, cycle)
```

---

## 🔄 Full Example: Adaptive Task Solving

```python
from core.system_state import initialize_system_state
from core.agents.pii_planner_agent import PlannerAgent
from core.adaptive_loop import AdaptiveLoop

# Initialize
state = initialize_system_state()
state["task"]["description"] = "Train a machine learning model"
state["task"]["complexity"] = 0.8
state["task"]["id"] = "ml_training_001"

# Create loop
loop = AdaptiveLoop(max_cycles=50, verbose=True)
planner = PlannerAgent()

print("Starting adaptive task solving...")
print(f"Task: {state['task']['description']}")
print(f"Complexity: {state['task']['complexity']}")

# Main loop
cycle = 0
all_reports = []

while cycle < 10:
    # Execute one cycle
    state, report = loop.execute_cycle(state, planner, update_cognition=True)
    all_reports.append(report)

    # Check if we should continue
    feedback = report["feedback"]
    if not loop.should_continue(state, feedback, cycle):
        print(f"\n✓ Stopping at cycle {cycle + 1}")
        break

    # Optional: custom stopping criteria
    if report["strategy_modifier"] > 2.0:
        print(f"\n✓ Strategy maxed out at {report['strategy_modifier']:.2f}")
        break

    cycle += 1

# Analyze results
print("\n" + "="*60)
print("FINAL RESULTS")
print("="*60)

summary = loop.get_learning_summary(all_reports)
print(f"Cycles completed: {summary['total_cycles']}")
print(f"Average success: {summary['avg_success']:.2f}")
print(f"Success trend: {summary['success_trend']:+.3f}")
print(f"Peak performance: Cycle {summary['peak_cycle']} ({summary['max_success']:.2f})")
print(f"Final strategy modifier: {all_reports[-1]['strategy_modifier']:.2f}")

# Cognitive evolution
first = all_reports[0]["cognitive_state"]
last = all_reports[-1]["cognitive_state"]
print(f"\nCognitive Evolution:")
print(f"  Focus: {first['focus']:.2f} → {last['focus']:.2f}")
print(f"  Fatigue: {first['fatigue']:.2f} → {last['fatigue']:.2f}")
print(f"  Load: {first['cognitive_load']:.2f} → {last['cognitive_load']:.2f}")

# Output:
# Cycles completed: 5
# Average success: 0.74
# Success trend: +0.156  (improving!)
# Peak performance: Cycle 3 (0.82)
# Final strategy modifier: 1.21
#
# Cognitive Evolution:
#   Focus: 0.50 → 0.76
#   Fatigue: 0.00 → 0.12
#   Load: 0.40 → 0.38
```

---

## 🧪 Test Coverage

L3 includes 7 comprehensive tests:

```
✅ test_single_cycle
✅ test_multi_cycle_sequential
✅ test_multi_agent_round_robin
✅ test_learning_summary
✅ test_continuation_rules
✅ test_full_adaptive_workflow
✅ test_cycle_isolation
```

Run tests:
```bash
python -m pytest tests/test_l3_adaptive_loop.py -v
```

---

## 📁 L3 File Structure

```
core/
├─ adaptive_loop.py             # Main L3 orchestrator

tests/
└─ test_l3_adaptive_loop.py     # 7 tests (all passing ✅)
```

---

## 🔗 L1 → L2 → L3 Integration

```
L1 (Intelligence Kernel)
├─ BaseAgent, PlannerAgent
├─ run(), evaluate(), learn()
└─ Produce: history, feedback, adaptation

    ↓ (L3 calls)

L3 (Adaptive Loop)
├─ execute_cycle()
├─ execute_multi_cycle()
└─ Orchestrate: STATE → ACTION → RESULT → SCORE → UPDATE

    ↕ (L3 coordinates)

L2 (Cognitive Engine)
├─ update_cognitive_state()
├─ Dynamic focus, fatigue, load, learning
└─ Produce: Fresh cognition metrics

    ↓ (L2 outputs feed L1)

L1 reads updated cognitive_state
└─ Next cycle uses fresh cognition
```

---

## ⚙️ Architecture Layers (Full Stack)

```
┌─────────────────────────────────────────────────────────┐
│ L4: Platform Layer                                      │
│ (FastAPI, Web Dashboard, Voice Interface)              │
│ [Will call L3 orchestrator]                            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ L3: Adaptive Learning Loop ✅ COMPLETE                 │
│ Orchestrates: STATE → ACTION → RESULT → SCORE → UPDATE│
│ Multi-cycle coordination, learning summaries            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ L2: Cognitive Engine ✅ COMPLETE                        │
│ Dynamic: focus, fatigue, load, learning_efficiency    │
│ Updates state["cognitive_state"] in real-time          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ L1: Intelligence Kernel ✅ COMPLETE                     │
│ BaseAgent: run() → evaluate() → learn()                │
│ SystemState: shared hub for all agents                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Building Your Own Agents with L3

Every agent you build automatically works with L3:

```python
from core.base_agent import BaseAgent
from core.types import SystemState, Feedback

class YourCustomAgent(BaseAgent):
    def run(self, state: SystemState):
        # Your logic
        state["history"].append({...})
        return state, output

    def evaluate(self, state, output) -> Feedback:
        return {...}  # Any Feedback object

    def learn(self, state, feedback):
        return state

# L3 automatically cycles it
loop = AdaptiveLoop()
agent = YourCustomAgent()
state, report = loop.execute_cycle(state, agent)  # ✓ Works!
```

---

## 📚 Next: L4 — Platform Layer Integration

L4 will expose L3 to the world via:

- **FastAPI endpoints** to trigger adaptive cycles
- **Web Dashboard** to visualize cycle reports & learning
- **Voice interface** to speak commands to the system
- **Scheduling** to run agents on a timer

L4 will simply call:
```python
loop = AdaptiveLoop()
state, reports = loop.execute_multi_cycle(state, agents, num_cycles=5)
```

And then visualize the results.

---

## 📊 Performance Metrics to Track

After running cycles, analyze:

1. **Success trend**: Is performance improving?
2. **Efficiency**: Are operations becoming faster?
3. **Cognitive health**: Is focus high, fatigue low?
4. **Learning rate**: Is learning_efficiency increasing?
5. **Strategy evolution**: Is difficulty modifier adapting?

```python
summary = loop.get_learning_summary(reports)

# Healthy signs:
assert summary["success_trend"] > 0.1      # ✓ Improving
assert summary["avg_efficiency"] > 0.7     # ✓ Efficient
assert summary["peak_cycle"] > sum/len/2   # ✓ Getting better over time
```

---

## 🎓 Design Principles (L3)

1. **Composable**: Works with any agent inheriting BaseAgent
2. **Observable**: Every cycle produces detailed reports
3. **Adaptive**: Learns when to continue/stop
4. **Coordinated**: L1 + L2 work together seamlessly
5. **Stateful**: History drives learning
6. **Introspectable**: Easy to analyze what happened

---

**Status: L3 — Adaptive Learning Loop ✅ COMPLETE**
**Test Results: 7/7 passing**
**Integration: L1 ↔ L2 ↔ L3 fully operational**
**Next: L4 — Platform Layer**
