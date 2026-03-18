import importlib
try:
    m = importlib.import_module('core.agents')
    print('core.agents module:', m)
    print('is package (has __path__)?', hasattr(m, '__path__'))
    print('__file__:', getattr(m, '__file__', None))
except Exception as e:
    print('IMPORT ERROR:', e)
