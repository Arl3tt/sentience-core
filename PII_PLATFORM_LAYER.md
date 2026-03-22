"""
PII v1.0 L4 — Platform Layer Documentation
FastAPI REST API for cognitive AI execution system.
"""

# PII v1.0 L4 — Platform Layer: REST API & Web Integration

## 🌐 What is L4?

**L4 exposes the entire cognitive system to the world.**

It provides REST endpoints so external applications can:
- Submit tasks for cognitive processing
- Monitor real-time cognition metrics
- Retrieve learning summaries
- Query system health

## 🎯 Core Features

### Task Management
- **Submit tasks** with complexity and cycle limits
- **Monitor progress** with real-time status updates
- **Retrieve results** with full learning analytics
- **Cancel tasks** that are still queued/running

### Real-Time Metrics
- **Cognitive snapshots** (focus, fatigue, load, efficiency)
- **Cycle reports** with success/efficiency scores
- **Learning summaries** showing improvement trajectory
- **Status indicators** (🟢 OPTIMAL, 🟡 FATIGUED, 🔴 OVERLOADED)

### Background Processing
- **Asynchronous task execution** via FastAPI background tasks
- **Non-blocking API calls** return immediately
- **Polling-based results** for async completion

---

## 📋 API Endpoints

### System Information & Health

#### `GET /`
Root endpoint with API info and links

```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "name": "PII v1.0 — Cognitive AI Execution System",
  "version": "1.0.0",
  "docs_url": "/docs",
  "health_url": "/health",
  "submit_task_url": "/api/tasks"
}
```

#### `GET /health`
System health check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "active_tasks": 3,
  "total_processed": 127,
  "uptime_seconds": 3600.5
}
```

---

### Task Management

#### `POST /api/tasks`
Submit a new task for processing

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Analyze customer data",
    "complexity": 0.7,
    "max_cycles": 10
  }'
```

**Request:**
```json
{
  "description": "Task description",
  "complexity": 0.5,     // 0.0-1.0
  "max_cycles": 10       // Max cycles to run
}
```

**Response:**
```json
{
  "task_id": "a1b2c3d4e5",
  "status": "queued",
  "message": "Task a1b2c3d4e5 queued for processing"
}
```

---

#### `GET /api/tasks/{task_id}`
Get task status

```bash
curl http://localhost:8000/api/tasks/a1b2c3d4e5
```

**Response:**
```json
{
  "task_id": "a1b2c3d4e5",
  "status": "running",
  "cycles_completed": 3,
  "max_cycles": 10,
  "created_at": "2026-03-22T10:30:00",
  "completed_at": null
}
```

**Status values:**
- `queued` — Waiting to start
- `running` — Currently executing
- `completed` — Finished successfully
- `failed` — Error occurred
- `cancelled` — Stopped by user

---

#### `GET /api/tasks/{task_id}/results`
Get full results (only works after completion)

```bash
curl http://localhost:8000/api/tasks/a1b2c3d4e5/results
```

**Response:**
```json
{
  "task_id": "a1b2c3d4e5",
  "status": "completed",
  "total_cycles": 6,
  "avg_success": 0.78,
  "avg_efficiency": 0.72,
  "success_trend": 0.25,
  "peak_cycle": 4,
  "final_modifier": 1.32,
  "created_at": "2026-03-22T10:30:00",
  "completed_at": "2026-03-22T10:35:12",
  "cycles": [
    {
      "cycle": 1,
      "agent": "Planner",
      "success_score": 0.75,
      "efficiency_score": 0.70,
      "cognitive_load": 0.40,
      "strategy_modifier": 1.00,
      "status": "🔵 NORMAL"
    },
    ...
  ]
}
```

---

#### `GET /api/tasks/{task_id}/cognition`
Get current cognitive state snapshot

```bash
curl http://localhost:8000/api/tasks/a1b2c3d4e5/cognition
```

