"""Core package initializer.

Ensure `core.agents` resolves to the package when possible. Some test
runners or import ordering can leave a stale non-package module named
`core.agents` in sys.modules which later causes "not a package" errors
when importing submodules. Defensively fix that here.
"""
import sys
import importlib

if 'core.agents' in sys.modules:
	m = sys.modules['core.agents']
	if not hasattr(m, '__path__'):
		# remove stale module so package import can succeed
		del sys.modules['core.agents']

try:
	importlib.import_module('core.agents')
except Exception:
	# best-effort import; if it fails, tests will report the underlying issue
	pass
