"""
PII v1.0 L4 — Platform Layer: FastAPI Application
Exposes the cognitive system via REST API.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from core.system_state import initialize_system_state
from core.agents.pii_planner_agent import PlannerAgent
from core.adaptive_loop import AdaptiveLoop
from core.cognition import get_cognitive_summary

# Initialize FastAPI app
app = FastAPI(
    title="PII v1.0 — Cognitive AI Execution System",
    description="Self-evolving, cognitively-aware multi-agent framework",
    version="1.0.0"
)

# Global state management (in production, use Redis or database)
active_tasks: Dict[str, Dict[str, Any]] = {}


# ═══════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════

class TaskRequest(BaseModel):
    """Request to execute a cognitive task."""
    description: str
    complexity: float = 0.5  # 0.0-1.0
    max_cycles: int = 10


class TaskResponse(BaseModel):
    """Response after task submission."""
    task_id: str
    status: str  # "queued", "running", "completed", "failed"
    message: str


class CycleReport(BaseModel):
    """Single cycle report."""
    cycle: int
    agent: str
    success_score: float
    efficiency_score: float
    cognitive_load: float
    strategy_modifier: float
    status: str


class CognitiveSnapshot(BaseModel):
    """Current cognitive state."""
    focus: float
    fatigue: float
    cognitive_load: float
    learning_efficiency: float
    status: str


class TaskResultResponse(BaseModel):
    """Result after task completes."""
    task_id: str
    status: str
    total_cycles: int
    avg_success: float
    avg_efficiency: float
    success_trend: float
    peak_cycle: int
    final_modifier: float
    cycles: List[CycleReport]
    created_at: str
    completed_at: Optional[str] = None


class HealthResponse(BaseModel):
    """System health status."""
    status: str  # "healthy", "busy", "error"
    active_tasks: int
    total_processed: int
    uptime_seconds: float


# ═══════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["health"])
async def root():
    """Root endpoint — API documentation."""
    return {
        "name": "PII v1.0 — Cognitive AI Execution System",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "submit_task_url": "/api/tasks",
        "status": "operational"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns current system status and task metrics.
    """
    return HealthResponse(
        status="healthy" if len(active_tasks) > 0 else "idle",
        active_tasks=sum(1 for t in active_tasks.values() if t["status"] == "running"),
        total_processed=len(active_tasks),
        uptime_seconds=0.0  # Implement proper uptime tracking in production
    )


@app.post("/api/tasks", response_model=TaskResponse, tags=["tasks"])
async def submit_task(task_req: TaskRequest, background_tasks: BackgroundTasks):
    """
    Submit a new task for adaptive cognitive processing.

    Args:
        description: Task description
        complexity: Task complexity (0.0-1.0)
        max_cycles: Maximum cycles to run

    Returns:
        task_id for polling results
    """
    # Generate unique task ID
    task_id = str(uuid.uuid4())[:12]

    # Initialize task state
    state = initialize_system_state()
    state["task"]["id"] = task_id
    state["task"]["description"] = task_req.description
    state["task"]["complexity"] = max(0.0, min(1.0, task_req.complexity))

    # Store in active tasks
    active_tasks[task_id] = {
        "status": "queued",
        "state": state,
        "reports": [],
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "complexity": task_req.complexity,
        "max_cycles": task_req.max_cycles
    }

    # Schedule background execution
    background_tasks.add_task(
        _execute_task_background,
        task_id=task_id,
        max_cycles=task_req.max_cycles
    )

    return TaskResponse(
        task_id=task_id,
        status="queued",
        message=f"Task {task_id} queued for processing"
    )


