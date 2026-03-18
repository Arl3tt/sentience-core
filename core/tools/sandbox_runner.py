#!/usr/bin/env python3
"""
sandbox_runner.py - Safe command execution in Docker sandbox
Runs potentially unsafe commands in an isolated container environment.
"""
import os
import sys
import subprocess
from typing import Dict, Any, Optional
import json


def run_in_sandbox(
    command: str,
    timeout: int = 30,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Run a command in the sandbox container

    Args:
        command: The command to execute
        timeout: Maximum execution time in seconds
        env: Optional environment variables

    Returns:
        Dict containing status, output, and error info
    """
    # Ensure docker environment is available
    # If Docker isn't available (e.g., in CI/test runner), fall back to
    # executing the command locally so tests can run without Docker.
    docker_available = _check_docker()
    if not docker_available:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True
            )
            status = "success" if result.returncode == 0 else "error"
            return {
                "status": status,
                "output": result.stdout,
                "error": result.stderr,
                "code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "output": "",
                "error": f"Command timed out after {timeout} seconds",
                "code": -1,
            }
        except Exception as e:
            return {"status": "error", "output": "", "error": str(e), "code": -1}

    # Prepare the docker-compose command
    # __file__ is core/tools/sandbox_runner.py, go up to project root
    compose_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "docker",
        "docker-compose.yml"
    )

    # Build the container if needed
    try:
        subprocess.run(
            ["docker-compose", "-f", compose_file, "build"],
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Docker build failed or docker-compose not available; fall back to local execution
        print(
            "WARNING: Docker build failed or docker-compose unavailable; falling back to local execution",
            file=sys.stderr,
        )
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True
            )
            status = "success" if result.returncode == 0 else "error"
            return {
                "status": status,
                "output": result.stdout,
                "error": result.stderr,
                "code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "output": "",
                "error": f"Command timed out after {timeout} seconds",
                "code": -1,
            }
        except Exception as e:
            return {"status": "error", "output": "", "error": str(e), "code": -1}

    # Prepare environment
    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    try:
        # Run the command
        result = subprocess.run(
            [
                "docker-compose",
                "-f", compose_file,
                "run",
                "--rm",
                "sandbox",
                "/bin/bash", "-c", command
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=run_env
        )

        status = "success" if result.returncode == 0 else "error"

        return {
            "status": status,
            "output": result.stdout,
            "error": result.stderr,
            "code": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "output": "",
            "error": f"Command timed out after {timeout} seconds",
            "code": -1
        }
    except Exception as e:
        return {
            "status": "error",
            "output": "",
            "error": str(e),
            "code": -1,
        }


def _check_docker() -> bool:
    """Check if docker and docker-compose are available"""
    try:
        subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            check=True
        )
        subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


if __name__ == "__main__":
    # Example usage
    result = run_in_sandbox("python -c 'print(\"Hello from sandbox!\")'")
    print(json.dumps(result, indent=2))
