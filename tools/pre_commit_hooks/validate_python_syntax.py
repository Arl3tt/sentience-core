#!/usr/bin/env python
"""Pre-commit hook: validate Python syntax across repository.

This script compiles all `.py` files found under the repository root and exits
with non-zero status when compilation errors are found. It is intended to be
called by pre-commit or as a git hook.
"""
import sys
import os
import py_compile

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
errors = []

for dirpath, dirnames, filenames in os.walk(root):
    # skip virtual environments and __pycache__
    if any(part in (".venv", "venv", "env", "__pycache__", ".git") for part in dirpath.split(os.sep)):
        continue
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        path = os.path.join(dirpath, fn)
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            errors.append((path, str(e)))

if errors:
    print("Python syntax errors detected:")
    for p, msg in errors:
        print(f"- {p}: {msg}")
    sys.exit(1)

print("All python files compile successfully.")
sys.exit(0)
