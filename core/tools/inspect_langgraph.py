import importlib

mods = []
try:
    lg = importlib.import_module('langgraph')
    print('langgraph version:', getattr(lg, '__version__', '(no __version__)'))
    print('\nTop-level attrs:')
    for name in sorted(dir(lg)):
        if name.startswith('_'): continue
        print(name)
    # try some submodules
    subs = ['sdk', 'workflow', 'graph', 'runtime', 'nodes', 'core']
    for s in subs:
        try:
            m = importlib.import_module('langgraph.'+s)
            print(f'\nmodule langgraph.{s}:')
            for name in sorted(dir(m)):
                if name.startswith('_'): continue
                print('  ', name)
        except Exception as e:
            # print nothing if not present
            pass
except Exception as e:
    print('failed to import langgraph:', e)
