# Sentience Core — Cognitive Copilot v1

This project is an advanced scaffold for a multi-agent, memory-enabled, reflexive AI Copilot.
It is designed to run on Windows (VSCode) and includes:
- core/brain.py (agent orchestrator)
- core/memory (episodic sqlite + semantic store with Chroma fallback)
- core/reflexion.py (self-evaluation & improvement loop)
- core/tools (safe tool runner, ingestion)
- core/agents (Planner, Researcher, Executor, Critic)
- ui/webui.py (FastAPI web UI)
- ui/voice.py (TTS/STT wrappers)
- models/router.py (model selection / routing)
- main.py (entrypoint to start agents + web UI + repl)
- .env.example and requirements.txt

**Important safety**: This is a research prototype. Code/shell execution requires confirmation (SAFE_MODE).
Do not use with human subjects without proper approvals. Secure your API keys and infrastructure before production use.

Quick start (Windows, PowerShell):
1. unzip sentience-core.zip
2. open folder in VSCode
3. python -m venv venv
4. .\venv\Scripts\activate
5. pip install -r requirements.txt
6. copy .env.example to .env and set OPENAI_API_KEY
7. python main.py

## Testing

All code is tested with pytest and must pass flake8 linting. To run tests locally:

```bash
# Run all tests
python -m pytest tests/ -v

# Run tests with coverage report
python -m pytest tests/ --cov=core --cov=memory --cov-report=html

# Run linting check
python -m flake8 --max-line-length=120

# Run security check
bandit -r core memory models data
```

**Test Suite:**
- 57 unit and integration tests covering core modules
- Tests for BCI tools, neural processing, and memory subsystems
- Mock-based testing to avoid external dependencies

## Continuous Integration / Continuous Deployment (CI/CD)

This project uses GitHub Actions for automated testing, linting, and security checks:

**Workflows:**
- **CI Pipeline** (`ci.yml`): Runs on every push and pull request
  - Linting with flake8 (max-line-length=120)
  - Full test suite with coverage reporting
  - Security scanning with bandit
  - Performance profiling (main branch only)
  
- **CodeQL Security Analysis** (`codeql.yml`): Weekly scans + on PRs
  - Automated security vulnerability detection
  - Code quality analysis

**Status Badges & Reports:**
- Coverage reports are uploaded as build artifacts
- CodeQL results visible in repository security tab
- All builds must pass before merge to main

