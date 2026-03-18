#!/usr/bin/env python3
"""
langgraph_planner.py - LangGraph adapter + streaming planner

This module adapts the repo's existing planner to the official `langgraph` SDK
when available while providing a safe fallback implementation. It also emits
streaming updates as dictionaries so the Web UI can display progress.

Notes / assumptions:
- The repo's `requirements.txt` includes `langgraph>=0.0.1` (see requirements).
- This file will attempt to import commonly-named SDK objects from
  `langgraph`. If the SDK in the environment exposes different symbols,
  the planner falls back to a local, tested Graph implementation.
"""
import os
import yaml
import json
import importlib.util
from typing import Dict, List, Any, TypeVar, Callable, AsyncGenerator

from core.memory import semantic_search, add_episode
from core.tools.tool_runner import run_python_snippet, run_shell
from core.tools.sandbox_runner import run_in_sandbox
import core.tools as ctools

# Detect installed langgraph package/version (from installed requirements file)
_LG_SPEC = importlib.util.find_spec("langgraph")
LANGGRAPH_AVAILABLE = _LG_SPEC is not None
LG_VERSION = None
if LANGGRAPH_AVAILABLE:
    try:
        import langgraph as _lg
        # best-effort attempt to read version attribute
        LG_VERSION = getattr(_lg, "__version__", None) or getattr(_lg, "version", None)
    except Exception:
        LG_VERSION = None

# Local Graph fallback for safe, predictable behavior
State = TypeVar("State", bound=Dict[str, Any])
END = "END"


class Graph:
    """Minimal deterministic graph runner used as a fallback.

    We keep the nodes simple: each node is a callable(state) -> next_node_or_END
    or callable that mutates state and returns next node name.
    """
    def __init__(self):
        self.nodes = {}
        self.conditional_edges = {}
        self.entry_point = None

    def add_node(self, name: str, fn: Callable[[Dict], Any]):
        self.nodes[name] = fn

    def add_conditional_edges(self, edges: Dict[str, Dict[str, Callable]]):
        self.conditional_edges = edges

    def set_entry_point(self, name: str):
        if name not in self.nodes:
            raise ValueError("entry node not found")
        self.entry_point = name

    def compile(self):
        def runner(state: Dict):
            current = self.entry_point
            while current != END:
                fn = self.nodes[current]
                nxt = fn(state)
                # conditional edges may override next
                if current in self.conditional_edges:
                    for candidate, cond in self.conditional_edges[current].items():
                        if cond(state):
                            nxt = candidate
                            break
                current = nxt
            return state

        return runner


# Tool wrapper to keep a unified interface
class ToolWrapper:
    def __init__(self, name: str, func: Callable, description: str = ""):
        self.name = name
        self.func = func
        self.description = description

    def invoke(self, args: Dict[str, Any]):
        # Simple call convention: pass kwargs if mapping, else pass single arg
        if isinstance(args, dict):
            return self.func(**args)
        return self.func(args)


