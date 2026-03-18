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
