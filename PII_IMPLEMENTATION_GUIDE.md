# PII v1.0 — Quick Implementation Guide

## Copy-Paste Template for New Agents

Use this to build new agents in seconds:

```python
"""
[YourAgent Name] — [Brief description]
"""
from typing import Tuple
from core.base_agent import BaseAgent
from core.types import SystemState, Feedback


class YourLowercaseAgent(BaseAgent):
    """
    [Full description of what this agent does]
    Reads from: [list fields it reads]
    Writes to: [list fields it writes]
    """

    def __init__(self):
        super().__init__("YourAgentName")

    def run(self, state: SystemState) -> Tuple[SystemState, dict]:
        """
        Execute the agent's primary function.
        Don't modify state directly—return it updated.
        """
        task = state["task"]
        cognitive = state["cognitive_state"]
        strategy = state["strategy"]

        # Your logic here
        result = {
            "key": "value"
        }

        # Always log to history
        state["history"].append({
            "agent": self.name,
            "action": "action_name",
            "result": result
        })

        return state, result

    def evaluate(self, state: SystemState, output: dict) -> Feedback:
        """
        Score your output on success (0.0–1.0).
        Return standardized Feedback.
        """
        success = 0.8  # Your scoring logic
        efficiency = 0.7
        errors = []

        return {
            "success_score": max(0.0, min(1.0, success)),
            "efficiency_score": max(0.0, min(1.0, efficiency)),
            "cognitive_load": state["cognitive_state"]["cognitive_load"],
            "errors": errors
        }

    def learn(self, state: SystemState, feedback: Feedback) -> SystemState:
        """
        Adapt strategy based on feedback.
        This is where the system learns.
        """
        if feedback["success_score"] > 0.8:
            state["strategy"]["difficulty_modifier"] *= 1.1
        elif feedback["success_score"] < 0.5:
            state["strategy"]["difficulty_modifier"] *= 0.9

        return state
```

---

## Checklist: Before Committing a New Agent

- [ ] Inherits from `BaseAgent`
- [ ] Implements `run()`, `evaluate()`, `learn()`
- [ ] All metrics are floats between 0.0–1.0
- [ ] Returns `(SystemState, dict)` from run()
- [ ] Returns `Feedback` from evaluate()
- [ ] Logs to `state["history"]` in run()
- [ ] Has a test case (use `test_pii_foundation.py` template)
- [ ] Type hints on all functions
- [ ] No placeholder logic (if, else, mocks are OK for now)

---

## Common Patterns

### Pattern 1: Read from history

```python
last_action = state["history"][-1] if state["history"] else None
recent_actions = [a for a in state["history"] if a["agent"] == "Researcher"]
```

### Pattern 2: Update cognitive state

```python
# DON'T DO THIS - cognitive_state is read-only in L1
# state["cognitive_state"]["focus"] = 0.9

# DO THIS - let L2 handle it
# (L2 will compute it dynamically based on history)
```

### Pattern 3: Validate output

```python
def evaluate(self, state: SystemState, output: dict) -> Feedback:
    success = 1.0
    errors = []

    if not output.get("key"):
        success = 0.0
        errors.append("Missing required key")

    return {
        "success_score": success,
        "efficiency_score": 0.5,
        "cognitive_load": state["cognitive_state"]["cognitive_load"],
        "errors": errors
    }
```

### Pattern 4: Adaptive learning

```python
def learn(self, state: SystemState, feedback: Feedback) -> SystemState:
    current = state["strategy"]["difficulty_modifier"]

    # Stress-reduce
    if feedback["cognitive_load"] > 0.75:
        state["strategy"]["difficulty_modifier"] = current * 0.85

    # Success-reward
    elif feedback["success_score"] > 0.9:
        state["strategy"]["difficulty_modifier"] = current * 1.15

    # Bound it
    state["strategy"]["difficulty_modifier"] = max(0.5,
        min(2.0, state["strategy"]["difficulty_modifier"]))

    return state
```

---

## Debugging Tips

### Check state composition

```python
print(state.keys())  # Should have: task, user_state, cognitive_state, history, strategy
print(state["cognitive_state"].keys())  # focus, fatigue, cognitive_load, learning_efficiency
```

### Verify feedback

```python
feedback = agent.evaluate(state, output)
for key, val in feedback.items():
    if isinstance(val, float):
        assert 0.0 <= val <= 1.0, f"{key} out of bounds: {val}"
```

### Trace history

```python
for i, entry in enumerate(state["history"]):
    print(f"{i}: {entry['agent']} → {entry['action']}")
```

---

## Running Tests

```bash
# All foundation tests
python -m pytest tests/test_pii_foundation.py -v

# Single test
python -m pytest tests/test_pii_foundation.py::test_planner_cognitive_loop -v

# With output
python -m pytest tests/test_pii_foundation.py -v -s
```

---

## Type Checking

```bash
# Install mypy
pip install mypy

# Check types
mypy core/base_agent.py --strict
mypy core/agents/pii_planner_agent.py --strict
```

---

## Next Layer Preview: L2 — Cognitive Engine

When you build L2, you'll add:

```python
# cognition/attention.py
def compute_attention(state: SystemState) -> float:
    """Based on recent success rate and task focus"""
    pass

# cognition/fatigue.py
def compute_fatigue(state: SystemState) -> float:
    """Based on history length and frequency of actions"""
    pass

# cognition/load.py
def compute_cognitive_load(state: SystemState) -> float:
    """Based on task complexity and current capacity"""
    pass

# cognition/learning.py
def compute_learning_efficiency(state: SystemState) -> float:
    """Based on feedback trend over time"""
    pass
```

These will **update** `state["cognitive_state"]` which L1 agents read!

---

## FAQ

**Q: Can I modify cognitive_state in learn()?**
A: No. L1 agents read it, L2 computes it. In learn(), only modify strategy.

**Q: How do I access previous agent outputs?**
A: Through state["history"]. Each entry is `{"agent": name, "action": action, ...}`.

**Q: Should I validate user input in run() or evaluate()?**
A: run() executes, evaluate() scores. Keep them separate.

**Q: What if feedback["success_score"] is exactly 0.8?**
A: Use `>=` in learn() logic. The boundary is intentional.

**Q: Can I have multiple agents running in parallel?**
A: For L1, think sequentially. L3 will handle async orchestration.

**Q: Where's the memory system integration?**
A: L2 (Cognitive Engine) will plug into core/memory. For now, history is your log.

---

## Resources

- Full Architecture: `PII_ARCHITECTURE.md`
- Test Examples: `tests/test_pii_foundation.py`
- Type Contracts: `core/types.py`
- Base Class: `core/base_agent.py`

---

Last Updated: 2026-03-22
Status: **Foundation Complete — L2 Ready to Build**
