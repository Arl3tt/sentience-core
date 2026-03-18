# Minimal FastAPI web UI for interacting with the Sentience Core
from datetime import datetime
import uvicorn
from fastapi import FastAPI, Form, UploadFile, File, WebSocket
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from config import HOST, PORT
from core.memory import ingest_document, semantic_search, add_episode
from core.brain import GOAL_QUEUE
from core.langgraph_planner import LangGraphPlanner

app = FastAPI()

INDEX = '''<!doctype html>
<html>
<head>
    <title>Sentience Core</title>
    <style>
        .progress-container {
            width: 100%;
            background-color: #f0f0f0;
            padding: 3px;
            border-radius: 3px;
            margin: 10px 0;
        }
        .progress-bar {
            width: 0%;
            height: 20px;
            background-color: #4CAF50;
            border-radius: 3px;
            transition: width 0.3s ease-in-out;
        }
        #status {
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ddd;
            background-color: #fff;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .error {
            background-color: #ffebee;
            color: #c62828;
            border-color: #ffcdd2;
        }
        .success {
            background-color: #e8f5e9;
            color: #2e7d32;
            border-color: #c8e6c9;
        }
        .task-list {
            margin: 10px 0;
            padding: 0;
            list-style: none;
        }
        .task-item {
            padding: 8px;
            margin: 4px 0;
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 4px solid #4CAF50;
        }
        .task-item.completed {
            border-left-color: #2196F3;
            background: #e3f2fd;
        }
        #connection-status {
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 8px;
            border-radius: 4px;
            font-size: 14px;
        }
        .connected {
            background-color: #c8e6c9;
            color: #2e7d32;
        }
        .disconnected {
            background-color: #ffcdd2;
            color: #c62828;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <h1>Sentience Core</h1>
    <div id="connection-status"></div>
    
    <div id="status" style="display: none;">
        <h3>Current Status</h3>
        <div id="status-text"></div>
        <div class="progress-container">
            <div class="progress-bar" id="progress"></div>
        </div>
    </div>

    <div id="task-container" style="display: none;">
        <h3>Task Progress</h3>
        <ul class="task-list" id="task-list"></ul>
    </div>
    
    <div class="card">
        <h3>Submit Goal</h3>
        <form id="goal-form" onsubmit="submitGoal(event)">
            <input type="text" name="user_input" id="user-input" style="width:400px" placeholder="Enter your goal..."/>
            <input type="submit" value="Send" id="submit-btn"/>
            <div class="loading" id="loading" style="display: none;"></div>
        </form>
    </div>

    <div class="card">
        <h3>Document Management</h3>
        <form action="/ingest" method="post" enctype="multipart/form-data">
            <input type="file" name="file"/>
            <input type="submit" value="Ingest"/>
        </form>
        
        <form action="/search" method="post">
            <input type="text" name="q" style="width:400px" placeholder="Search documents..."/>
            <input type="submit" value="Search"/>
        </form>
    </div>
    
    <p class="info-text">
        This UI provides real-time task execution monitoring with WebSocket-based progress updates.
        Use the console for advanced agent control.
    </p>

    <script>
        let socket = null;
        let taskMap = new Map();

        function updateConnectionStatus(connected) {
            const statusEl = document.getElementById('connection-status');
            statusEl.textContent = connected ? 'Connected' : 'Disconnected';
            statusEl.className = connected ? 'connected' : 'disconnected';
        }

        function updateTaskList(tasks) {
            const taskList = document.getElementById('task-list');
            const taskContainer = document.getElementById('task-container');
            
            if (tasks && tasks.length > 0) {
                taskContainer.style.display = 'block';
                taskList.innerHTML = tasks.map(task => {
                    const isCompleted = taskMap.get(task.id) === 'completed';
                    return `
                        <li class="task-item ${isCompleted ? 'completed' : ''}" id="task-${task.id}">
                            <strong>${task.description}</strong>
                            ${isCompleted ? ' ✓' : ''}
                        </li>
                    `;
                }).join('');
            }
        }

        function submitGoal(event) {
            event.preventDefault();
            const input = document.getElementById('user-input');
            const submitBtn = document.getElementById('submit-btn');
            const loading = document.getElementById('loading');
            const status = document.getElementById('status');
            const statusText = document.getElementById('status-text');
            const progress = document.getElementById('progress');
            
            // Reset UI state
            taskMap.clear();
            status.style.display = 'block';
            document.getElementById('task-container').style.display = 'none';
            submitBtn.disabled = true;
            loading.style.display = 'inline-block';
            
            if (socket) {
                socket.close();
            }
            
            socket = new WebSocket(`ws://${window.location.host}/ws`);
            
            socket.onopen = function() {
                updateConnectionStatus(true);
                socket.send(input.value);
            };
            
            socket.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    
                    // Update status and progress
                    statusText.textContent = data.status || 'Processing...';
                    if (data.progress !== undefined) {
                        progress.style.width = `${data.progress * 100}%`;
                    }
                    
                    // Handle task updates
                    if (data.current_task) {
                        taskMap.set(data.current_task.id, 'completed');
                    }
                    if (data.tasks) {
                        updateTaskList(data.tasks);
                    }
                    
                    // Handle errors
                    if (data.error) {
                        status.classList.add('error');
                        statusText.textContent = `Error: ${data.error}`;
                    }
                    
                } catch (e) {
                    console.error('Failed to parse message:', e);
                    status.classList.add('error');
                    statusText.textContent = 'Error: Failed to parse server message';
                }
            };
            
            socket.onclose = function() {
                updateConnectionStatus(false);
                submitBtn.disabled = false;
                loading.style.display = 'none';
                
                setTimeout(() => {
                    if (status.classList.contains('error')) {
                        return; // Keep error message visible
                    }
                    status.style.display = 'none';
                    status.classList.remove('error');
                }, 3000);
            };
            
            socket.onerror = function(error) {
                console.error('WebSocket error:', error);
                status.classList.add('error');
                statusText.textContent = 'Error: Connection failed';
                submitBtn.disabled = false;
                loading.style.display = 'none';
            };
        }

        // Initialize connection status
        updateConnectionStatus(false);
    </script>
</body>
</html>'''