@app.get("/api/tasks/{task_id}", tags=["tasks"])
async def get_task_status(task_id: str):
    """
    Get current status of a task.

    Args:
        task_id: Task ID from submission

    Returns:
        Current task status and progress
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = active_tasks[task_id]

    return {
        "task_id": task_id,
        "status": task["status"],
        "cycles_completed": len(task["reports"]),
        "max_cycles": task["max_cycles"],
        "created_at": task["created_at"],
        "completed_at": task["completed_at"]
    }


@app.get("/api/tasks/{task_id}/results", response_model=TaskResultResponse, tags=["tasks"])
async def get_task_results(task_id: str):
    """
    Get full results of a completed task.

    Args:
        task_id: Task ID from submission

    Returns:
        Complete learning summary and cycle reports
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = active_tasks[task_id]

    if task["status"] == "running":
        raise HTTPException(status_code=202, detail="Task still running")

    if task["status"] == "queued":
        raise HTTPException(status_code=202, detail="Task queued")

    if task["status"] == "failed":
        raise HTTPException(status_code=500, detail="Task failed")

    # Compute summary
    loop = AdaptiveLoop(verbose=False)
    summary = loop.get_learning_summary(task["reports"])

    # Convert reports to response format
    cycle_responses = [
        CycleReport(
            cycle=r["cycle"],
            agent=r["agent"],
            success_score=r["feedback"]["success_score"],
            efficiency_score=r["feedback"]["efficiency_score"],
            cognitive_load=r["feedback"]["cognitive_load"],
            strategy_modifier=r["strategy_modifier"],
            status=get_cognitive_summary(r["cognitive_state"])["status"]
        )
        for r in task["reports"]
    ]

    return TaskResultResponse(
        task_id=task_id,
        status=task["status"],
        total_cycles=len(task["reports"]),
        avg_success=summary.get("avg_success", 0.0),
        avg_efficiency=summary.get("avg_efficiency", 0.0),
        success_trend=summary.get("success_trend", 0.0),
        peak_cycle=summary.get("peak_cycle", 0),
        final_modifier=task["reports"][-1]["strategy_modifier"] if task["reports"] else 1.0,
        cycles=cycle_responses,
        created_at=task["created_at"],
        completed_at=task["completed_at"]
    )


@app.get("/api/tasks/{task_id}/cognition", response_model=CognitiveSnapshot, tags=["tasks"])
async def get_task_cognition(task_id: str):
    """
    Get current cognitive state snapshot of a task.

    Args:
        task_id: Task ID from submission

    Returns:
        Current focus, fatigue, load, learning_efficiency
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = active_tasks[task_id]
    cog = task["state"]["cognitive_state"]
    summary = get_cognitive_summary(task["state"])

    return CognitiveSnapshot(
        focus=cog["focus"],
        fatigue=cog["fatigue"],
        cognitive_load=cog["cognitive_load"],
        learning_efficiency=cog["learning_efficiency"],
        status=summary["status"]
    )


@app.delete("/api/tasks/{task_id}", tags=["tasks"])
async def cancel_task(task_id: str):
    """Cancel a running or queued task."""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = active_tasks[task_id]
    if task["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed task")

    active_tasks[task_id]["status"] = "cancelled"

    return {"message": f"Task {task_id} cancelled"}


@app.get("/api/tasks", tags=["tasks"])
async def list_tasks():
    """List all tasks with their status."""
    return {
        "total": len(active_tasks),
        "tasks": [
            {
                "task_id": tid,
                "status": t["status"],
                "description": t["state"]["task"]["description"],
                "cycles": len(t["reports"]),
                "created_at": t["created_at"]
            }
            for tid, t in active_tasks.items()
        ]
    }


# ═══════════════════════════════════════════════════════════════════════════
# BACKGROUND TASK EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

async def _execute_task_background(task_id: str, max_cycles: int):
    """
    Background worker for executing adaptive cycles.

    This runs asynchronously and updates active_tasks.
    """
    try:
        task = active_tasks[task_id]
        task["status"] = "running"

        # Create loop and agent
        loop = AdaptiveLoop(max_cycles=max_cycles, verbose=False)
        planner = PlannerAgent()

        state = task["state"]

        # Execute cycles
        for cycle_num in range(max_cycles):
            # Check if cancelled
            if active_tasks[task_id]["status"] == "cancelled":
                break

            # Execute one cycle
            state, report = loop.execute_cycle(state, planner, update_cognition=True)
            task["reports"].append(report)
            task["state"] = state

            # Check continuation rules
            feedback = report["feedback"]
            if not loop.should_continue(state, feedback, cycle_num):
                break

        # Mark as completed
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
        task["completed_at"] = datetime.now().isoformat()


# ═══════════════════════════════════════════════════════════════════════════
# STARTUP/SHUTDOWN
# ═══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    print("PII v1.0 L4 Platform Layer starting...")
    print("Cognitive AI Execution System ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("PII v1.0 Platform Layer shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