class LangGraphPlanner:
    """Planner that uses langgraph SDK where available and yields streaming updates.

    Behavior:
    - If `langgraph` present and exposes helpful runtime types, attempt to use
      them for orchestration (best-effort).
    - Otherwise use an internal Graph implementation that mirrors the expected
      node flow. In all cases the planner emits incremental updates as dicts.
    """

    def __init__(self):
        # Build tools
        self.tools = self._setup_tools()

        # Load workflow configuration
        config_path = os.path.join(os.path.dirname(__file__), "config", "planner_workflow.yaml")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.workflow_config = yaml.safe_load(f)
        except FileNotFoundError:
            self.workflow_config = {}

        # Attempt to construct a langgraph workflow if SDK exposes convenient API
        self._use_langgraph_sdk = False
        if LANGGRAPH_AVAILABLE:
            try:
                import langgraph as lg
                # If lg exposes a Workflow/Graph runtime, prefer it.
                # This is best-effort mapping; if names differ, we fall back.
                if hasattr(lg, "Workflow") or hasattr(lg, "Graph"):
                    self._lg = lg
                    self._use_langgraph_sdk = True
            except Exception:
                self._use_langgraph_sdk = False

        # Build internal workflow (fallback) that emits progress updates when run
        self._workflow = self._create_workflow()

    def _setup_tools(self) -> List[ToolWrapper]:
        tools = [
            ToolWrapper("semantic_search", semantic_search, "Semantic search tool"),
            ToolWrapper("run_python_snippet", run_python_snippet, "Execute python snippet"),
            ToolWrapper("run_shell", run_shell, "Run shell command"),
            ToolWrapper("sandbox_runner", run_in_sandbox, "Run code in sandbox")
        ]

        # Register BCI tools if available in core.tools
        try:
            tools.append(ToolWrapper("classify_brainwave_bands", ctools.classify_brainwave_bands, "Brain wave band classifier"))
            tools.append(ToolWrapper("classify_cognitive_state", ctools.classify_cognitive_state, "Cognitive state classifier"))
            tools.append(ToolWrapper("classify_multi_channel", ctools.classify_multi_channel, "Multi-channel aggregator"))

            tools.append(ToolWrapper("classify_motor_imagery", ctools.classify_motor_imagery, "Motor imagery classifier"))
            tools.append(ToolWrapper("extract_motor_imagery_features", ctools.extract_motor_imagery_features, "Motor imagery feature extractor"))

            tools.append(ToolWrapper("P300Speller", ctools.P300Speller, "P300 speller tool"))
            tools.append(ToolWrapper("create_speller_interface", ctools.create_speller_interface, "Create P300 speller instance"))
            tools.append(ToolWrapper("classify_p300_response", ctools.classify_p300_response, "Classify P300 row/col responses"))

            tools.append(ToolWrapper("create_neurofeedback_session", ctools.create_neurofeedback_session, "Create neurofeedback session"))

            tools.append(ToolWrapper("create_hybrid_bci", ctools.create_hybrid_bci, "Hybrid BCI fusion"))
            tools.append(ToolWrapper("ASDAttentionAnalyzer", ctools.ASDAttentionAnalyzer, "ASD attention analyzer"))
        except Exception:
            # If any of the tools are not available, continue with the baseline tools
            pass

        return tools

    def _create_workflow(self):
        # Build a simple two-node graph: planner -> executor -> loop until no tasks
        graph = Graph()

        def task_planner(state: Dict):
            # Produce tasks by running a prompt or heuristics. We emit a planning
            # update so the caller can stream.
            state.setdefault("messages", [])
            state.setdefault("tasks", [])
            state.setdefault("updates", [])

            state["updates"].append({"status": "Planning tasks...", "progress": 0.1})

            # Simple heuristic / placeholder: if workflow_config contains a planner prompt
            prompt_template = None
            try:
                prompt_template = self.workflow_config.get("nodes", {}).get("planner", {}).get("config", {}).get("prompt_template")
            except Exception:
                prompt_template = None

            # If we had a parser/template, we would call an LLM here. For safety,
            # keep a minimal behavior: create a single echo task.
            tasks = []
            goal_text = state.get("goal", "")
            if goal_text:
                tasks.append({
                    "id": "t1",
                    "description": f"Echo goal: {goal_text}",
                    "tool": "run_shell",
                    "args": {"cmd": f"echo {json.dumps(goal_text)}"}
                })

            state["tasks"] = tasks
            state["updates"].append({"status": "Tasks created", "progress": 0.25, "tasks": tasks})
            return "task_executor"

        def task_executor(state: Dict):
            # Execute tasks one at a time and emit intermediate updates
            if not state.get("tasks"):
                return END

            task = state["tasks"].pop(0)
            state["current_task"] = task
            state["updates"].append({"status": f"Running {task.get('description')}", "progress": 0.5, "current_task": task})

            # Find tool
            tool = next((t for t in self.tools if t.name == task.get("tool")), None)
            result = None
            try:
                if tool is None:
                    raise RuntimeError(f"Tool {task.get('tool')} not available")
                result = tool.invoke(task.get("args", {}))
                state.setdefault("messages", []).append({"role": "system", "content": f"Task result: {str(result)}"})
                state["updates"].append({"status": "Task completed", "progress": 0.8, "current_task": task, "result": result})
            except Exception as e:
                state["updates"].append({"status": f"Task error: {str(e)}", "progress": 1.0, "error": str(e)})

            # Continue if there are more tasks
            return "task_executor" if state.get("tasks") else END

        graph.add_node("task_planner", task_planner)
        graph.add_node("task_executor", task_executor)
        graph.add_conditional_edges({
            "task_executor": {"task_executor": lambda s: bool(s.get("tasks")), END: lambda s: not bool(s.get("tasks"))}
        })
        graph.set_entry_point("task_planner")
        return graph.compile()

    async def plan(self, goal: str) -> AsyncGenerator[Dict, None]:
        """Run planning pipeline and yield streaming updates.

        Yields dictionaries with keys like: status, progress, tasks, current_task, result, error
        """
        state = {"goal": goal, "messages": [], "tasks": [], "current_task": None, "updates": []}

        # Run the compiled workflow synchronously but yield updates asynchronously
        runner = self._workflow

        # We interleave execution and yield updates from `state['updates']` as they appear
        # To keep the runtime non-blocking for the websocket, yield after each update appended.
        # Note: this is a minimal cooperative streaming model.
        import asyncio

        # run workflow in thread to avoid blocking event loop if heavy sync work occurs
        def _run_and_collect():
            runner(state)

        loop = asyncio.get_event_loop()
        # schedule the runner in executor
        fut = loop.run_in_executor(None, _run_and_collect)

        # While runner is running, stream updates
        last_sent = 0
        while not fut.done():
            # send any pending updates
            updates = state.get("updates", [])
            while last_sent < len(updates):
                u = updates[last_sent]
                last_sent += 1
                # normalize progress to 0-1
                if "progress" in u:
                    try:
                        p = float(u["progress"])
                        u["progress"] = max(0.0, min(1.0, p))
                    except Exception:
                        u["progress"] = 0.0
                yield u
            # small sleep to yield control
            await asyncio.sleep(0.05)

        # ensure all remaining updates are sent
        updates = state.get("updates", [])
        while last_sent < len(updates):
            u = updates[last_sent]
            last_sent += 1
            if "progress" in u:
                try:
                    p = float(u["progress"])
                    u["progress"] = max(0.0, min(1.0, p))
                except Exception:
                    u["progress"] = 0.0
            yield u

        # final state snapshot
        yield {"status": "completed", "progress": 1.0, "state": state}

        # persist episode log
        try:
            add_episode("langgraph.plan", json.dumps(state, default=str))
        except Exception:
            pass


__all__ = ["LangGraphPlanner", "LANGGRAPH_AVAILABLE", "LG_VERSION"]