planner = LangGraphPlanner()

@app.get('/', response_class=HTMLResponse)
def index():
    return INDEX

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        goal = await websocket.receive_text()
        add_episode('webui.input', goal)
        
        # Process goal through LangGraph with streaming
        async for update in planner.plan(goal):
            await websocket.send_json(update)
            
        # Add goal to queue for other processors
        GOAL_QUEUE.put(goal)
            
    except Exception as e:
        await websocket.send_json({
            "status": f"Error: {str(e)}",
            "progress": 1.0
        })
    finally:
        await websocket.close()

@app.post('/send')
async def send(user_input: str = Form(...)):
    add_episode('webui.input', user_input)
    GOAL_QUEUE.put(user_input)
    return RedirectResponse('/', status_code=303)


@app.post('/ingest')
async def ingest(file: UploadFile = File(...)):
    content = await file.read()
    try:
        text = content.decode('utf-8')
    except Exception:
        text = '[binary content]'
    ingest_document(file.filename, text, {'source': 'webui'})
    return RedirectResponse('/', status_code=303)


@app.post('/search')
async def search(q: str = Form(...)):
    hits = semantic_search(q, top_k=6)
    body = '<h2>Search results</h2>'
    for h in hits:
        body += f"<div><b>{h.get('id')}</b>: {h.get('doc')[:300]}...</div><hr/>"
    return HTMLResponse(body)


@app.get('/history', response_class=HTMLResponse)
async def training_history():
    """Display model training history"""
    import csv
    from core.tools.model_logger import HISTORY_FILE, FIELDNAMES

    try:
        with open(HISTORY_FILE, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        rows = []

    # Generate HTML table
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Training History</title>
        <style>
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            th { background-color: #4CAF50; color: white; }
        </style>
    </head>
    <body>
        <h1>Model Training History</h1>
        <table>
            <tr>
    '''

    # Add headers
    html += ''.join(f'<th>{field}</th>' for field in FIELDNAMES)
    html += '</tr>'

    # Add rows
    for row in reversed(rows):  # Most recent first
        html += '<tr>'
        for field in FIELDNAMES:
            value = row.get(field, '')
            if field == 'timestamp':
                # Format timestamp for readability
                try:
                    dt = datetime.fromisoformat(value)
                    value = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass
            html += f'<td>{value}</td>'
        html += '</tr>'

    html += '''
        </table>
    </body>
    </html>
    '''
    return html


def run_server():
    uvicorn.run(app, host=HOST, port=PORT, log_level='info')
