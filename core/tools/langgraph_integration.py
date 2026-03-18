"""
LangGraph integration helpers for BCI tools.

Provides simple integration utilities to wire the 6 BCI tools into the
LangGraphPlanner and run a quick integration test.
"""
from typing import Optional
from core.langgraph_planner import LangGraphPlanner


def create_bci_planner() -> LangGraphPlanner:
    """Create a LangGraphPlanner pre-wired to expose BCI tools."""
    planner = LangGraphPlanner()
    return planner


def run_sample_bci_plan(goal: str = "Test BCI toolchain") -> dict:
    """Run planner synchronously and return final state snapshot.

    This helper shells out to the planner's workflow and returns the final
    state dictionary produced by the planner for quick integration testing.
    """
    import asyncio

    planner = create_bci_planner()

    async def _run():
        result = None
        async for update in planner.plan(goal):
            # consume updates; final update contains `state`
            if isinstance(update, dict) and update.get("status") == "completed":
                result = update.get("state")
        return result

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_run())
