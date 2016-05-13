# -*- coding: utf-8 -*-

from  __builtin__ import __import__ as _import


def false_import(name, globals=None, locals=None, fromlist=[], level=-1):
    class ImpostorModule(object):
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return self
        def __enter__(self, *args, **kwargs):
            return ''
        def __exit__(self, *args, **kwargs):
            pass
        def __setitem__(self, *args, **kwargs):
            pass
        def __getitem__(self, *args, **kwargs):
            return self
        def __setattr__(self, *args, **kwargs):
            pass
        def __getattr__(self, *args, **kwargs):
            return self

    def return_empty_list(*args, **kwargs):
        return []

    def do_nothing(*args, **kwargs):
        pass

    def false_setup(*args, **kwargs):
        global setupargs
        setupargs = kwargs

    def get_module(*args):
        try:
            module = _import(*args)
        except ImportError as e:
            return ImpostorModule()
        else:
            return module

    if not fromlist:
        fromlist = []

    mod = get_module(name, globals, locals, fromlist, level)

    if (name == 'setuptools' or name == 'distutils.core' and 'setup' in fromlist):
        mod.setup = false_setup
    if name == 'pip.req' and 'parse_requirements' in fromlist:
        mod.parse_requirements = return_empty_list
    if name == 'distribute_setup':
        mod = false_module
    if name == 'sys':
        mod.exit = do_nothing
    if name == 'os':
        mod._exit = do_nothing
    return mod

def patchedglobals(setuppath):
    env = globals()
    env.update({
        '__file__': setuppath,
        '__name__': '__main__',
        '__package__': None,
    })
    env['__builtins__'].update({
        'exit': lambda *args: None,
        '__import__': false_import
    })

    return env
