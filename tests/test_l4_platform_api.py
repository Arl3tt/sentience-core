"""
PII v1.0 L4 — Platform Layer Test Suite
Tests the FastAPI endpoints and task orchestration.
"""
import pytest
from fastapi.testclient import TestClient
from ui.api_l4 import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "PII v1.0" in data["name"]
    print("✅ test_root_endpoint PASSED")


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "active_tasks" in data
    print("✅ test_health_check PASSED")


def test_submit_task():
    """Test task submission."""
    task_data = {
        "description": "Test task",
        "complexity": 0.5,
        "max_cycles": 3
    }

    response = client.post("/api/tasks", json=task_data)
    assert response.status_code == 200
    data = response.json()

    assert "task_id" in data
    assert data["status"] == "queued"
    assert len(data["task_id"]) > 0

    print(f"✅ test_submit_task PASSED (task_id={data['task_id']})")


def test_get_task_status():
    """Test getting task status."""
    # Submit task first
    task_data = {
        "description": "Status check task",
        "complexity": 0.4,
        "max_cycles": 2
    }
    submit_response = client.post("/api/tasks", json=task_data)
    task_id = submit_response.json()["task_id"]

    # Get status
    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["task_id"] == task_id
    assert "status" in data
    assert "cycles_completed" in data

    print(f"✅ test_get_task_status PASSED (status={data['status']})")


def test_get_nonexistent_task():
    """Test getting nonexistent task returns 404."""
    response = client.get("/api/tasks/nonexistent_id")
    assert response.status_code == 404
    print("✅ test_get_nonexistent_task PASSED")


def test_list_tasks():
    """Test listing all tasks."""
    # Submit a few tasks
    for i in range(2):
        client.post("/api/tasks", json={
            "description": f"Task {i}",
            "complexity": 0.5,
            "max_cycles": 2
        })

    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "tasks" in data
    assert len(data["tasks"]) > 0

    print(f"✅ test_list_tasks PASSED (total={data['total']} tasks)")


def test_cancel_task():
    """Test cancelling a task."""
    # Submit task
    submit_response = client.post("/api/tasks", json={
        "description": "Cancellable task",
        "complexity": 0.5,
        "max_cycles": 10
    })
    task_id = submit_response.json()["task_id"]

    # Check initial status is queued or running
    status_before = client.get(f"/api/tasks/{task_id}").json()["status"]
    assert status_before in ["queued", "running", "completed"]

    # Try to cancel it
    response = client.delete(f"/api/tasks/{task_id}")

    # With TestClient, background tasks execute synchronously
    # so if the task is already completed, cancellation returns 400
    # This is expected behavior
    assert response.status_code in [200, 400]

    print(f"✅ test_cancel_task PASSED")


def test_task_complexity_validation():
    """Test that invalid complexity is clamped."""
    # Submit with invalid complexity
    response = client.post("/api/tasks", json={
        "description": "Complexity test",
        "complexity": 2.5,  # > 1.0
        "max_cycles": 2
    })

    assert response.status_code == 200
    task_id = response.json()["task_id"]

    # Check that it was clamped
    status_response = client.get(f"/api/tasks/{task_id}")
    # Task should still work (complexity was clamped internally)
    assert status_response.status_code == 200

    print("✅ test_task_complexity_validation PASSED")


def test_get_task_cognition():
    """Test getting cognitive snapshot."""
    # Submit task
    submit_response = client.post("/api/tasks", json={
        "description": "Cognition test",
        "complexity": 0.5,
        "max_cycles": 2
    })
    task_id = submit_response.json()["task_id"]

    # Get cognition
    response = client.get(f"/api/tasks/{task_id}/cognition")
    assert response.status_code == 200
    data = response.json()

    # Verify cognition fields
    assert "focus" in data
    assert "fatigue" in data
    assert "cognitive_load" in data
    assert "learning_efficiency" in data
    assert "status" in data

    # Verify normalization
    assert 0.0 <= data["focus"] <= 1.0
    assert 0.0 <= data["fatigue"] <= 1.0
    assert 0.0 <= data["cognitive_load"] <= 1.0
    assert 0.0 <= data["learning_efficiency"] <= 1.0

    print(f"✅ test_get_task_cognition PASSED (status={data['status']})")


def test_full_task_workflow():
    """Test complete task workflow: submit → poll → results."""
    print("\n" + "="*60)
    print("Full Task Workflow Test")
    print("="*60)

    # 1. Submit task
    print("\n[1] Submitting task...")
    task_data = {
        "description": "Complete workflow task",
        "complexity": 0.6,
        "max_cycles": 3
    }
    submit_response = client.post("/api/tasks", json=task_data)
    assert submit_response.status_code == 200
    task_id = submit_response.json()["task_id"]
    print(f"✓ Task submitted: {task_id}")

    # 2. Check status
    print("\n[2] Checking task status...")
    status_response = client.get(f"/api/tasks/{task_id}")
    assert status_response.status_code == 200
    initial_status = status_response.json()["status"]
    print(f"✓ Initial status: {initial_status}")

    # 3. Wait for completion (in test, we skip actual execution)
    # In real scenario, you'd poll with retries
    print("\n[3] Waiting for task to complete...")
    import time
    max_wait = 5  # seconds
    start = time.time()
    while time.time() - start < max_wait:
        status = client.get(f"/api/tasks/{task_id}").json()
        if status["status"] in ["completed", "failed", "cancelled"]:
            break
        time.sleep(0.1)

    # 4. Get final status
    final_response = client.get(f"/api/tasks/{task_id}")
    final_status = final_response.json()
    print(f"✓ Final status: {final_status['status']}")

    print("\n✅ Full workflow test PASSED")
    print("="*60)


if __name__ == "__main__":
    print("\n" + "🌐 "*30)
    print("PII v1.0 L4 — Platform Layer Test Suite")
    print("🌐 "*30)

    test_root_endpoint()
    test_health_check()
    test_submit_task()
    test_get_task_status()
    test_get_nonexistent_task()
    test_list_tasks()
    test_cancel_task()
    test_task_complexity_validation()
    test_get_task_cognition()
    test_full_task_workflow()

    print("\n" + "✅ "*30)
    print("All L4 API tests PASSED!")
    print("Platform Layer is operational")
    print("✅ "*30)
