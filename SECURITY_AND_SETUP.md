# Sentience Core Security and Setup Guide

## New Components

### LangGraph Planning System
- `core/config/planner_workflow.yaml` - Workflow definition
- `core/langgraph_planner.py` - LangGraph implementation
- Falls back to classic planner if LangGraph not installed

### Sandboxed Execution
- `docker/Dockerfile.sandbox` - Minimal Python container
- `docker/docker-compose.yml` - Sandbox service definition
- `core/tools/sandbox_runner.py` - Safe command execution

## Setup Instructions

1. Install additional dependencies:
```bash
pip install langgraph pyyaml docker-compose
```

2. Build the sandbox container:
```bash
cd docker
docker-compose build
```

3. Update your config to enable sandboxed execution:
```python
SANDBOX_ENABLED = True  # in config.py
```

## Security Best Practices

### Sandbox Container
- Runs as non-root user
- No network access
- Read-only filesystem
- Dropped capabilities
- No privilege escalation
- Ephemeral container (--rm)

### Code Execution
- Use sandbox for untrusted code
- Limit execution time
- Validate inputs
- Monitor resource usage
- Log all executions

### LangGraph Usage
- Validate workflow outputs
- Set memory limits
- Use semantic memory wisely
- Monitor LLM costs

## Architecture Notes

### Command Execution Flow
1. Executor receives command
2. If SANDBOX_ENABLED, routes to sandbox_runner
3. Command runs in isolated container
4. Results returned safely

### Error Handling
- Timeouts for hung processes
- Resource limits
- Graceful fallbacks
- Comprehensive logging

### Memory Management
- Semantic search with limits
- Episodic memory pruning
- Efficient embeddings

## Monitoring

Monitor these aspects:
- Container resource usage
- Execution times
- Error rates
- Memory usage
- LLM token usage

## Updates and Maintenance

1. Update sandbox dependencies:
```bash
pip freeze > docker/requirements.txt
docker-compose build --no-cache
```

2. Test sandbox security:
```bash
python -m pytest tests/security/
```

3. Regular security updates:
```bash
docker-compose pull
docker system prune
```

## Common Issues

1. Docker not available
- Fallback to local execution
- Warning in logs
- Reduced functionality

2. LangGraph import fails
- Automatic fallback to classic planner
- No service interruption
- Consider installing LangGraph

3. Resource constraints
- Adjustable timeouts
- Memory limits
- CPU restrictions

## Best Practices

1. Development
- Test in sandbox first
- Use version control
- Document changes
- Monitor errors

2. Deployment
- Regular updates
- Security scans
- Backup state
- Monitor logs

3. Operations
- Rate limiting
- Resource quotas
- Access controls
- Audit logging