**Response:**
```json
{
  "focus": 0.82,
  "fatigue": 0.15,
  "cognitive_load": 0.38,
  "learning_efficiency": 0.71,
  "status": "🟢 OPTIMAL"
}
```

---

#### `DELETE /api/tasks/{task_id}`
Cancel a task (only works if queued/running)

```bash
curl -X DELETE http://localhost:8000/api/tasks/a1b2c3d4e5
```

**Response:**
```json
{
  "message": "Task a1b2c3d4e5 cancelled"
}
```

---

#### `GET /api/tasks`
List all tasks

```bash
curl http://localhost:8000/api/tasks
```

**Response:**
```json
{
  "total": 127,
  "tasks": [
    {
      "task_id": "a1b2c3d4e5",
      "status": "completed",
      "description": "Analyze customer data",
      "cycles": 6,
      "created_at": "2026-03-22T10:30:00"
    },
    ...
  ]
}
```

---

## 🚀 Usage Examples

### Python Client

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# 1. Submit a task
task_data = {
    "description": "Train recommendation model",
    "complexity": 0.8,
    "max_cycles": 20
}

response = requests.post(f"{BASE_URL}/api/tasks", json=task_data)
task = response.json()
task_id = task["task_id"]
print(f"Task submitted: {task_id}")

# 2. Poll for completion
while True:
    status = requests.get(f"{BASE_URL}/api/tasks/{task_id}").json()
    print(f"Status: {status['status']}, Cycles: {status['cycles_completed']}/{status['max_cycles']}")

    if status["status"] in ["completed", "failed", "cancelled"]:
        break

    time.sleep(1)

# 3. Get results
results = requests.get(f"{BASE_URL}/api/tasks/{task_id}/results").json()

print(f"\n=== RESULTS ===")
print(f"Avg Success: {results['avg_success']:.2f}")
print(f"Success Trend: {results['success_trend']:+.3f}")
print(f"Peak Performance: Cycle {results['peak_cycle']}")
print(f"Total Cycles: {results['total_cycles']}")

# 4. View cognitive evolution
for cycle in results["cycles"]:
    print(f"Cycle {cycle['cycle']}: "
          f"Success={cycle['success_score']:.2f}, "
          f"Status={cycle['status']}")
```

### JavaScript/Fetch

```javascript
const BASE_URL = "http://localhost:8000";

