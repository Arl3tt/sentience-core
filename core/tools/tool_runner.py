# Safe tool runner utilities
import subprocess, sys, tempfile, os
from config import SAFE_MODE


def run_python_snippet(code: str, timeout_s=20, require_confirm=True):
    """Run a short python snippet in a temporary file and return its output."""
    if SAFE_MODE and require_confirm:
        ok = input('Confirm running python snippet? (y/N): ')
        if ok.strip().lower() != 'y':
            return {'status': 'aborted'}

    fname = tempfile.NamedTemporaryFile(delete=False, suffix='.py').name
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(code)
    try:
        p = subprocess.run([sys.executable, fname], capture_output=True, text=True, timeout=timeout_s)
        return {'stdout': p.stdout, 'stderr': p.stderr, 'returncode': p.returncode}
    except subprocess.TimeoutExpired:
        return {'stdout': '', 'stderr': 'timeout', 'returncode': -1}
    finally:
        try:
            os.remove(fname)
        except Exception:
            pass


def run_shell(cmd: str, require_confirm=True):
    """Run a shell command and return captured output."""
    if SAFE_MODE and require_confirm:
        ok = input(f"Confirm run shell command: {cmd} (y/N): ")
        if ok.strip().lower() != 'y':
            return {'status': 'aborted'}
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=60)
        return {'stdout': p.stdout, 'stderr': p.stderr, 'returncode': p.returncode}
    except Exception as e:
        return {'error': str(e)}
