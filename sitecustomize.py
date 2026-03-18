"""Startup hook to ensure `core.agents` is imported as a package during test collection.

Pytest can sometimes import modules in an order that leaves a stale non-package
module in `sys.modules` named `core.agents`, causing `ModuleNotFoundError: '...'
not a package` when importing submodules. This file attempts a best-effort
repair at interpreter startup so tests see the package form.
"""
import sys
import importlib
import types
from pathlib import Path
import builtins
import traceback
import time
import threading
import os
from collections.abc import MutableMapping


# Proxy wrapper around sys.modules to detect assignments to specific keys
class _SysModulesProxy(MutableMapping):
    def __init__(self, backing):
        self._backing = backing

    def __getitem__(self, key):
        return self._backing[key]

    def __setitem__(self, key, value):
        # detect non-package assignment to 'core.agents'
        try:
            if key == 'core.agents' and not getattr(value, '__path__', None):
                with _import_lock:
                    with open(_import_log, 'a', encoding='utf-8') as f:
                        f.write(f"SET sys.modules['{key}'] = non-package -> repr={repr(value)} file={getattr(value,'__file__',None)} ts={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write('Stack:\n')
                        f.write(''.join(traceback.format_stack()[:-2]))
                        f.write('\n')
        except Exception:
            pass
        self._backing[key] = value

    def __delitem__(self, key):
        del self._backing[key]

    def __iter__(self):
        return iter(self._backing)

    def __len__(self):
        return len(self._backing)

    def __contains__(self, key):
        return key in self._backing

    def get(self, key, default=None):
        return self._backing.get(key, default)


# Replace sys.modules with proxy to detect problematic assignments during import
try:
    if not isinstance(sys.modules, _SysModulesProxy):
        sys.modules = _SysModulesProxy(sys.modules)
except Exception:
    pass

# Instrument imports to detect when a non-package 'core.agents' gets created.
_import_log = os.path.join(os.path.dirname(__file__), 'import_debug.log')
_import_lock = threading.Lock()
_logged = False

_orig_import = builtins.__import__

def _maybe_log_nonpackage():
    global _logged
    try:
        mod = sys.modules.get('core.agents')
        if mod is not None and not getattr(mod, '__path__', None):
            # Log only once to avoid noisy output
            if _logged:
                return
            stack = ''.join(traceback.format_stack()[:-2])
            info = {
                'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
                'thread': threading.get_ident(),
                'repr': repr(mod),
                'file': getattr(mod, '__file__', None),
                'stack': stack,
            }
            with _import_lock:
                with open(_import_log, 'a', encoding='utf-8') as f:
                    f.write('--- NON-PACKAGE core.agents DETECTED ---\n')
                    for k, v in info.items():
                        f.write(f"{k}: {v}\n")
                    f.write('\n')
            _logged = True
    except Exception:
        pass

def _traced_import(name, globals=None, locals=None, fromlist=(), level=0):
    # Delegate to original importer
    module = _orig_import(name, globals, locals, fromlist, level)
    # After import, check for offending module
    try:
        _maybe_log_nonpackage()
    except Exception:
        pass
    return module

# Install our import tracer early
builtins.__import__ = _traced_import


# Start a short-lived monitor thread to capture assignment timing for sys.modules
def _monitor_sysmodules(duration=12.0, interval=0.02):
    start = time.time()
    seen = False
    while time.time() - start < duration:
        try:
            mod = sys.modules.get('core.agents')
            if mod is not None and not getattr(mod, '__path__', None):
                # capture stacks of all threads and module repr
                stacks = []
                for tid, frame in sys._current_frames().items():
                    stacks.append(f"--- Thread {tid} stack:\n" + ''.join(traceback.format_stack(frame)))
                info = {
                    'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'thread': threading.get_ident(),
                    'repr': repr(mod),
                    'file': getattr(mod, '__file__', None),
                    'stacks': '\n'.join(stacks),
                    'sys_modules_keys': ','.join(list(sys.modules.keys())[:200])
                }
                with _import_lock:
                    with open(_import_log, 'a', encoding='utf-8') as f:
                        f.write('=== DETECTED non-package core.agents ===\n')
                        for k, v in info.items():
                            f.write(f"{k}: {v}\n")
                        f.write('\n')
                seen = True
                break
        except Exception:
            pass
        time.sleep(interval)
    if not seen:
        with _import_lock:
            with open(_import_log, 'a', encoding='utf-8') as f:
                f.write(f"no_nonpackage_detected ts={time.strftime('%Y-%m-%d %H:%M:%S')}\n")


try:
    t = threading.Thread(target=_monitor_sysmodules, args=(12.0, 0.02), daemon=True)
    t.start()
except Exception:
    pass

try:
    # If core.agents already exists and lacks __path__, remove it so package import can proceed
    if 'core.agents' in sys.modules and not getattr(sys.modules['core.agents'], '__path__', None):
        del sys.modules['core.agents']

    # Try to import the package form
    try:
        importlib.import_module('core.agents')
    except Exception:
        # If import fails, attempt to inject a package module pointing to the folder
        agents_dir = Path(__file__).parent / 'core' / 'agents'
        if agents_dir.exists():
            pkg = types.ModuleType('core.agents')
            pkg.__path__ = [str(agents_dir)]
            sys.modules['core.agents'] = pkg
            # Also try to pre-load key submodules like neuro_behavior to avoid
            # "not a package" errors during pytest collection.
            nb_path = agents_dir / 'neuro_behavior.py'
            if nb_path.exists() and 'core.agents.neuro_behavior' not in sys.modules:
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location('core.agents.neuro_behavior', str(nb_path))
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules['core.agents.neuro_behavior'] = mod
                    spec.loader.exec_module(mod)
                except Exception:
                    pass
except Exception:
    # If this fails, don't block startup — tests will show underlying errors.
    pass