// Submit task
const submitTask = async () => {
  const response = await fetch(`${BASE_URL}/api/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      description: "Process user feedback",
      complexity: 0.6,
      max_cycles: 15
    })
  });

  const task = await response.json();
  return task.task_id;
};

// Poll until completion
const waitForCompletion = async (taskId) => {
  while (true) {
    const status = await (
      await fetch(`${BASE_URL}/api/tasks/${taskId}`)
    ).json();

    console.log(`Status: ${status.status}`);

    if (["completed", "failed"].includes(status.status)) {
      return status;
    }

    await new Promise(r => setTimeout(r, 1000));
  }
};

// Get results
const getResults = async (taskId) => {
  const response = await fetch(`${BASE_URL}/api/tasks/${taskId}/results`);
  return await response.json();
};

// Run
const taskId = await submitTask();
await waitForCompletion(taskId);
const results = await getResults(taskId);
console.log(results);
```

### cURL Workflow

```bash
# 1. Submit task
TASK_RESPONSE=$(curl -s -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Generate insights",
    "complexity": 0.7,
    "max_cycles": 10
  }')

TASK_ID=$(echo $TASK_RESPONSE | jq -r '.task_id')
echo "Task ID: $TASK_ID"

# 2. Wait for completion
while true; do
  STATUS=$(curl -s http://localhost:8000/api/tasks/$TASK_ID | jq -r '.status')
  echo "Status: $STATUS"

  if [[ "$STATUS" == "completed" ]] || [[ "$STATUS" == "failed" ]]; then
    break
  fi

  sleep 1
done

# 3. Get results
curl -s http://localhost:8000/api/tasks/$TASK_ID/results | jq '.'
```

---

## 🏃 Running the API

### Development

```bash
# Install dependencies
pip install fastapi uvicorn

# Run with reload
uvicorn ui.api_l4:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# With gunicorn (recommended)
pip install gunicorn

gunicorn ui.api_l4:app -w 4 -b 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker
```

### Docker

```dockerfile
FROM python:3.13

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "ui.api_l4:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📊 API Interactive Documentation

FastAPI automatically generates interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Use these to:
- Explore all endpoints
- Try requests directly in browser
- See response schemas
- View error examples

---

## 🔄 Task Lifecycle

```
┌─────────┐
│ queued  │  ← Task submitted, awaiting execution
└────┬────┘
     │
     ▼
┌─────────┐
│ running │  ← Cycles executing, cognition updating
└────┬────┘
     │
     └─────┬─────────┬──────────┐
           │         │          │
        Success   Failed    Cancelled
           │         │          │
           ▼         ▼          ▼
      ┌─────────┬─────────┬─────────┐
      │Completed│ Failed  │Cancelled│
      └─────────┴─────────┴─────────┘

Results available only after reaching terminal state
```

---

## 🧪 Testing

```bash
# Run all L4 tests
python -m pytest tests/test_l4_platform_api.py -v

# Run with full output
python -m pytest tests/test_l4_platform_api.py -v -s
```

**Test Coverage:**
- Endpoint availability
- Task submission and status tracking
- Cognitive snapshot retrieval
- Learning summary computation
- Error handling (404, 400)
- Full workflow (submit → poll → results)

---

## 🔌 Integration with Existing System

L4 automatically integrates with L1-L3:

```
User/Client
    │
    │ HTTP
    ▼
L4 API (FastAPI)
    │
    │ Python calls
    ├─→ L3 (AdaptiveLoop)
    │    │
    │    ├─→ L1 (BaseAgent + PlannerAgent)
    │    │
    │    └─→ L2 (Cognitive Engine)
    │
    │ Stores results
    ▼
Task State Dictionary
```

---

## 📈 Monitoring & Observability

### Health Metrics

```json
{
  "status": "healthy",
  "active_tasks": 5,
  "total_processed": 512,
  "uptime_seconds": 86400
}
```

### Per-Task Metrics

- Current cycle count
- Average success rate
- Learning efficiency trend
- Cognitive load evolution
- Strategy adaptation rate

### Logging

Add to your FastAPI app for production:

```python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
```

---

## ⚠️ Best Practices

### 1. **Use Polling with Backoff**

```python
import backoff

@backoff.on_predicate(backoff.expo, lambda x: x["status"] == "running")
def wait_for_task(task_id):
    return requests.get(f"http://localhost:8000/api/tasks/{task_id}").json()

result = wait_for_task(task_id)
```

### 2. **Validate Input**

```python
assert 0.0 <= task_data["complexity"] <= 1.0
assert task_data["max_cycles"] > 0
assert len(task_data["description"]) > 0
```

### 3. **Handle Errors**

```python
try:
    response = requests.post(f"{BASE_URL}/api/tasks", json=task_data)
    response.raise_for_status()
    task_id = response.json()["task_id"]
except requests.exceptions.RequestException as e:
    print(f"API error: {e}")
```

### 4. **Set Timeouts**

```python
response = requests.get(
    f"{BASE_URL}/api/tasks/{task_id}",
    timeout=5  # 5 second timeout
)
```

---

## 🚀 Next: Dashboard & Voice Interface

Future enhancements:

- **Web Dashboard** (React/Vue) for real-time visualization
- **WebSocket support** for live updates instead of polling
- **Voice interface** (FastAPI + text-to-speech) for voice commands
- **Metrics export** (Prometheus, CloudWatch)
- **Database persistence** (PostgreSQL for production)

---

**Status: L4 — Platform Layer ✅ COMPLETE**
**Test Results: 10/10 passing**
**API Ready for: Development, Testing, Production**
**Full Stack: L1 ↔ L2 ↔ L3 ↔ L4 Operational**
